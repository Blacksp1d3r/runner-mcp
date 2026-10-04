from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import runner_mcp.ci_runner_cron as cron
from runner_mcp.ci_runner_cron import (
    CIRunnerCronError,
    ci_runner_cron_status,
    install_ci_runner_cron,
    remove_ci_runner_cron,
    render_ci_runner_cron_block,
)
from runner_mcp.ci_runner_lifecycle import CIRunnerSpec


def specs(root: Path) -> dict[str, CIRunnerSpec]:
    return {
        "aifordable-lab-ci": CIRunnerSpec(
            alias="aifordable-lab-ci",
            repository="Blacksp1d3r/AIfordable",
            runner_name="aifordable-lab-ci",
            runner_root=root / "runner",
            work_root=root / "runner" / "_work",
            labels=("aifordable-ci",),
        )
    }


def prepare(tmp_path: Path) -> tuple[Path, Path]:
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o700)
    config = tmp_path / "config"
    config.mkdir()
    return executable, config


def fake_crontab(monkeypatch, initial: str = ""):
    state = {"value": initial}
    monkeypatch.setattr(cron, "_crontab_executable", lambda: "/usr/bin/crontab")

    def runner(argv, **kwargs):
        if argv[-1] == "-l":
            return subprocess.CompletedProcess(
                argv,
                0 if state["value"] else 1,
                state["value"],
                "",
            )
        state["value"] = kwargs["input"]
        return subprocess.CompletedProcess(argv, 0, "", "")

    return state, runner


def test_render_contains_only_alias_not_private_runner_values(tmp_path: Path) -> None:
    executable, config = prepare(tmp_path)
    private = tmp_path / "private"
    block = render_ci_runner_cron_block(
        executable=executable,
        config_dir=config,
        specs=specs(private),
    )
    rendered = "\n".join(block)

    assert "ci-runner run aifordable-lab-ci" in rendered
    assert "Blacksp1d3r/AIfordable" not in rendered
    assert str(private / "runner") not in rendered
    assert "aifordable-ci" not in rendered


def test_install_preserves_existing_cron_and_is_idempotent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable, config = prepare(tmp_path)
    state, runner = fake_crontab(monkeypatch, "5 * * * * echo existing\n")

    first = install_ci_runner_cron(
        executable=executable,
        config_dir=config,
        specs=specs(tmp_path),
        runner=runner,
    )
    second = install_ci_runner_cron(
        executable=executable,
        config_dir=config,
        specs=specs(tmp_path),
        runner=runner,
    )

    assert first == second
    assert state["value"].count(cron.CI_CRON_BEGIN) == 1
    assert "5 * * * * echo existing" in state["value"]


def test_remove_only_managed_ci_runner_block(tmp_path: Path, monkeypatch) -> None:
    executable, config = prepare(tmp_path)
    state, runner = fake_crontab(monkeypatch, "5 * * * * echo existing\n")
    install_ci_runner_cron(
        executable=executable,
        config_dir=config,
        specs=specs(tmp_path),
        runner=runner,
    )

    assert remove_ci_runner_cron(runner=runner) is True
    assert state["value"] == "5 * * * * echo existing\n"
    assert remove_ci_runner_cron(runner=runner) is False


def test_status_is_alias_only(tmp_path: Path, monkeypatch) -> None:
    executable, config = prepare(tmp_path)
    _state, runner = fake_crontab(monkeypatch)
    install_ci_runner_cron(
        executable=executable,
        config_dir=config,
        specs=specs(tmp_path),
        runner=runner,
    )

    assert ci_runner_cron_status(
        specs=specs(tmp_path),
        runner=runner,
    ).to_payload() == {
        "installed": True,
        "aliases": ["aifordable-lab-ci"],
    }


@pytest.mark.parametrize(
    "value",
    [
        "# BEGIN RUNNER MCP CI RUNNERS v1\n",
        "# END RUNNER MCP CI RUNNERS v1\n",
        (
            "# BEGIN RUNNER MCP CI RUNNERS v1\n"
            "# BEGIN RUNNER MCP CI RUNNERS v1\n"
            "# END RUNNER MCP CI RUNNERS v1\n"
        ),
        "* * * * * runner-mcp ci-runner run rogue\n",
    ],
)
def test_malformed_or_unmanaged_entries_fail_closed(
    tmp_path: Path,
    monkeypatch,
    value: str,
) -> None:
    executable, config = prepare(tmp_path)
    _state, runner = fake_crontab(monkeypatch, value)

    with pytest.raises(CIRunnerCronError):
        install_ci_runner_cron(
            executable=executable,
            config_dir=config,
            specs=specs(tmp_path),
            runner=runner,
        )
