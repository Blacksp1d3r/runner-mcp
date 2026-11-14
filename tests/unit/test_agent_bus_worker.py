from __future__ import annotations

from pathlib import Path

import pytest

import runner_mcp.agent_bus_worker as worker_module
from runner_mcp.agent_bus_worker import (
    AgentBusWorkerError,
    agent_bus_convergence_status,
    agent_bus_worker_configured,
    agent_bus_worker_preflight,
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


def test_convergence_is_not_initialized_before_worker_state_exists(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)

    assert agent_bus_convergence_status(paths.config_dir) == {
        "state": "not_initialized",
        "pending_results": 0,
    }


def test_convergence_reports_clear_private_results_directory(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)
    state_root = paths.config_dir / "agent-bus-state"
    results = state_root / "results"
    state_root.mkdir(mode=0o700)
    results.mkdir(mode=0o700)

    assert agent_bus_convergence_status(paths.config_dir) == {
        "state": "clear",
        "pending_results": 0,
    }


def test_convergence_reports_pending_count_without_reading_payloads(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)
    state_root = paths.config_dir / "agent-bus-state"
    results = state_root / "results"
    state_root.mkdir(mode=0o700)
    results.mkdir(mode=0o700)
    for name in ("a.json", "b.json"):
        target = results / name
        target.write_text("not parsed", encoding="utf-8")
        target.chmod(0o600)

    assert agent_bus_convergence_status(paths.config_dir) == {
        "state": "pending",
        "pending_results": 2,
    }


def test_convergence_fails_closed_on_unexpected_state_entry(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)
    state_root = paths.config_dir / "agent-bus-state"
    results = state_root / "results"
    state_root.mkdir(mode=0o700)
    results.mkdir(mode=0o700)
    unexpected = results / ".control-result-interrupted"
    unexpected.write_text("partial", encoding="utf-8")
    unexpected.chmod(0o600)

    assert agent_bus_convergence_status(paths.config_dir) == {
        "state": "invalid",
        "pending_results": 0,
    }


def test_convergence_fails_closed_on_symlinked_result(
    tmp_path: Path,
) -> None:
    paths = private_config(tmp_path)
    state_root = paths.config_dir / "agent-bus-state"
    results = state_root / "results"
    state_root.mkdir(mode=0o700)
    results.mkdir(mode=0o700)
    outside = tmp_path / "outside"
    outside.write_text("private", encoding="utf-8")
    (results / "a.json").symlink_to(outside)

    assert agent_bus_convergence_status(paths.config_dir) == {
        "state": "invalid",
        "pending_results": 0,
    }


def test_read_only_preflight_existing_valid_private_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    executable = tmp_path / "fake-fixed-launcher"
    executable.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module, "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )
    before = sorted(p.name for p in paths.config_dir.iterdir())
    assert agent_bus_worker_preflight(paths.config_dir) == {
        "state": "ready", "reason_code": "local_static_prerequisites_ready",
    }
    assert sorted(p.name for p in paths.config_dir.iterdir()) == before
    assert not (paths.config_dir / "agent-bus-state").exists()


def test_read_only_preflight_missing_and_partial_relay(tmp_path: Path) -> None:
    paths = private_config(tmp_path)
    assert agent_bus_worker_preflight(paths.config_dir) == {
        "state": "wait", "reason_code": "relay_not_configured",
    }
    append_env(paths.env_file, {"RUNNER_FABRIC_RELAY_ORIGIN": "https://relay.invalid"})
    assert agent_bus_worker_preflight(paths.config_dir) == {
        "state": "blocked", "reason_code": "relay_configuration_incomplete",
    }
    assert not (paths.config_dir / "agent-bus-state").exists()


def test_read_only_preflight_invalid_relay_and_loopback(tmp_path: Path) -> None:
    paths = private_config(tmp_path)
    v = relay_values()
    v["RUNNER_FABRIC_RELAY_ORIGIN"] = "http://relay.invalid"
    append_env(paths.env_file, v)
    assert agent_bus_worker_preflight(paths.config_dir)["reason_code"] == (
        "relay_configuration_invalid"
    )

    second = tmp_path / "second"
    second.mkdir()
    other = private_config(second)
    v = relay_values()
    v["RUNNER_MCP_AGENT_BUS_LOCAL_ENDPOINT"] = "http://untrusted.invalid/mcp"
    append_env(other.env_file, v)
    assert agent_bus_worker_preflight(other.config_dir)["reason_code"] == (
        "loopback_endpoint_invalid"
    )


def test_read_only_preflight_missing_fabric_is_wait(tmp_path: Path, monkeypatch) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    def missing() -> Path:
        raise AgentBusWorkerError("Runner Fabric executable is unavailable")
    monkeypatch.setattr(worker_module, "_fixed_runner_fabric_executable", missing)
    assert agent_bus_worker_preflight(paths.config_dir) == {
        "state": "wait", "reason_code": "fabric_launcher_unavailable",
    }
    assert not (paths.config_dir / "agent-bus-state").exists()


def test_read_only_preflight_rejects_symlinked_durable_state(
    tmp_path: Path, monkeypatch,
) -> None:
    paths = private_config(tmp_path)
    append_env(paths.env_file, relay_values())
    monkeypatch.setattr(
        worker_module, "_fixed_runner_fabric_executable", lambda: tmp_path,
    )
    (paths.config_dir / "agent-bus-state").symlink_to(tmp_path)
    assert agent_bus_worker_preflight(paths.config_dir) == {
        "state": "blocked", "reason_code": "durable_state_unsafe",
    }


def test_read_only_preflight_cli_does_not_claim_ack_or_emit_secret(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.cli import main

    paths = private_config(tmp_path)
    values = relay_values()
    values["RUNNER_FABRIC_RELAY_CREDENTIAL"] = "s" * 48
    append_env(paths.env_file, values)
    monkeypatch.setattr(
        worker_module, "_fixed_runner_fabric_executable", lambda: tmp_path,
    )
    assert main(["--config-dir", str(paths.config_dir), "agent-bus", "preflight"]) == 0
    output = capsys.readouterr()
    assert "state=ready" in output.out
    assert "original_client_ack_proven=false" in output.out
    assert "s" * 48 not in output.out + output.err
    assert str(tmp_path) not in output.out
    assert not (paths.config_dir / "agent-bus-state").exists()


def test_a7_original_worker_uses_new_private_credential_only_after_supervisor_reexec_and_restores_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A7: real existing worker execve reads its PRIVATE config each launch.

    This is a disposable source-level worker boundary test, not an original
    host rotation, SQL provider transaction or service/cron activation proof.
    """
    paths = private_config(tmp_path)
    original_credential = "r" * 48
    replacement_credential = "n" * 48
    append_env(
        paths.env_file,
        {
            **relay_values(),
            "RUNNER_MCP_GITHUB_TOKEN": "g" * 48,
        },
    )
    original_bytes = paths.env_file.read_bytes()
    before_mode = paths.env_file.stat().st_mode & 0o777
    original_line = (
        "RUNNER_FABRIC_RELAY_CREDENTIAL=" + original_credential + "\n"
    ).encode("ascii")
    next_line = (
        "RUNNER_FABRIC_RELAY_CREDENTIAL=" + replacement_credential + "\n"
    ).encode("ascii")
    assert original_bytes.count(original_line) == 1
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        worker_module,
        "_fixed_runner_fabric_executable",
        lambda: executable.resolve(),
    )

    captured: list[dict[str, str]] = []

    def observe_execve(
        _path: str, _argv: list[str], environment: dict[str, str],
    ) -> object:
        captured.append(dict(environment))
        return object()

    assert run_agent_bus_worker_process(
        paths.config_dir, execve=observe_execve,
    ) == 0
    assert captured[-1]["RUNNER_FABRIC_RELAY_CREDENTIAL"] == original_credential
    assert "RUNNER_MCP_GITHUB_TOKEN" not in captured[-1]

    # Represents the already owner-qualified, private atomic-file replacement.
    # No serving process or cron task is touched by this synthetic fixture.
    next_bytes = original_bytes.replace(original_line, next_line)
    assert next_bytes != original_bytes
    paths.env_file.write_bytes(next_bytes)
    assert paths.env_file.stat().st_mode & 0o777 == before_mode

    assert run_agent_bus_worker_process(
        paths.config_dir, execve=observe_execve,
    ) == 0
    assert captured[-1]["RUNNER_FABRIC_RELAY_CREDENTIAL"] == replacement_credential
    assert captured[-1]["RUNNER_FABRIC_RELAY_SUBJECT"] == "runner:one"
    assert "RUNNER_MCP_GITHUB_TOKEN" not in captured[-1]

    def fail_new_exec(
        _path: str, _argv: list[str], environment: dict[str, str],
    ) -> object:
        assert environment["RUNNER_FABRIC_RELAY_CREDENTIAL"] == replacement_credential
        raise OSError("synthetic private start failure")

    with pytest.raises(
        AgentBusWorkerError, match="Agent Bus worker could not start",
    ) as error:
        run_agent_bus_worker_process(paths.config_dir, execve=fail_new_exec)
    assert replacement_credential not in str(error.value)

    # Independent operator rollback restores the original exact config.
    paths.env_file.write_bytes(original_bytes)
    assert paths.env_file.read_bytes() == original_bytes
    assert paths.env_file.stat().st_mode & 0o777 == before_mode
    assert run_agent_bus_worker_process(
        paths.config_dir, execve=observe_execve,
    ) == 0
    assert captured[-1]["RUNNER_FABRIC_RELAY_CREDENTIAL"] == original_credential
    assert captured[-1]["RUNNER_FABRIC_RELAY_SUBJECT"] == "runner:one"
    assert "RUNNER_MCP_GITHUB_TOKEN" not in captured[-1]
