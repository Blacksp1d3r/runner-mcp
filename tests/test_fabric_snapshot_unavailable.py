from __future__ import annotations

import pytest

from runner_mcp.fabric_bridge import bounded_snapshot_unavailable


@pytest.mark.parametrize(
    "reason,category",
    [
        ("Runner Fabric operational snapshot failed", "fabric_snapshot_unavailable"),
        ("Runner Fabric returned invalid operational snapshot", "fabric_snapshot_invalid_payload"),
        ("Runner Fabric operational snapshot must be read-only", "fabric_snapshot_invalid_payload"),
        ("/sensitive/path bearer-secret", "fabric_snapshot_unavailable"),
        (None, "fabric_snapshot_unavailable"),
        ({"secret": "value"}, "fabric_snapshot_unavailable"),
    ],
)
def test_expected_failures_return_bounded_nonsecret_state(
    reason: object, category: str
):
    result = bounded_snapshot_unavailable(reason)
    assert result == {
        "schema_version": "runner-mcp/fabric-operational-snapshot-error/v1",
        "state": "unavailable",
        "reason_code": category,
        "degraded": True,
        "unknown_layers": ["fabric-bridge"],
        "mutation_enabled": False,
        "execution_enabled": False,
    }
    assert "sensitive" not in str(result)
    assert "secret" not in str(result)


def test_unknown_failure_never_authorizes_new_execution():
    result = bounded_snapshot_unavailable("some future arbitrary connector error")
    assert result["state"] == "unavailable"
    assert result["execution_enabled"] is False
    assert result["mutation_enabled"] is False
