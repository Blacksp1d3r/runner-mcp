from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .onboarding import TunnelRestartConfigState, inspect_tunnel_restart_config
from .tunnel_readiness import (
    TunnelReadiness,
    TunnelReadinessEvidence,
    classify_tunnel_readiness,
)


@dataclass(frozen=True, slots=True)
class TunnelConfigReadiness:
    restart_config: TunnelRestartConfigState
    readiness: TunnelReadiness

    def public_dict(self) -> dict[str, str]:
        return {
            "restart_config": self.restart_config.value,
            **self.readiness.public_dict(),
        }


def collect_tunnel_config_readiness(config_dir: Path) -> TunnelConfigReadiness:
    """Collect bounded config evidence only; no process or network probing."""

    restart_config = inspect_tunnel_restart_config(config_dir)
    readiness = classify_tunnel_readiness(
        TunnelReadinessEvidence(
            configured=restart_config is TunnelRestartConfigState.COMPLETE,
        )
    )
    return TunnelConfigReadiness(
        restart_config=restart_config,
        readiness=readiness,
    )
