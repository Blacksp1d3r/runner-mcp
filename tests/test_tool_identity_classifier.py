from __future__ import annotations

import pytest

from runner_mcp.tool_identity_classifier import (
    ToolContract,
    ToolIdentityReason,
    classify_tool_contract,
)

KEY = {
    "namespace": "com.aifordable.runner-mcp",
    "registry_trusted": True,
    "observed_authenticated": True,
    "runtime_reachable": True,
    "inventory_fresh": True,
}


def _contract(**changes: object) -> ToolContract:
    data = {
        "tool_name": "runtime_status",
        "stable_id": "runtime-status",
        "schema_digest": "a" * 64,
        "revision": 1,
        "enabled": True,
    }
    data.update(changes)
    return ToolContract(**data)


def test_equal_contract_metadata_is_only_pre_dispatch_ready():
    assert classify_tool_contract(_contract(), _contract(), **KEY) is ToolIdentityReason.READY


@pytest.mark.parametrize(
    "expected,observed,changes,reason",
    [
        (None, _contract(), {}, ToolIdentityReason.UNKNOWN_TOOL),
        (_contract(), None, {}, ToolIdentityReason.VERSION_MISMATCH),
        (_contract(), _contract(revision=2), {}, ToolIdentityReason.VERSION_MISMATCH),
        (_contract(), _contract(schema_digest="b" * 64), {}, ToolIdentityReason.SCHEMA_MISMATCH),
        (_contract(enabled=False), _contract(), {}, ToolIdentityReason.TOOL_DISABLED),
        (_contract(), _contract(enabled=False), {}, ToolIdentityReason.TOOL_DISABLED),
        (_contract(), _contract(stable_id="different-id"), {}, ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY),
        (_contract(), _contract(tool_name="other_tool"), {}, ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY),
        (_contract(), _contract(), {"namespace": "org.forged.runner-mcp"}, ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY),
        (_contract(), _contract(), {"registry_trusted": False}, ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY),
        (_contract(), _contract(), {"observed_authenticated": False}, ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY),
        (_contract(), _contract(), {"runtime_reachable": False}, ToolIdentityReason.RUNTIME_UNREACHABLE),
        (_contract(), _contract(), {"inventory_fresh": False}, ToolIdentityReason.STALE_INVENTORY),
    ],
)
def test_mismatch_reasons_are_distinct(expected, observed, changes, reason):
    result = classify_tool_contract(expected, observed, **(KEY | changes))
    assert result is reason


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_digest": "z" * 64},
        {"revision": True},
        {"revision": 0},
        {"stable_id": "../escape"},
        {"tool_name": "invalid/name"},
        {"enabled": "yes"},
    ],
)
def test_malformed_registry_or_witness_denied(changes):
    assert (
        classify_tool_contract(_contract(), _contract(**changes), **KEY)
        is ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    )


def test_no_dispatch_callback_or_remote_request_exists_in_classifier():
    # Contract checker cannot call a tool and never returns an authorization token.
    result = classify_tool_contract(_contract(), _contract(), **KEY)
    assert isinstance(result, ToolIdentityReason)
    assert result.value == "READY"


@pytest.mark.parametrize(
    "flag",
    ["registry_trusted", "observed_authenticated", "runtime_reachable", "inventory_fresh"],
)
@pytest.mark.parametrize("value", ["false", 1, None, [], {"faked": True}])
def test_trust_and_runtime_flags_must_be_real_booleans(flag: str, value: object):
    result = classify_tool_contract(
        _contract(), _contract(), **(KEY | {flag: value})
    )
    assert result is ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
