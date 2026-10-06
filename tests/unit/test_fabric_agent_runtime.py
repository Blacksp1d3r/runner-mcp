from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp import fabric_agent_runtime as runtime
from runner_mcp.fabric_agent_runtime import (
    FabricAgentRestartError,
    restart_fabric_qualification_agent,
)


class _Process:
    def __init__(self, pid: int, *, returncode: int | None = None) -> None:
        self.pid = pid
        self._returncode = returncode
        self.terminated = False

    def poll(self) -> int | None:
        return self._returncode

    def terminate(self) -> None:
        self.terminated = True


def _managed_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    slot_bin = (
        home
        / ".local"
        / "state"
        / "runner-fabric"
        / "control-plane-update"
        / "slots"
        / ("a" * 40)
        / "bin"
    )
    slot_bin.mkdir(parents=True)
    target = slot_bin / "runner-fabric"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o700)
    launcher_dir = home / ".local" / "bin"
    launcher_dir.mkdir(parents=True)
    (launcher_dir / "runner-fabric").symlink_to(target)
    return home


def _config(tmp_path: Path) -> Path:
    config = tmp_path / "config"
    config.mkdir()
    return config.resolve()


def _patch_start(
    monkeypatch: pytest.MonkeyPatch,
    process: _Process,
) -> None:
    monkeypatch.setattr(runtime.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(runtime, "_wait_health", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        runtime,
        "qualification_agent_environment_additions",
        lambda _config: {},
    )


def test_restart_recovers_when_pid_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    process = _Process(43210)
    _patch_start(monkeypatch, process)

    result = restart_fabric_qualification_agent(
        config_dir=config,
        resource_url="http://127.0.0.1:9020/mcp",
        bearer_token="q" * 48,
        home=home,
    )

    assert result == {"state": "restarted", "pid_changed": True, "healthy": True}
    assert (config / "fabric-qualification.pid").read_text(encoding="ascii") == "43210\n"


def test_restart_recovers_when_recorded_pid_has_disappeared(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    (config / "fabric-qualification.pid").write_text("1234\n", encoding="ascii")
    monkeypatch.setattr(runtime, "_same_user_process", lambda _pid: False)
    monkeypatch.setattr(runtime, "_pid_exists", lambda _pid: False)
    process = _Process(43211)
    _patch_start(monkeypatch, process)

    result = restart_fabric_qualification_agent(
        config_dir=config,
        resource_url="http://127.0.0.1:9020/mcp",
        bearer_token="q" * 48,
        home=home,
    )

    assert result["healthy"] is True
    assert (config / "fabric-qualification.pid").read_text(encoding="ascii") == "43211\n"


def test_restart_rejects_pid_reused_by_another_live_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    (config / "fabric-qualification.pid").write_text("1234\n", encoding="ascii")
    monkeypatch.setattr(runtime, "_same_user_process", lambda _pid: False)
    monkeypatch.setattr(runtime, "_pid_exists", lambda _pid: True)

    def unexpected_start(*_args, **_kwargs):
        raise AssertionError("must not start over a live mismatched PID")

    monkeypatch.setattr(runtime.subprocess, "Popen", unexpected_start)

    with pytest.raises(
        FabricAgentRestartError,
        match="fabric_agent_process_mismatch",
    ):
        restart_fabric_qualification_agent(
            config_dir=config,
            resource_url="http://127.0.0.1:9020/mcp",
            bearer_token="q" * 48,
            home=home,
        )


def test_restart_keeps_live_process_restart_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    (config / "fabric-qualification.pid").write_text("1234\n", encoding="ascii")
    observations = iter((True, False))
    monkeypatch.setattr(runtime, "_same_user_process", lambda _pid: next(observations))
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(runtime.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    process = _Process(43212)
    _patch_start(monkeypatch, process)

    result = restart_fabric_qualification_agent(
        config_dir=config,
        resource_url="http://127.0.0.1:9020/mcp",
        bearer_token="q" * 48,
        home=home,
    )

    assert killed == [(1234, runtime.signal.SIGTERM)]
    assert result["healthy"] is True


def test_restart_rejects_spawn_that_exits_even_if_old_listener_looks_healthy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    process = _Process(43213, returncode=1)
    _patch_start(monkeypatch, process)

    with pytest.raises(
        FabricAgentRestartError,
        match="fabric_agent_health_failed",
    ):
        restart_fabric_qualification_agent(
            config_dir=config,
            resource_url="http://127.0.0.1:9020/mcp",
            bearer_token="q" * 48,
            home=home,
        )

    assert process.terminated is True


def test_restart_keeps_malformed_pid_fail_closed(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    (config / "fabric-qualification.pid").write_text("not-a-pid\n", encoding="ascii")

    with pytest.raises(FabricAgentRestartError, match="fabric_agent_pid_invalid"):
        restart_fabric_qualification_agent(
            config_dir=config,
            resource_url="http://127.0.0.1:9020/mcp",
            bearer_token="q" * 48,
            home=home,
        )


def test_restart_forwards_only_fixed_qualification_additions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    process = _Process(43214)
    additions = {
        "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": "/private/journal",
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": "http://127.0.0.1:8000/mcp",
    }
    monkeypatch.setattr(
        runtime,
        "qualification_agent_environment_additions",
        lambda _config: dict(additions),
    )
    monkeypatch.setattr(runtime, "_wait_health", lambda *_args, **_kwargs: True)
    captured: dict[str, object] = {}

    def fake_popen(*args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs["env"]
        return process

    monkeypatch.setattr(runtime.subprocess, "Popen", fake_popen)

    result = restart_fabric_qualification_agent(
        config_dir=config,
        resource_url="http://127.0.0.1:9020/mcp",
        bearer_token="q" * 48,
        home=home,
    )

    assert result["healthy"] is True
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["RUNNER_FABRIC_UPDATE_JOURNAL_ROOT"] == "/private/journal"
    assert environment["RUNNER_FABRIC_RUNNER_MCP_ENDPOINT"] == (
        "http://127.0.0.1:8000/mcp"
    )
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == "q" * 48


def test_restart_fails_closed_when_fixed_qualification_binding_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    home = _managed_home(tmp_path)
    monkeypatch.setattr(
        runtime,
        "qualification_agent_environment_additions",
        lambda _config: (_ for _ in ()).throw(
            FabricAgentQualificationError("invalid")
        ),
    )

    with pytest.raises(FabricAgentRestartError, match="fabric_agent_config_invalid"):
        restart_fabric_qualification_agent(
            config_dir=config,
            resource_url="http://127.0.0.1:9020/mcp",
            bearer_token="q" * 48,
            home=home,
        )
