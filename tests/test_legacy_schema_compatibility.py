"""Synthetic, hostless v1 schema compatibility checks; never execute tools."""
from __future__ import annotations

import copy

import pytest

from runner_mcp.legacy_schema_compatibility import (
    LegacySchemaReason,
    classify_legacy_tool_schemas,
)

TRUST = {"baseline_independently_pinned": True, "observed_authenticated": True}


def _tool(name: str = "list_backups") -> dict:
    return {
        "name": name,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "limit": {"type": "integer", "default": 100},
            },
            "required": ["project"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"result": {"type": "array"}},
            "required": ["result"],
        },
    }


def _compare(older, newer, **flags):
    return classify_legacy_tool_schemas(older, newer, **(TRUST | flags))


def test_original_contract_still_available_with_new_tool_addition():
    old = [_tool()]
    new = [copy.deepcopy(old[0]), _tool("new_readonly_status")]
    assert _compare(old, new) is LegacySchemaReason.MATCHED_SOURCE_ONLY
    assert old[0]["name"] == "list_backups"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda t: t["inputSchema"]["properties"]["limit"].update(default=200),
        lambda t: t["inputSchema"]["properties"]["limit"].update(type="string"),
        lambda t: t["inputSchema"]["required"].append("limit"),
        lambda t: t["inputSchema"].update(additionalProperties=True),
        lambda t: t["inputSchema"]["properties"].update(foreign={"type": "string"}),
        lambda t: t["outputSchema"]["properties"]["result"].update(type="string"),
    ],
)
def test_old_tool_schema_or_default_change_requires_v2(mutate):
    old = [_tool()]
    new = copy.deepcopy(old)
    mutate(new[0])
    assert _compare(old, new) is LegacySchemaReason.LEGACY_SCHEMA_CHANGED


def test_missing_old_name_never_succeeds():
    assert _compare([_tool()], [_tool("renamed_backups")]) is LegacySchemaReason.LEGACY_TOOL_MISSING


@pytest.mark.parametrize("candidate", [
    [], [_tool(), _tool()], [None], [{"name": "a", "inputSchema": {}}],
    [_tool("bad/name")], [_tool("tool"), {"name": "tool", "inputSchema": _tool()["inputSchema"]}],
])
def test_missing_invalid_duplicate_or_empty_inventory_fails_closed(candidate):
    assert _compare([_tool()], candidate) is LegacySchemaReason.INVALID_INVENTORY


@pytest.mark.parametrize("field", list(TRUST))
@pytest.mark.parametrize("bad", [False, None, "true", 1])
def test_untrusted_or_nonboolean_pins_are_not_authority(field, bad):
    assert _compare([_tool()], [_tool()], **{field: bad}) is LegacySchemaReason.UNTRUSTED_INVENTORY


def test_oversized_inventory_and_deep_schema_do_not_dispatch():
    many = [_tool(f"tool_{i}") for i in range(257)]
    assert _compare([_tool()], many) is LegacySchemaReason.INVENTORY_TOO_LARGE
    deep = [_tool()]
    nested: dict = deep[0]["inputSchema"]["properties"]["limit"]
    for _ in range(1100):
        child = {"nested": {}}
        nested["nested"] = child
        nested = child["nested"]
    assert _compare([_tool()], deep) is LegacySchemaReason.INVALID_INVENTORY


def test_output_contract_presence_must_not_be_implicitly_added_or_removed():
    old = [_tool()]
    new = copy.deepcopy(old)
    del new[0]["outputSchema"]
    assert _compare(old, new) is LegacySchemaReason.LEGACY_SCHEMA_CHANGED


def test_schema_equality_is_read_only_without_dispatch_or_private_leaks():
    original = [_tool()]
    tampered = copy.deepcopy(original)
    tampered[0]["description"] = "/private/DO_NOT_EMIT key=DO_NOT_EMIT"
    assert _compare(original, tampered) is LegacySchemaReason.MATCHED_SOURCE_ONLY
    result = _compare(original, tampered)
    assert "DO_NOT_EMIT" not in str(result)
    assert str(result) == "MATCHED_SOURCE_ONLY"
