"""Managed self-update handoff is source-only: never an A7 commit/ACK."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from runner_mcp.self_update_activation import (
    ManagedServerActivationError,
    ManagedServerBackend,
    activate_managed_server,
    managed_server_activation_status,
)


def _row(*, active: bool = True):
    return SimpleNamespace(
        component="server", installed=True, enabled=True, active=active,
    )


def test_cron_handoff_uses_fixed_self_termination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: False,
    )
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.cron_status",
        lambda **kwargs: [_row()],
    )
    terminated: list[bool] = []
    backend = activate_managed_server(
        tmp_path, terminate_self=lambda: terminated.append(True),
    )
    assert backend is ManagedServerBackend.CRON
    assert terminated == [True]


def test_systemd_handoff_uses_existing_fixed_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: False,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.user_service_status", lambda: [_row()],
    )
    restarted: list[bool] = []
    monkeypatch.setattr(
        "runner_mcp.autostart.restart_managed_server_unit",
        lambda: restarted.append(True),
    )
    assert activate_managed_server(tmp_path) is ManagedServerBackend.SYSTEMD_USER
    assert restarted == [True]


@pytest.mark.parametrize("cron,systemd", [(True, True), (False, False)])
def test_multiple_or_missing_managers_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    cron: bool, systemd: bool,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: cron,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: systemd,
    )
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.cron_status",
        lambda **kwargs: [_row()],
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.user_service_status",
        lambda: [_row()],
    )
    with pytest.raises(
        ManagedServerActivationError, match="missing or multiple",
    ):
        activate_managed_server(tmp_path)


def test_inactive_manager_denies_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: False,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.user_service_status",
        lambda: [_row(active=False)],
    )
    with pytest.raises(ManagedServerActivationError, match="not active"):
        activate_managed_server(tmp_path)


def test_cron_readback_error_does_not_kill_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.cron_autostart import CronAutostartError

    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: False,
    )

    def reject(**kwargs):
        raise CronAutostartError("synthetic unreadable crontab")

    monkeypatch.setattr("runner_mcp.cron_autostart.cron_status", reject)
    executed: list[bool] = []
    with pytest.raises(ManagedServerActivationError, match="unreadable"):
        activate_managed_server(
            tmp_path, terminate_self=lambda: executed.append(True),
        )
    assert executed == []


def test_partial_cron_to_systemd_peer_migration_is_not_duplicate_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One cron SERVER plus an unrelated systemd peer is still one server."""
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: True,
    )
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.cron_status",
        lambda **kwargs: [_row()],
    )
    monkeypatch.setattr(
        "runner_mcp.autostart.user_service_status",
        lambda: [
            SimpleNamespace(
                component="server", installed=False,
                enabled=False, active=False,
            ),
            SimpleNamespace(
                component="topology-heartbeat", installed=True,
                enabled=True, active=True,
            ),
        ],
    )
    assert (
        managed_server_activation_status(tmp_path).backend
        is ManagedServerBackend.CRON
    )
