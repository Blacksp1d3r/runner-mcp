from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import runner_mcp.self_update_activation as activation


COMMIT = "a" * 40
OTHER = "b" * 40


def write_installed_state(config: Path, commit: str = COMMIT) -> None:
    config.mkdir(parents=True, exist_ok=True)
    (config / "self-update-state.json").write_text(
        '{"commit":"' + commit + '"}\n',
        encoding="utf-8",
    )
    (config / "self-update-state.json").chmod(0o600)


def write_server_marker(config: Path, commit: str = COMMIT) -> None:
    (config / "self-update-restart-server.marker").write_text(
        commit + "\n",
        encoding="utf-8",
    )
    (config / "self-update-restart-server.marker").chmod(0o600)


def test_old_process_cannot_consume_new_server_marker(tmp_path: Path) -> None:
    config = tmp_path / "private"
    write_installed_state(config)
    write_server_marker(config)

    assert activation.confirm_server_activation(config, process_commit=OTHER) is False
    assert activation.restart_marker_commit(config, "server") == COMMIT


def test_exact_new_process_consumes_server_marker_on_proof(tmp_path: Path) -> None:
    config = tmp_path / "private"
    write_installed_state(config)
    write_server_marker(config)

    assert activation.confirm_server_activation(config, process_commit=COMMIT) is True
    assert activation.restart_marker_commit(config, "server") is None


def test_installed_revision_mismatch_keeps_marker(tmp_path: Path) -> None:
    config = tmp_path / "private"
    write_installed_state(config, OTHER)
    write_server_marker(config, COMMIT)

    assert activation.confirm_server_activation(config, process_commit=COMMIT) is False
    assert activation.restart_marker_commit(config, "server") == COMMIT


def test_managed_cron_activation_uses_fixed_self_termination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activation, "has_managed_cron", lambda: True)
    monkeypatch.setattr(activation, "has_managed_user_units", lambda: False)
    monkeypatch.setattr(
        activation,
        "cron_status",
        lambda **_kwargs: [
            SimpleNamespace(
                component="server",
                installed=True,
                enabled=True,
                active=True,
            )
        ],
    )
    terminated: list[bool] = []

    backend = activation.activate_managed_server(
        tmp_path,
        terminate_self=lambda: terminated.append(True),
    )

    assert backend is activation.ManagedServerBackend.CRON
    assert terminated == [True]


def test_managed_systemd_activation_uses_fixed_server_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activation, "has_managed_cron", lambda: False)
    monkeypatch.setattr(activation, "has_managed_user_units", lambda: True)
    monkeypatch.setattr(
        activation,
        "user_service_status",
        lambda: [
            SimpleNamespace(
                component="server",
                installed=True,
                enabled=True,
                active=True,
            )
        ],
    )
    restarted: list[bool] = []
    monkeypatch.setattr(
        activation,
        "restart_managed_server_unit",
        lambda: restarted.append(True),
    )

    backend = activation.activate_managed_server(tmp_path)

    assert backend is activation.ManagedServerBackend.SYSTEMD_USER
    assert restarted == [True]


def test_multiple_or_missing_supervisors_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activation, "has_managed_cron", lambda: True)
    monkeypatch.setattr(activation, "has_managed_user_units", lambda: True)
    with pytest.raises(
        activation.ManagedServerActivationError,
        match="Multiple managed",
    ):
        activation.managed_server_activation_status(tmp_path)

    monkeypatch.setattr(activation, "has_managed_cron", lambda: False)
    monkeypatch.setattr(activation, "has_managed_user_units", lambda: False)
    with pytest.raises(
        activation.ManagedServerActivationError,
        match="unavailable",
    ):
        activation.managed_server_activation_status(tmp_path)


def test_activation_proof_middleware_confirms_only_after_http_request(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private"
    write_installed_state(config)
    write_server_marker(config)
    calls: list[str] = []

    async def app(scope, receive, send):
        calls.append(scope["type"])

    middleware = activation.ServerActivationProofMiddleware(
        app,
        config_dir=config,
    )
    assert activation.restart_marker_commit(config, "server") == COMMIT

    async def exercise() -> None:
        await middleware(
            {"type": "lifespan"},
            lambda: None,
            lambda _message: None,
        )
        assert activation.restart_marker_commit(config, "server") == COMMIT

        await middleware(
            {"type": "http"},
            lambda: None,
            lambda _message: None,
        )

    asyncio.run(exercise())
    assert activation.restart_marker_commit(config, "server") is None
    assert calls == ["lifespan", "http"]
