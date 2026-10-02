from __future__ import annotations

from pathlib import Path

import pytest

import runner_mcp.agent_bus_worker as worker_module
from runner_mcp.agent_bus_worker import (
    AgentBusWorkerError,
    agent_bus_worker_configured,
    run_agent_bus_worker_process,
)
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


def private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "private"
    paths = install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    return paths


def append_env(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def relay_values() -> dict[str, str]:
    return {
        "RUNNER_FABRIC_RELAY_ORIGIN": "https://relay.example.invalid",
        "RUNNER_FABRIC_RELAY_SUBJECT": "runner:one",
        "RUNNER_FABRIC_RELAY_CREDENTIAL": "r" * 48,
        "RUNNER_FABRIC_AGENT_RESOURCE_URL": "http://127.0.0.1:9020/mcp",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN": "a" * 48,
    }


def test_agent_bus_configuration_is_all_or_nothing(tmp_path: Path) -> None:
    paths = private_config(tmp_path)

    assert agent_bus_worker_configured(paths.config_dir) is False

    append_env(
        paths.env_file,
        {"RUNNER_FABRIC_RELAY_ORIGIN": "https://relay.example.invalid"},
    )

    with pytest.raises(AgentBusWorkerError, match="incomplete"):
        agent_bus_worker_configured(paths.config_dir)


def test_worker_execs_only_fixed_runner_fabric_command_and_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(
        paths.env_file,
        {
            **relay_values(),
            "RUNNER_MCP_GITHUB_TOKEN": "g" * 48,
        },
    )
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )

    captured: dict[str, object] = {}

    def fake_execve(
        path: str,
        argv: list[str],
        environment: dict[str, str],
    ) -> object:
        captured["path"] = path
        captured["argv"] = argv
        captured["environment"] = environment
        return object()

    assert run_agent_bus_worker_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    environment = captured["environment"]
    assert captured["path"] == str(executable.resolve())
    assert captured["argv"] == [str(executable.resolve()), "agent-bus-run"]
    assert environment["RUNNER_FABRIC_RELAY_SUBJECT"] == "runner:one"
    assert environment["RUNNER_FABRIC_RUNNER_MCP_ENDPOINT"] == (
        "http://127.0.0.1:8000/mcp"
    )
    assert environment["RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN"]
    assert environment["RUNNER_FABRIC_AGENT_RESOURCE_URL"] == (
        "http://127.0.0.1:9020/mcp"
    )
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == "a" * 48
    assert environment["RUNNER_FABRIC_AGENT_BUS_STATE_ROOT"].endswith(
        "/agent-bus-state"
    )
    assert "RUNNER_MCP_GITHUB_TOKEN" not in environment
    assert "RUNNER_MCP_GITHUB_REPOSITORY" not in environment



def test_worker_rejects_tampered_relay_config_before_exec(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)
    append_env(
        paths.env_file,
        {
            "RUNNER_FABRIC_RELAY_ORIGIN": "http://relay.example.invalid",
            "RUNNER_FABRIC_RELAY_SUBJECT": "runner:one",
            "RUNNER_FABRIC_RELAY_CREDENTIAL": "r" * 48,
            "RUNNER_FABRIC_AGENT_RESOURCE_URL": "http://127.0.0.1:9020/mcp",
            "RUNNER_FABRIC_AGENT_BEARER_TOKEN": "a" * 48,
        },
    )
    called: list[bool] = []

    with pytest.raises(AgentBusWorkerError, match="relay configuration is invalid"):
        run_agent_bus_worker_process(
            paths.config_dir,
            execve=lambda *_args: called.append(True),
        )

    assert called == []

def test_worker_rejects_non_loopback_local_endpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(
        paths.env_file,
        {
            **relay_values(),
            "RUNNER_MCP_AGENT_BUS_LOCAL_ENDPOINT": (
                "https://private-runner.example.invalid/mcp"
            ),
        },
    )
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: tmp_path / "unused",
    )

    with pytest.raises(AgentBusWorkerError, match="configuration is invalid"):
        run_agent_bus_worker_process(
            paths.config_dir,
            execve=lambda *_args: object(),
        )


def test_worker_state_root_is_private(tmp_path: Path, monkeypatch) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )

    run_agent_bus_worker_process(
        paths.config_dir,
        execve=lambda *_args: object(),
    )

    state_root = paths.config_dir / "agent-bus-state"
    assert state_root.is_dir()
    assert state_root.stat().st_mode & 0o077 == 0


def test_worker_start_error_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )

    sensitive = "private-relay-secret"

    def fail(*_args) -> object:
        raise OSError(sensitive)

    with pytest.raises(AgentBusWorkerError) as captured:
        run_agent_bus_worker_process(paths.config_dir, execve=fail)

    assert str(captured.value) == "Agent Bus worker could not start"
    assert sensitive not in str(captured.value)


def test_worker_once_execs_only_fixed_one_shot_runner_fabric_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )

    captured: dict[str, object] = {}

    def fake_execve(
        path: str,
        argv: list[str],
        environment: dict[str, str],
    ) -> object:
        captured["path"] = path
        captured["argv"] = argv
        captured["environment"] = environment
        return object()

    assert run_agent_bus_worker_process(
        paths.config_dir,
        once=True,
        execve=fake_execve,
    ) == 0

    assert captured["path"] == str(executable.resolve())
    assert captured["argv"] == [
        str(executable.resolve()),
        "agent-bus-run-once",
    ]
    environment = captured["environment"]
    assert environment["RUNNER_FABRIC_RELAY_SUBJECT"] == "runner:one"
    assert "RUNNER_MCP_GITHUB_TOKEN" not in environment


def test_worker_rejects_non_boolean_once(tmp_path: Path) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())

    with pytest.raises(TypeError, match="once must be a boolean"):
        run_agent_bus_worker_process(
            paths.config_dir,
            once="yes",  # type: ignore[arg-type]
            execve=lambda *_args: object(),
        )


def test_worker_rejects_non_loopback_agent_mcp_endpoint_before_exec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    values = relay_values()
    values["RUNNER_FABRIC_AGENT_RESOURCE_URL"] = (
        "http://fabric.example.invalid:9020/mcp"
    )
    append_env(paths.env_file, values)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: tmp_path / "unused",
    )
    called: list[bool] = []

    with pytest.raises(AgentBusWorkerError, match="configuration is invalid"):
        run_agent_bus_worker_process(
            paths.config_dir,
            execve=lambda *_args: called.append(True),
        )

    assert called == []


def test_worker_rejects_invalid_agent_mcp_token_before_exec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    values = relay_values()
    values["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] = "short"
    append_env(paths.env_file, values)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: tmp_path / "unused",
    )
    called: list[bool] = []

    with pytest.raises(AgentBusWorkerError, match="configuration is invalid"):
        run_agent_bus_worker_process(
            paths.config_dir,
            execve=lambda *_args: called.append(True),
        )

    assert called == []
