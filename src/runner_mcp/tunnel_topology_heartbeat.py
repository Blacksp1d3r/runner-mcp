from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .tunnel_topology_refresh import (
    TunnelTopologyRefreshError,
    refresh_tunnel_topology_attestation,
)

DEFAULT_HEARTBEAT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class TopologyHeartbeatOutcome:
    healthy: bool
    state: str
    reason: str
    qualified: bool

    def public_dict(self) -> dict[str, str | bool]:
        return {
            "healthy": self.healthy,
            "state": self.state,
            "reason": self.reason,
            "qualified": self.qualified,
        }


def run_topology_heartbeat_once(
    config_dir: Path,
    *,
    refresh: Callable[[Path], dict[str, str | bool]] = (
        refresh_tunnel_topology_attestation
    ),
) -> TopologyHeartbeatOutcome:
    """Run one bounded topology refresh without exposing private evidence."""

    try:
        result = refresh(config_dir)
    except TunnelTopologyRefreshError:
        return TopologyHeartbeatOutcome(
            healthy=False,
            state="unavailable",
            reason="topology_refresh_unavailable",
            qualified=False,
        )

    state = result.get("state")
    reason = result.get("reason")
    qualified = result.get("qualified")
    if (
        not isinstance(state, str)
        or not isinstance(reason, str)
        or not isinstance(qualified, bool)
        or not 1 <= len(state) <= 64
        or not 1 <= len(reason) <= 96
        or not state.isascii()
        or not reason.isascii()
    ):
        return TopologyHeartbeatOutcome(
            healthy=False,
            state="invalid",
            reason="topology_refresh_invalid",
            qualified=False,
        )
    return TopologyHeartbeatOutcome(
        healthy=True,
        state=state,
        reason=reason,
        qualified=qualified,
    )


def run_topology_heartbeat_forever(
    config_dir: Path,
    *,
    refresh: Callable[[Path], dict[str, str | bool]] = (
        refresh_tunnel_topology_attestation
    ),
    sleep: Callable[[float], object] = time.sleep,
    interval_seconds: float = DEFAULT_HEARTBEAT_SECONDS,
) -> None:
    """Continuously refresh topology evidence at one fixed bounded cadence."""

    if isinstance(interval_seconds, bool) or not 5.0 <= interval_seconds <= 30.0:
        raise ValueError("topology heartbeat interval is outside supported bounds")

    while True:
        run_topology_heartbeat_once(
            config_dir,
            refresh=refresh,
        )
        sleep(interval_seconds)
