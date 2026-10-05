from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TunnelReadinessState(StrEnum):
    UNCONFIGURED = "unconfigured"
    CONFIGURED = "configured"
    PROCESS_RUNNING = "process_running"
    LOCAL_READY = "local_ready"
    CONTROL_PLANE_AUTHENTICATED = "control_plane_authenticated"
    ROUTABLE = "routable"
    BLOCKED = "blocked"


class TunnelReadinessReason(StrEnum):
    NOT_CONFIGURED = "not_configured"
    PROCESS_NOT_RUNNING = "process_not_running"
    LOCAL_MCP_NOT_READY = "local_mcp_not_ready"
    CONTROL_PLANE_NOT_AUTHENTICATED = "control_plane_not_authenticated"
    END_TO_END_NOT_ROUTABLE = "end_to_end_not_routable"
    INCONSISTENT_EVIDENCE = "inconsistent_evidence"
    READY = "ready"


@dataclass(frozen=True, slots=True)
class TunnelReadinessEvidence:
    configured: bool
    process_running: bool = False
    local_mcp_ready: bool = False
    control_plane_authenticated: bool = False
    end_to_end_routable: bool = False


@dataclass(frozen=True, slots=True)
class TunnelReadiness:
    state: TunnelReadinessState
    reason: TunnelReadinessReason

    def public_dict(self) -> dict[str, str]:
        return {
            "state": self.state.value,
            "reason": self.reason.value,
        }


def classify_tunnel_readiness(evidence: TunnelReadinessEvidence) -> TunnelReadiness:
    """Classify already-collected evidence without probing processes, network, or secrets."""

    progression = (
        evidence.configured,
        evidence.process_running,
        evidence.local_mcp_ready,
        evidence.control_plane_authenticated,
        evidence.end_to_end_routable,
    )
    seen_false = False
    for item in progression:
        if not item:
            seen_false = True
        elif seen_false:
            return TunnelReadiness(
                state=TunnelReadinessState.BLOCKED,
                reason=TunnelReadinessReason.INCONSISTENT_EVIDENCE,
            )

    if not evidence.configured:
        return TunnelReadiness(
            state=TunnelReadinessState.UNCONFIGURED,
            reason=TunnelReadinessReason.NOT_CONFIGURED,
        )

    if not evidence.process_running:
        return TunnelReadiness(
            state=TunnelReadinessState.CONFIGURED,
            reason=TunnelReadinessReason.PROCESS_NOT_RUNNING,
        )

    if not evidence.local_mcp_ready:
        return TunnelReadiness(
            state=TunnelReadinessState.PROCESS_RUNNING,
            reason=TunnelReadinessReason.LOCAL_MCP_NOT_READY,
        )

    if not evidence.control_plane_authenticated:
        return TunnelReadiness(
            state=TunnelReadinessState.LOCAL_READY,
            reason=TunnelReadinessReason.CONTROL_PLANE_NOT_AUTHENTICATED,
        )

    if not evidence.end_to_end_routable:
        return TunnelReadiness(
            state=TunnelReadinessState.CONTROL_PLANE_AUTHENTICATED,
            reason=TunnelReadinessReason.END_TO_END_NOT_ROUTABLE,
        )

    return TunnelReadiness(
        state=TunnelReadinessState.ROUTABLE,
        reason=TunnelReadinessReason.READY,
    )
