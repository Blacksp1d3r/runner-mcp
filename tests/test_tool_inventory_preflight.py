from __future__ import annotations

import pytest

from runner_mcp.tool_identity_classifier import ToolContract
from runner_mcp.tool_inventory_preflight import (
    ToolInventoryReason,
    classify_tool_inventory,
)


def _tool(name: str, stable_id: str, **kwargs) -> ToolContract:
    values = {
        "tool_name": name,
        "stable_id": stable_id,
        "schema_digest": "a" * 64,
        "revision": 1,
        "enabled": True,
    }
    values.update(kwargs)
    return ToolContract(**values)


KEY = {
    "registry_trusted": True,
    "observed_authenticated": True,
    "inventory_fresh": True,
}


def test_two_distinct_bounded_tool_entries_compare_equal():
    entries = [_tool("runtime_status", "runtime-status"), _tool("runtime_doctor", "runtime-doctor")]
    assert classify_tool_inventory(entries, list(reversed(entries)), **KEY) is ToolInventoryReason.READY


def test_duplicate_stable_id_is_rejected_even_if_names_differ():
    observed = [_tool("runtime_status", "same-id"), _tool("runtime_doctor", "same-id")]
    assert classify_tool_inventory(observed, observed, **KEY) is ToolInventoryReason.DUPLICATE_TOOL_ID


def test_duplicate_name_is_rejected_even_if_ids_differ():
    observed = [_tool("runtime_status", "first-id"), _tool("runtime_status", "second-id")]
    assert classify_tool_inventory(observed, observed, **KEY) is ToolInventoryReason.DUPLICATE_TOOL_NAME


@pytest.mark.parametrize(
    "tampered",
    [
        [_tool("wrong_tool", "runtime-status")],
        [_tool("runtime_status", "wrong-id")],
        [_tool("runtime_status", "runtime-status", schema_digest="b" * 64)],
        [_tool("runtime_status", "runtime-status", revision=2)],
        [_tool("runtime_status", "runtime-status", enabled=False)],
    ],
)
def test_mismatched_inventory_never_returns_ready(tampered):
    expected = [_tool("runtime_status", "runtime-status")]
    assert classify_tool_inventory(expected, tampered, **KEY) is ToolInventoryReason.INVENTORY_MISMATCH


@pytest.mark.parametrize("field", list(KEY))
@pytest.mark.parametrize("value", [False, "false", 1, None])
def test_forged_or_unready_authority_flags_are_denied(field: str, value: object):
    entry = [_tool("runtime_status", "runtime-status")]
    result = classify_tool_inventory(entry, entry, **(KEY | {field: value}))
    assert result is not ToolInventoryReason.READY


@pytest.mark.parametrize(
    "inputs",
    [
        ("not-a-list", []),
        ([_tool("runtime_status", "runtime-status")], {"fake": "tool"}),
        ([None], [None]),
        ([_tool("runtime_status", "runtime-status", revision=True)], []),
    ],
)
def test_untrusted_or_malformed_inventory_entries_denied(inputs):
    result = classify_tool_inventory(inputs[0], inputs[1], **KEY)
    assert result is ToolInventoryReason.INVALID_TOOL_CONTRACT


def test_inventory_size_is_bounded():
    many = [_tool(f"tool_{i}", f"tool-{i}") for i in range(257)]
    assert classify_tool_inventory(many, many, **KEY) is ToolInventoryReason.INVENTORY_TOO_LARGE


def test_empty_inventories_compare_without_granting_execution():
    result = classify_tool_inventory([], [], **KEY)
    assert result is ToolInventoryReason.READY
    assert isinstance(result, ToolInventoryReason)
