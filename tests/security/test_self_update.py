import subprocess
import time
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.self_update import (
    SelfUpdateError,
    SelfUpdateJobState,
    SelfUpdateManager,
    consume_restart_marker,
    restart_marker_path,
)


class FakeSource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def sync_project_main_commit(self, project: str, commit: str):
        self.calls.append((project, commit))
        return {"project": project, "commit": commit, "changed": True}


class FakeTests:
    def __init__(self, *, fail_profile: str | None = None) -> None:
        self.fail_profile = fail_profile
        self.started: list[str] = []
        self.jobs: dict[str, str] = {}

    def list_profiles(self, project: str):
        assert project == "runner-mcp"
        return [
            {"name": "lint", "timeout_seconds": 120},
            {"name": "unit", "timeout_seconds": 300},
        ]

    def start_test(self, project: str, suite: str):
        assert project == "runner-mcp"
        self.started.append(suite)
        job_id = ("a" if suite == "lint" else "b") * 32
        self.jobs[job_id] = suite
        return {"job_id": job_id, "status": "queued"}

    def job_status(self, job_id: str):
        suite = self.jobs[job_id]
        return {
            "job_id": job_id,
            "status": "failed" if suite == self.fail_profile else "passed",
        }


def make_registry(root: Path, *, repository: str = "Blacksp1d3r/runner-mcp"):
    root.mkdir(parents=True, exist_ok=True)
    return ProjectRegistry(
        projects={
            "runner-mcp": ProjectConfig(
                display_name="Runner MCP",
                repository=repository,
                environment="staging",
                root=root,
            )
        }
    )


def make_manager(
    tmp_path: Path,
    *,
    repository: str = "Blacksp1d3r/runner-mcp",
    tests=None,
    source=None,
    installer_runner=subprocess.run,
):
    project = tmp_path / "project"
    registry = make_registry(project, repository=repository)
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    exits: list[int] = []
    manager = SelfUpdateManager(
        config_dir=tmp_path / "config",
        registry=registry,
        safety=guard,
        tests=tests or FakeTests(),
        source=source or FakeSource(),
        installer_runner=installer_runner,
        resource_url="http://127.0.0.1:8000/mcp",
        server_reexec=lambda: exits.append(75),
        restart_delay_seconds=1,
    )
    return manager, project, exits


def wait_terminal(manager: SelfUpdateManager, job_id: str) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        result = manager.status(job_id)
        if result["state"] in {"completed", "failed", "interrupted"}:
            return result
        time.sleep(0.01)
    raise AssertionError("self-update job did not terminate")


def test_self_update_rejects_noncanonical_repository(tmp_path: Path) -> None:
    manager, _root, _exits = make_manager(
        tmp_path,
        repository="example/runner-mcp",
    )
    with pytest.raises(SelfUpdateError, match="canonical"):
        manager.start("a" * 40)


def test_self_update_rejects_non_commit_and_concurrent_job(tmp_path: Path) -> None:
    manager, _root, _exits = make_manager(tmp_path)
    with pytest.raises(SelfUpdateError, match="full lowercase commit"):
        manager.start("main")
    with pytest.raises(SelfUpdateError, match="full lowercase commit"):
        manager.start("A" * 40)

    with manager._lock:
        from runner_mcp.self_update import SelfUpdateJob, _utc_now
        job = SelfUpdateJob(
            job_id="c" * 32,
            commit="a" * 40,
            state=SelfUpdateJobState.TESTING,
            created_at=_utc_now(),
        )
        manager._jobs[job.job_id] = job
    with pytest.raises(SelfUpdateError, match="already active"):
        manager.start("a" * 40)


def test_self_update_failure_stops_before_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installs: list[list[str]] = []

    def installer(command, **kwargs):
        installs.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    tests = FakeTests(fail_profile="lint")
    manager, _root, _exits = make_manager(
        tmp_path,
        tests=tests,
        installer_runner=installer,
    )
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda root: {"commit": "a" * 40, "clean": True},
    )

    started = manager.start("a" * 40)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "failed"
    assert result["error_category"] == "self_update_failed"
    assert tests.started == ["lint"]
    assert installs == []
    assert not restart_marker_path(manager.config_dir, "github-watcher").exists()


def test_successful_self_update_uses_fixed_installer_and_restart_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installs: list[tuple[list[str], dict]] = []

    def installer(command, **kwargs):
        installs.append((list(command), dict(kwargs)))
        return subprocess.CompletedProcess(command, 0, "", "")

    source = FakeSource()
    tests = FakeTests()
    manager, root, _exits = make_manager(
        tmp_path,
        tests=tests,
        source=source,
        installer_runner=installer,
    )
    commit = "d" * 40
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda project_root: {"commit": commit, "clean": True},
    )

    started = manager.start(commit)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "completed"
    assert result["restart_required"] is True
    assert source.calls == [("runner-mcp", commit)]
    assert tests.started == ["lint", "unit"]
    assert len(installs) == 1

    command, kwargs = installs[0]
    assert command[1:] == [
        "-m",
        "pip",
        "install",
        "--no-input",
        "--disable-pip-version-check",
        "--no-deps",
        "--no-build-isolation",
        "--force-reinstall",
        str(root.resolve()),
    ]
    assert Path(command[0]).is_absolute()
    assert kwargs["shell"] is False if "shell" in kwargs else True
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["timeout"] == 300
    assert kwargs["check"] is False
    assert kwargs["env"]["PIP_NO_INPUT"] == "1"
    assert "PIP_INDEX_URL" not in kwargs["env"]

    for component in ("github-watcher", "completion-watcher"):
        marker = restart_marker_path(manager.config_dir, component)
        assert marker.exists()
        assert oct(marker.stat().st_mode & 0o777) == "0o600"
        assert consume_restart_marker(manager.config_dir, component) is True
        assert not marker.exists()

    status = manager.runtime_status()
    assert status["last_installed_commit"] == commit
    assert status["self_update_ready"] is True


def test_restart_marker_rejects_symlink(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    target = tmp_path / "target"
    target.write_text("a" * 40 + "\n", encoding="utf-8")
    marker = restart_marker_path(config, "github-watcher")
    marker.symlink_to(target)

    with pytest.raises(SelfUpdateError, match="unsafe"):
        consume_restart_marker(config, "github-watcher")


def test_self_update_requires_safe_loopback_resource(tmp_path: Path) -> None:
    project = tmp_path / "project-loopback"
    registry = make_registry(project)
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "stop-loopback",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    manager = SelfUpdateManager(
        config_dir=tmp_path / "config-loopback",
        registry=registry,
        safety=guard,
        tests=FakeTests(),
        source=FakeSource(),
        resource_url="https://example.invalid/mcp",
    )

    assert manager.runtime_status()["self_update_ready"] is False
    with pytest.raises(SelfUpdateError, match="loopback restart runtime"):
        manager.start("a" * 40)
