"""Pure legacy MCP tools/list schema equality guard (#664).

Compares bounded, already-captured tool metadata only. The caller MUST separately
authenticate the old contract baseline and live observed serving-generation
inventory. MATCHED is NOT dispatch, host, protocol or update authorization.
This deliberately rejects schema evolution on legacy names until a separate
versioned tool and explicit compatibility review are available.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from enum import StrEnum

_NAME = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_MAX_TOOLS = 256
_MAX_BYTES = 262_144


class LegacySchemaReason(StrEnum):
    MATCHED_SOURCE_ONLY = "MATCHED_SOURCE_ONLY"
    UNTRUSTED_INVENTORY = "UNTRUSTED_INVENTORY"
    INVALID_INVENTORY = "INVALID_INVENTORY"
    INVENTORY_TOO_LARGE = "INVENTORY_TOO_LARGE"
    LEGACY_TOOL_MISSING = "LEGACY_TOOL_MISSING"
    LEGACY_SCHEMA_CHANGED = "LEGACY_SCHEMA_CHANGED"


def _canonical_schema(value: object) -> bytes | None:
    if not isinstance(value, dict) or value.get("type") != "object":
        return None
    if not isinstance(value.get("properties"), dict):
        return None
    required = value.get("required", [])
    if (
        not isinstance(required, list)
        or not all(isinstance(name, str) for name in required)
        or len(set(required)) != len(required)
        or not set(required).issubset(value["properties"])
    ):
        return None
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (RecursionError, TypeError, ValueError, UnicodeError):
        return None
    if len(encoded) > _MAX_BYTES:
        return None
    return encoded


def _index_inventory(
    catalogue: Sequence[Mapping[str, object]],
) -> dict[str, tuple[bytes, bytes | None]] | None:
    if not isinstance(catalogue, (list, tuple)) or not 1 <= len(catalogue) <= _MAX_TOOLS:
        return None
    result: dict[str, tuple[bytes, bytes | None]] = {}
    for item in catalogue:
        if not isinstance(item, dict):
            return None
        name = item.get("name")
        if not isinstance(name, str) or _NAME.fullmatch(name) is None or name in result:
            return None
        raw_input = item.get("inputSchema")
        input_schema = _canonical_schema(raw_input)
        if input_schema is None:
            return None
        if "outputSchema" in item and item["outputSchema"] is not None:
            output_schema = _canonical_schema(item["outputSchema"])
            if output_schema is None:
                return None
        else:
            output_schema = None
        result[name] = (input_schema, output_schema)
    return result


def classify_legacy_tool_schemas(
    baseline: Sequence[Mapping[str, object]],
    observed: Sequence[Mapping[str, object]],
    *,
    baseline_independently_pinned: bool,
    observed_authenticated: bool,
) -> LegacySchemaReason:
    """Keep old MCP tool contracts identical while permitting additional names.

    This only compares supplied tools/list metadata and never calls a tool.
    A future authenticated serving-process adapter must supply observations,
    pins and host policy; do not infer either from caller booleans.
    """
    if (
        type(baseline_independently_pinned) is not bool
        or type(observed_authenticated) is not bool
        or not baseline_independently_pinned
        or not observed_authenticated
    ):
        return LegacySchemaReason.UNTRUSTED_INVENTORY
    if not isinstance(baseline, (list, tuple)) or not isinstance(observed, (list, tuple)):
        return LegacySchemaReason.INVALID_INVENTORY
    if len(baseline) > _MAX_TOOLS or len(observed) > _MAX_TOOLS:
        return LegacySchemaReason.INVENTORY_TOO_LARGE
    older = _index_inventory(baseline)
    newer = _index_inventory(observed)
    if older is None or newer is None:
        return LegacySchemaReason.INVALID_INVENTORY
    if older.keys() - newer.keys():
        return LegacySchemaReason.LEGACY_TOOL_MISSING
    if any(newer[name] != contract for name, contract in older.items()):
        return LegacySchemaReason.LEGACY_SCHEMA_CHANGED
    return LegacySchemaReason.MATCHED_SOURCE_ONLY
