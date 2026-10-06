from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp import fabric_agent_qualification as qualification
from runner_mcp.fabric_agent_qualification import (
    FabricAgentQualificationError,
    fabric_agent_qualification_configured,
    run_fabric_agent_qualification_process,
)
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


def _private_config(tmp_path: Path):
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


def _append_bridge(paths, *, endpoint: str = "http://127.0.0.1:9020/mcp") -> str:
    token = "q" * 48
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"RUNNER_FABRIC_AGENT_RESOURCE_URL={endpoint}\n")
        handle.write(f"RUNNER_FABRIC_AGENT_BEARER_TOKEN={token}\n")
    return token


def test_qualification_agent_is_optional_until_bridge_is_complete(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)

    assert fabric_agent_qualification_configured(paths.config_dir) is False

    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(
            "RUNNER_FABRIC_AGENT_RESOURCE_URL=http://127.0.0.1:9020/mcp\n"
        )

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is incomplete",
    ):
        fabric_agent_qualification_configured(paths.config_dir)


def test_qualification_agent_rejects_non_loopback_endpoint(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths, endpoint="http://fabric.example.invalid:9020/mcp")

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is invalid",
    ):
        fabric_agent_qualification_configured(paths.config_dir)


def test_qualification_agent_forwards_only_fixed_optional_target_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    token = _append_bridge(paths)
    external_config = tmp_path / "private-target.json"
    external_config.write_text("{}\n", encoding="utf-8")
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG={external_config}\n")
        handle.write("UNRELATED_PRIVATE_VALUE=must-not-leak\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == token
    assert environment["RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG"] == str(external_config)
    assert "UNRELATED_PRIVATE_VALUE" not in environment
    assert set(environment) == {
        "HOME",
        "PATH",
        "LANG",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN",
        "RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG",
    }


def test_qualification_agent_rejects_relative_external_target_config(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG=relative.json\n")

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is invalid",
    ):
        run_fabric_agent_qualification_process(paths.config_dir, execve=lambda *_: object())


def test_qualification_agent_execs_only_fixed_qualification_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    token = _append_bridge(paths)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert (
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=fake_execve,
        )
        == 0
    )

    assert captured["path"] == str(executable)
    assert captured["argv"] == [str(executable), "agent-serve-qualification"]
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["RUNNER_FABRIC_AGENT_RESOURCE_URL"] == (
        "http://127.0.0.1:9020/mcp"
    )
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == token
    assert set(environment) == {
        "HOME",
        "PATH",
        "LANG",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN",
    }


def test_qualification_agent_start_failure_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    secret = _append_bridge(paths)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )

    def fail_execve(_path: str, _argv: list[str], _env: dict[str, str]) -> object:
        raise OSError(f"private={secret}")

    with pytest.raises(FabricAgentQualificationError) as exc:
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=fail_execve,
        )

    assert str(exc.value) == "Runner Fabric qualification agent could not start"
    assert secret not in str(exc.value)


_A6_VALUES = {
    "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": "/private/a6-journal",
    "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN": "control:evidence",
    "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN": "target:runner-mcp",
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": "http://127.0.0.1:8000/mcp",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": "r" * 48,
    "RUNNER_FABRIC_SYNTHETIC_PROBE_ID": "fleet-a6",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT": "runner:aifordable-lab",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION": "f" * 40,
    "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS": "60",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT": "/private/a6-evidence",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION": "f" * 40,
}


def _append_a6(paths, values: dict[str, str] | None = None) -> None:
    selected = _A6_VALUES if values is None else values
    with paths.env_file.open("a", encoding="utf-8") as handle:
        for key, value in selected.items():
            handle.write(f"{key}={value}\n")


def test_qualification_agent_forwards_complete_fixed_a6_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_a6(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("UNRELATED_PRIVATE_VALUE=must-not-leak\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    environment = captured["env"]
    assert isinstance(environment, dict)
    for key, value in _A6_VALUES.items():
        assert environment[key] == value
    assert "UNRELATED_PRIVATE_VALUE" not in environment


def test_qualification_agent_rejects_partial_a6_binding(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_a6(
        paths,
        {"RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": "/private/a6-journal"},
    )

    with pytest.raises(
        FabricAgentQualificationError,
        match="A6 qualification configuration is incomplete",
    ):
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=lambda *_: object(),
        )
