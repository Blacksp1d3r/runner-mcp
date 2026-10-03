from __future__ import annotations

from pathlib import Path

import pytest

import runner_mcp.fabric_live_overview as overview
from runner_mcp.fabric_live_overview import (
    FabricLiveOverviewError,
    fabric_live_overview_configured,
    run_fabric_live_overview_process,
)
from runner_mcp.onboarding import (
    SetupAnswers,
    install_private_configuration,
)


def private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "private",
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_RELAY_ORIGIN=https://relay.example.invalid\n")
        handle.write("RUNNER_FABRIC_RELAY_SUBJECT=runner:aifordable-lab\n")
        handle.write(f"RUNNER_FABRIC_RELAY_CREDENTIAL={'r' * 48}\n")
        handle.write(
            "RUNNER_FABRIC_AGENT_RESOURCE_URL=http://127.0.0.1:9020/mcp\n"
        )
        handle.write(f"RUNNER_FABRIC_AGENT_BEARER_TOKEN={'a' * 48}\n")
    return paths


def safe_live_config(tmp_path: Path) -> Path:
    path = tmp_path / "live-overview.v1.json"
    path.write_text('{"schemaVersion":"placeholder"}', encoding="utf-8")
    path.chmod(0o600)
    return path


def test_optional_overview_requires_private_fixed_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(
        overview,
        "_fixed_live_overview_config",
        lambda: missing,
    )
    assert fabric_live_overview_configured(paths.config_dir) is False

    configured = safe_live_config(tmp_path)
    monkeypatch.setattr(
        overview,
        "_fixed_live_overview_config",
        lambda: configured,
    )
    assert fabric_live_overview_configured(paths.config_dir) is True

    configured.chmod(0o644)
    with pytest.raises(FabricLiveOverviewError, match="unsafe"):
        fabric_live_overview_configured(paths.config_dir)


def test_wrapper_execs_only_fixed_command_with_sanitized_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = private_config(tmp_path)
    config = safe_live_config(tmp_path)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        overview,
        "_fixed_live_overview_config",
        lambda: config,
    )
    monkeypatch.setattr(
        overview,
        "_fixed_runner_fabric_executable",
        lambda: executable,
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

    assert run_fabric_live_overview_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    assert captured["path"] == str(executable)
    assert captured["argv"] == [
        str(executable),
        "live-overview-serve",
    ]
    environment = captured["environment"]
    assert environment["RUNNER_FABRIC_RELAY_SUBJECT"] == "runner:aifordable-lab"
    assert environment["RUNNER_FABRIC_AGENT_BUS_STATE_ROOT"].endswith(
        "agent-bus-state"
    )
    assert "RUNNER_FABRIC_RELAY_CREDENTIAL" not in environment
    assert "RUNNER_MCP_BEARER_TOKEN" not in environment
    assert "RUNNER_FABRIC_AGENT_BEARER_TOKEN" not in environment
    assert set(environment) == {
        "HOME",
        "PATH",
        "LANG",
        "RUNNER_FABRIC_RELAY_SUBJECT",
        "RUNNER_FABRIC_AGENT_BUS_STATE_ROOT",
    }
