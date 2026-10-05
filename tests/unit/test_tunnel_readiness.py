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
