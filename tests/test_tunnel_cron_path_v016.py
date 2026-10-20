"""Minimal-cron PATH regression for the fixed managed tunnel-client launcher."""

import os
from pathlib import Path

import pytest

from runner_mcp.tunnel_runtime import TunnelRuntimeError, _resolve_tunnel_client


def _fake_executable(path: Path, *, executable: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700 if executable else 0o600)
    return path


def test_service_user_install_available_with_minimal_cron_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    client = _fake_executable(tmp_path / ".local" / "bin" / "tunnel-client")
    assert _resolve_tunnel_client() == client.resolve()


def test_existing_system_path_fallback_remains_supported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    system_client = _fake_executable(tmp_path / "system" / "bin" / "tunnel-client")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(system_client.parent))
    assert _resolve_tunnel_client() == system_client.resolve()


def test_unexecutable_service_user_client_fails_closed_without_path_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _fake_executable(
        tmp_path / ".local" / "bin" / "tunnel-client", executable=False
    )
    other = _fake_executable(tmp_path / "other" / "tunnel-client")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", str(other.parent))
    assert client.is_file()
    assert not os.access(client, os.X_OK)
    with pytest.raises(TunnelRuntimeError, match="tunnel-client is unavailable"):
        _resolve_tunnel_client()


def test_broken_service_user_link_does_not_fall_through_to_different_binary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    local = tmp_path / ".local" / "bin" / "tunnel-client"
    local.parent.mkdir(parents=True)
    local.symlink_to("not-present")
    other = _fake_executable(tmp_path / "other" / "tunnel-client")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", str(other.parent))
    with pytest.raises(TunnelRuntimeError, match="tunnel-client is unavailable"):
        _resolve_tunnel_client()
