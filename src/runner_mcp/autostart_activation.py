from __future__ import annotations

import dataclasses
import enum


class AutostartActivationState(enum.StrEnum):
    CLEAR = "autostart_activation_clear"
    EMERGENCY_STOP_ACTIVE = "emergency_stop_active"
    INSTALL_RECOVERY_BLOCKED = "install_recovery_blocked"
    SELF_UPDATE_RESTART_PENDING = "self_update_restart_pending"
    RUNTIME_SMOKE_FAILED = "runtime_smoke_failed"
    HOST_INTEGRITY_BLOCKED = "host_integrity_blocked"


@dataclasses.dataclass(frozen=True, slots=True)
class AutostartActivationPermit:
    _state: AutostartActivationState

    @classmethod
    def clear(cls) -> "AutostartActivationPermit":
        return cls(AutostartActivationState.CLEAR)

    @property
    def is_clear(self) -> bool:
        return self._state is AutostartActivationState.CLEAR


def require_clear_autostart_permit(permit: AutostartActivationPermit | None) -> None:
    if not isinstance(permit, AutostartActivationPermit) or not permit.is_clear:
        raise PermissionError("autostart activation is not permitted")
