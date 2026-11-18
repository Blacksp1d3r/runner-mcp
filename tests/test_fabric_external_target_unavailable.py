from __future__ import annotations

import pytest

from runner_mcp.fabric_bridge import bounded_external_target_read_unavailable


@pytest.mark.parametrize("phase", ["preflight", "inspect"])
@pytest.mark.parametrize(
    ("reason", "code"),
    [
        ("Runner Fabric external target preflight failed", "target_read_unavailable"),
        ("Runner Fabric external target inspection failed", "target_read_unavailable"),
        ("Runner Fabric returned invalid external target preflight", "invalid_peer_evidence"),
        ("Runner Fabric returned invalid external target inspection", "invalid_peer_evidence"),
        ("/private/endpoint bearer_token=secret", "target_read_unavailable"),
        ({"credential": "secret"}, "target_read_unavailable"),
        (None, "target_read_unavailable"),
    ],
)
def test_external_target_read_failures_are_bounded_and_non_authorizing(
    phase: str, reason: object, code: str
) -> None:
    result = bounded_external_target_read_unavailable(reason, phase=phase)
    assert result == {
        "schema_version": "runner-mcp/fabric-external-target-read-unavailable/v1",
        "state": "unavailable",
        "phase": phase,
        "reason_code": code,
        "ready": False,
        "mutation_enabled": False,
        "execution_enabled": False,
    }
    assert "secret" not in str(result)
    assert "/private/" not in str(result)


def test_external_target_error_projection_refuses_other_phases() -> None:
    with pytest.raises(ValueError, match="fixed"):
        bounded_external_target_read_unavailable("opaque", phase="update")
