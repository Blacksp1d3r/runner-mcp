from __future__ import annotations

import pytest

from runner_mcp.fabric_update import (
    FabricUpdateError,
    bounded_fabric_readiness_failure,
)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("fabric_launcher_unmanaged", "fabric_launcher_unmanaged"),
        ("runner_mcp_state_unavailable", "runner_mcp_state_unavailable"),
        ("runner_mcp_self_update_active", "runner_mcp_self_update_active"),
        ("runner_mcp_restart_pending", "runner_mcp_restart_pending"),
        ("artifact_metadata_unavailable", "artifact_metadata_unavailable"),
        ("actions_run_unavailable", "actions_run_unavailable"),
        ("fabric_recovery_required", "fabric_recovery_required"),
        ("fabric_update_commit_invalid", "fabric_update_commit_invalid"),
        ("fabric_bundle_integrity_failed", "fabric_bundle_integrity_failed"),
        ("/private/path?access_token=secret", "fabric_update_readiness_unavailable"),
        ("unexpected future private failure", "fabric_update_readiness_unavailable"),
    ],
)
@pytest.mark.parametrize("source", ["github-actions", "local-custody", "github-release"])
def test_readiness_failure_is_bounded_and_never_authorizes_update(
    message: str, expected: str, source: str,
) -> None:
    result = bounded_fabric_readiness_failure(
        FabricUpdateError(message), source=source,
    )
    assert result == {
        "state": "blocked",
        "reasonCode": expected,
        "artifact_ready": False,
        "source": source,
    }
    assert "secret" not in repr(result)
    assert "/private" not in repr(result)


def test_readiness_refuses_unknown_source_and_untrusted_exception_type() -> None:
    with pytest.raises(ValueError, match="unsupported Fabric update source"):
        bounded_fabric_readiness_failure(
            FabricUpdateError("actions_run_unavailable"), source="untrusted",
        )
    assert bounded_fabric_readiness_failure(
        ValueError("actions_run_unavailable"), source="github-actions",
    )["reasonCode"] == "fabric_update_readiness_unavailable"


def test_failed_preflight_never_claims_artifact_or_installed_release() -> None:
    result = bounded_fabric_readiness_failure(
        FabricUpdateError("artifact_metadata_unavailable"), source="github-actions",
    )
    assert "commit" not in result
    assert "installed" not in result
    assert result["artifact_ready"] is False
