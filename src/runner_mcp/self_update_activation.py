from __future__ import annotations

import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .autostart import (
    AutostartError,
    has_managed_user_units,
    restart_managed_server_unit,
    user_service_status,
)
from .cron_autostart import (
    CronAutostartError,
    cron_status,
    has_managed_cron,
)
from .self_update import (
    SelfUpdateError,
    confirm_server_activation,
    installed_self_update_commit,
)


class ManagedServerActivationError(RuntimeError):
    """Bounded managed-supervisor activation failure."""


class ManagedServerBackend(StrEnum):
    CRON = "cron"
    SYSTEMD_USER = "systemd-user"


@dataclass(frozen=True, slots=True)
class ManagedServerActivationStatus:
    backend: ManagedServerBackend
    installed: bool
    enabled: bool
    active: bool

    @property
    def ready(self) -> bool:
        return self.installed and self.enabled and self.active

    def public_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend.value,
            "installed": self.installed,
            "enabled": self.enabled,
            "active": self.active,
            "ready": self.ready,
        }


def managed_server_activation_status(
    config_dir: Path,
) -> ManagedServerActivationStatus:
    """Inspect exactly one Runner-MCP-managed server supervisor."""

    try:
        cron = has_managed_cron()
        systemd = has_managed_user_units()
    except (CronAutostartError, AutostartError) as exc:
        raise ManagedServerActivationError(
            "Managed server supervisor state is unavailable"
        ) from exc

    if cron and systemd:
        raise ManagedServerActivationError(
            "Multiple managed server supervisors are present"
        )
    if not cron and not systemd:
        raise ManagedServerActivationError(
            "Managed server supervisor is unavailable"
        )

    if cron:
        try:
            rows = cron_status(
                config_dir=config_dir,
                components=("server",),
            )
        except CronAutostartError as exc:
            raise ManagedServerActivationError(
                "Managed cron server state is unavailable"
            ) from exc
        row = next((item for item in rows if item.component == "server"), None)
        if row is None:
            raise ManagedServerActivationError(
                "Managed cron server state is unavailable"
            )
        return ManagedServerActivationStatus(
            backend=ManagedServerBackend.CRON,
            installed=row.installed,
            enabled=row.enabled,
            active=row.active,
        )

    try:
        rows = user_service_status()
    except AutostartError as exc:
        raise ManagedServerActivationError(
            "Managed systemd server state is unavailable"
        ) from exc
    row = next((item for item in rows if item.component == "server"), None)
    if row is None:
        raise ManagedServerActivationError(
            "Managed systemd server state is unavailable"
        )
    return ManagedServerActivationStatus(
        backend=ManagedServerBackend.SYSTEMD_USER,
        installed=row.installed,
        enabled=row.enabled,
        active=row.active,
    )


def activate_managed_server(
    config_dir: Path,
    *,
    terminate_self: Callable[[], object] | None = None,
) -> ManagedServerBackend:
    """Hand off activation only to the already-managed fixed server supervisor."""

    status = managed_server_activation_status(config_dir)
    if not status.ready:
        raise ManagedServerActivationError(
            "Managed server supervisor is not ready"
        )

    if status.backend is ManagedServerBackend.SYSTEMD_USER:
        try:
            restart_managed_server_unit()
        except AutostartError as exc:
            raise ManagedServerActivationError(
                "Managed systemd server restart failed"
            ) from exc
        return status.backend

    terminate = terminate_self or _terminate_current_process
    try:
        terminate()
    except OSError as exc:
        raise ManagedServerActivationError(
            "Managed cron server handoff failed"
        ) from exc
    return status.backend


def _terminate_current_process() -> None:
    os.kill(os.getpid(), signal.SIGTERM)



class ServerActivationProofMiddleware:
    """Consume only the exact server marker belonging to this running process."""

    def __init__(self, app, *, config_dir: Path) -> None:
        self.app = app
        self.config_dir = config_dir.expanduser().resolve()
        try:
            self.process_commit = installed_self_update_commit(self.config_dir)
        except SelfUpdateError:
            self.process_commit = None
        self._confirmed = False

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "http" and not self._confirmed:
            try:
                self._confirmed = confirm_server_activation(
                    self.config_dir,
                    process_commit=self.process_commit,
                )
            except SelfUpdateError:
                self._confirmed = False
        await self.app(scope, receive, send)
