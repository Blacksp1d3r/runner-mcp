"""Pure fail-closed validation for proposed stable Runner-MCP tool identities.

This module does not dispatch, authenticate, discover, or allocate tool IDs.
"""
from __future__ import annotations

import json
import re
from hashlib import sha256

NAMESPACE = "com.aifordable.runner-mcp"
ID_RE = re.compile(r"RMCP-[0-9]{6}\Z")
HEX_RE = re.compile(r"[0-9a-f]{64}\Z")
STATUSES = frozenset({"active", "deprecated", "retired"})
PERMISSIONS = frozenset({"read", "write", "admin"})


class RegistryContractError(ValueError):
    """Invalid or ambiguous static registry: no tool may be dispatched."""


def canonical_digest(schema: object) -> str:
    """Hash canonical JSON only, rejecting NaN and non-JSON objects."""
    try:
        data = json.dumps(
            schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise RegistryContractError("invalid JSON schema") from exc
    return sha256(data).hexdigest()


def validate_registry(document: object, *, previous: object | None = None) -> tuple[tuple[str, str, int], ...]:
    """Validate a versioned registry and optionally its immutable predecessor."""
    if not isinstance(document, dict) or set(document) != {"schemaVersion", "namespace", "tools"}:
        raise RegistryContractError("invalid registry envelope")
    if document["schemaVersion"] != "runner-mcp/tool-id-registry/v1" or document["namespace"] != NAMESPACE:
        raise RegistryContractError("unknown registry namespace or schema")
    entries = document["tools"]
    if not isinstance(entries, list):
        raise RegistryContractError("tools must be a list")
    seen_keys: set[tuple[str, int]] = set()
    seen_names: dict[str, str] = {}
    seen_ids: dict[str, str] = {}
    known: dict[tuple[str, int], dict] = {}
    for entry in entries:
        fields = {"tool_id", "tool_name", "contract_revision", "input_schema_sha256",
                  "output_schema_sha256", "permission_class", "status"}
        if not isinstance(entry, dict) or set(entry) != fields:
            raise RegistryContractError("invalid tool entry")
        tid, name, revision = entry["tool_id"], entry["tool_name"], entry["contract_revision"]
        if not isinstance(tid, str) or not ID_RE.fullmatch(tid):
            raise RegistryContractError("invalid tool ID")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise RegistryContractError("invalid tool name")
        if type(revision) is not int or revision < 1:
            raise RegistryContractError("invalid contract revision")
        for field in ("input_schema_sha256", "output_schema_sha256"):
            val = entry[field]
            if not isinstance(val, str) or not HEX_RE.fullmatch(val):
                raise RegistryContractError("invalid schema digest")
        if (not isinstance(entry["permission_class"], str) or
                not isinstance(entry["status"], str) or
                entry["permission_class"] not in PERMISSIONS or entry["status"] not in STATUSES):
            raise RegistryContractError("invalid policy descriptor")
        key = (tid, revision)
        if key in seen_keys:
            raise RegistryContractError("duplicate ID and revision")
        seen_keys.add(key)
        if tid in seen_ids and seen_ids[tid] != name:
            raise RegistryContractError("ID assigned to multiple tool names")
        seen_ids[tid] = name
        if name in seen_names and seen_names[name] != tid:
            raise RegistryContractError("name assigned to multiple IDs")
        seen_names[name] = tid
        known[key] = entry
    if previous is not None:
        validate_registry(previous)
        old_entries = {(e["tool_id"], e["contract_revision"]): e for e in previous["tools"]}
        old_ids = {e["tool_id"]: e["tool_name"] for e in previous["tools"]}
        for key, old in old_entries.items():
            if key not in known or known[key] != old:
                raise RegistryContractError("historical contract changed or disappeared")
        for entry in entries:
            if entry["tool_id"] in old_ids and old_ids[entry["tool_id"]] != entry["tool_name"]:
                raise RegistryContractError("retired ID was reused")
    return tuple(sorted((NAMESPACE, tid, rev) for tid, rev in seen_keys))
