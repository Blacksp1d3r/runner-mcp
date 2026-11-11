"""#253 existing-self-update handoff to one already managed local supervisor.

This module NEVER arms, clears, or commits an A7 checkpoint. Its call path is
opt-in only after external independent A7 recovery has been proven. A matching
HTTP request or healthy port is NOT an original-client end-to-end ACK.
"""
from __future__ import annotations

import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ManagedServerActivationError(RuntimeError):
    """One fixed owner-local activation boundary was not qualified."""


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


def managed_server_activation_status(
    config_dir: Path,
) -> ManagedServerActivationStatus:
    """Require one already active and managed server, never select a new unit."""
    from .autostart import (
        AutostartError,
        has_managed_user_units,
        user_service_status,
    )
    from .cron_autostart import (
        CronAutostartError,
        cron_status,
        has_managed_cron,
    )

    try:
        cron = has_managed_cron()
        systemd = has_managed_user_units()
    except (CronAutostartError, AutostartError) as exc:
        raise ManagedServerActivationError(
            "managed server supervisor state unavailable"
        ) from exc
    if cron == systemd:
        raise ManagedServerActivationError(
            "missing or multiple managed supervisor generations"
        )
    try:
        rows = (
            cron_status(config_dir=config_dir, components=("server",))
            if cron
            else user_service_status()
        )
    except (CronAutostartError, AutostartError) as exc:
        raise ManagedServerActivationError(
            "managed server supervisor state unreadable"
        ) from exc
    found = [row for row in rows if row.component == "server"]
    if len(found) != 1:
        raise ManagedServerActivationError(
            "managed server service identity ambiguous"
        )
    row = found[0]
    return ManagedServerActivationStatus(
        backend=ManagedServerBackend.CRON if cron else ManagedServerBackend.SYSTEMD_USER,
        installed=row.installed,
        enabled=row.enabled,
        active=row.active,
    )


def activate_managed_server(
    config_dir: Path,
    *,
    terminate_self: Callable[[], object] | None = None,
) -> ManagedServerBackend:
    """Handoff ONLY after an external A7 admission and explicit opt-in.

    Does not consume the restart marker, disarm A7, or claim result/ACK.
    An independent A7 actor must retain rollback through the live deadline.
    """
    status = managed_server_activation_status(config_dir)
    if not status.ready:
        raise ManagedServerActivationError(
            "managed server is not active and ready"
        )
    if status.backend is ManagedServerBackend.SYSTEMD_USER:
        from .autostart import AutostartError, restart_managed_server_unit

        try:
            restart_managed_server_unit()
        except AutostartError as exc:
            raise ManagedServerActivationError(
                "managed systemd server restart failed"
            ) from exc
        return status.backend
    terminate = terminate_self or _terminate_current_process
    try:
        terminate()
    except OSError as exc:
        raise ManagedServerActivationError(
            "managed cron server handoff failed"
        ) from exc
    return status.backend


def _terminate_current_process() -> None:
    os.kill(os.getpid(), signal.SIGTERM)
