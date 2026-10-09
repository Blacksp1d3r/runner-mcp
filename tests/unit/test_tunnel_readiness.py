import pytest

from runner_mcp.tunnel_readiness import (
    TunnelReadinessEvidence,
    TunnelReadinessReason,
    TunnelReadinessState,
    classify_tunnel_readiness,
)


def test_tunnel_readiness_progression_uses_stable_reason_codes():
    cases = [
        (
            TunnelReadinessEvidence(configured=False),
            TunnelReadinessState.UNCONFIGURED,
            TunnelReadinessReason.NOT_CONFIGURED,
        ),
        (
            TunnelReadinessEvidence(configured=True),
            TunnelReadinessState.CONFIGURED,
            TunnelReadinessReason.PROCESS_NOT_RUNNING,
        ),
        (
            TunnelReadinessEvidence(configured=True, process_running=True),
            TunnelReadinessState.PROCESS_RUNNING,
            TunnelReadinessReason.LOCAL_MCP_NOT_READY,
        ),
        (
            TunnelReadinessEvidence(
                configured=True,
                process_running=True,
                local_mcp_ready=True,
            ),
            TunnelReadinessState.LOCAL_READY,
            TunnelReadinessReason.CONTROL_PLANE_NOT_AUTHENTICATED,
        ),
        (
            TunnelReadinessEvidence(
                configured=True,
                process_running=True,
                local_mcp_ready=True,
                control_plane_authenticated=True,
            ),
            TunnelReadinessState.CONTROL_PLANE_AUTHENTICATED,
            TunnelReadinessReason.END_TO_END_NOT_ROUTABLE,
        ),
        (
            TunnelReadinessEvidence(
                configured=True,
                process_running=True,
                local_mcp_ready=True,
                control_plane_authenticated=True,
                end_to_end_routable=True,
            ),
            TunnelReadinessState.ROUTABLE,
            TunnelReadinessReason.READY,
        ),
    ]

    for evidence, state, reason in cases:
        result = classify_tunnel_readiness(evidence)
        assert result.state is state
        assert result.reason is reason


def test_public_payload_contains_only_bounded_state_and_reason():
    result = classify_tunnel_readiness(
        TunnelReadinessEvidence(
            configured=True,
            process_running=True,
            local_mcp_ready=True,
            control_plane_authenticated=False,
        )
    )

    assert result.public_dict() == {
        "state": "local_ready",
        "reason": "control_plane_not_authenticated",
    }
    assert set(result.public_dict()) == {"state", "reason"}



def test_inconsistent_readiness_evidence_fails_closed():
    cases = [
        TunnelReadinessEvidence(
            configured=False,
            process_running=True,
        ),
        TunnelReadinessEvidence(
            configured=True,
            process_running=False,
            local_mcp_ready=True,
        ),
        TunnelReadinessEvidence(
            configured=True,
            process_running=True,
            local_mcp_ready=False,
            control_plane_authenticated=True,
        ),
        TunnelReadinessEvidence(
            configured=True,
            process_running=True,
            local_mcp_ready=True,
            control_plane_authenticated=False,
            end_to_end_routable=True,
        ),
    ]

    for evidence in cases:
        result = classify_tunnel_readiness(evidence)
        assert result.state is TunnelReadinessState.BLOCKED
        assert result.reason is TunnelReadinessReason.INCONSISTENT_EVIDENCE
        assert result.public_dict() == {
            "state": "blocked",
            "reason": "inconsistent_evidence",
        }


@pytest.mark.parametrize("field", [
    "configured",
    "process_running",
    "local_mcp_ready",
    "control_plane_authenticated",
    "end_to_end_routable",
])
@pytest.mark.parametrize("invalid", ["false", "true", 0, 1, None])
def test_nonboolean_tunnel_evidence_cannot_be_truthy_or_falsy(
    field: str, invalid: object,
) -> None:
    evidence = {
        "configured": True,
        "process_running": True,
        "local_mcp_ready": True,
        "control_plane_authenticated": True,
        "end_to_end_routable": True,
    }
    evidence[field] = invalid
    with pytest.raises(ValueError, match="boolean"):
        TunnelReadinessEvidence(**evidence)  # type: ignore[arg-type]
