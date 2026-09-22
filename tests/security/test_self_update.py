import subprocess
import threading
import time
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.self_update import (
    SelfUpdateError,
    SelfUpdateJobState,
    SelfUpdateManager,
    _write_restart_marker,
    _write_restart_markers,
    consume_restart_marker,
    restart_marker_commit,
    restart_marker_path,
    restart_pending_count,
    run_restart_if_requested,
)


class TrackingRLock:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.depth = 0

    def __enter__(self):
        self._lock.acquire()
        self.depth += 1
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.depth -= 1
        self._lock.release()


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
        self.source_lock = TrackingRLock()

    def list_profiles(self, project: str):
        assert project == "runner-mcp"
        return [
            {"name": "lint", "timeout_seconds": 120},
            {"name": "unit", "timeout_seconds": 300},
        ]

    def project_source_guard(self, project: str):
        assert project == "runner-mcp"
        return self.source_lock

    def start_test(self, project: str, suite: str):
        assert project == "runner-mcp"
        assert self.source_lock.depth > 0
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


def stage_fake_wheel(command: list[str]) -> None:
    wheel_dir = Path(command[command.index("--wheel-dir") + 1])
    wheel_dir.mkdir(parents=True, exist_ok=True)
    (wheel_dir / "runner_mcp-0.1.0-py3-none-any.whl").write_bytes(b"synthetic wheel")


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

    source = FakeSource()
    tests = FakeTests()

    def installer(command, **kwargs):
        assert tests.source_lock.depth > 0
        installs.append((list(command), dict(kwargs)))
        if len(command) > 3 and command[3] == "wheel":
            stage_fake_wheel(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")
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
    record_installed = manager._record_installed_commit

    def guarded_record_installed(value: str) -> None:
        assert tests.source_lock.depth > 0
        record_installed(value)

    def guarded_restart_markers(config_dir: Path, value: str) -> None:
        assert tests.source_lock.depth > 0
        _write_restart_markers(config_dir, value)

    monkeypatch.setattr(manager, "_record_installed_commit", guarded_record_installed)
    monkeypatch.setattr(
        "runner_mcp.self_update._write_restart_markers",
        guarded_restart_markers,
    )

    started = manager.start(commit)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "completed"
    assert result["restart_required"] is True
    assert source.calls == [("runner-mcp", commit)]
    assert tests.started == ["lint", "unit"]
    assert len(installs) == 3

    wheel_command, wheel_kwargs = installs[0]
    assert wheel_command[1:4] == ["-m", "pip", "wheel"]
    assert "--no-deps" in wheel_command
    assert "--no-build-isolation" in wheel_command
    assert str(root.resolve()) == wheel_command[-1]
    assert wheel_kwargs["shell"] is False
    assert wheel_kwargs["stdin"] is subprocess.DEVNULL
    assert wheel_kwargs["timeout"] == 300
    assert wheel_kwargs["env"]["PIP_NO_INDEX"] == "1"

    install_command, install_kwargs = installs[1]
    assert install_command[1:4] == ["-m", "pip", "install"]
    assert "--no-index" in install_command
    assert "--no-deps" in install_command
    assert "--force-reinstall" in install_command
    assert install_command[-1].endswith(".whl")
    assert Path(install_command[0]).is_absolute()
    assert install_kwargs["shell"] is False
    assert install_kwargs["stdin"] is subprocess.DEVNULL
    assert install_kwargs["timeout"] == 300
    assert install_kwargs["check"] is False
    assert install_kwargs["env"]["PIP_NO_INPUT"] == "1"
    assert install_kwargs["env"]["PIP_NO_INDEX"] == "1"
    assert "PIP_INDEX_URL" not in install_kwargs["env"]

    verify_command, verify_kwargs = installs[2]
    assert verify_command[1] == "-c"
    assert "runner_mcp.self_update" in verify_command[2]
    assert verify_kwargs["shell"] is False
    assert verify_kwargs["timeout"] == 60

    status = manager.runtime_status()
    assert status["last_installed_commit"] == commit
    assert status["self_update_ready"] is False
    assert status["restart_pending"] is True
    assert status["pending_restart_count"] == 3

    for component in ("server", "github-watcher", "completion-watcher"):
        marker = restart_marker_path(manager.config_dir, component)
        assert marker.exists()
        assert oct(marker.stat().st_mode & 0o777) == "0o600"
        assert restart_marker_commit(manager.config_dir, component) == commit
        assert consume_restart_marker(manager.config_dir, component) is True
        assert not marker.exists()

    status = manager.runtime_status()
    assert status["restart_pending"] is False
    assert status["pending_restart_count"] == 0
    assert status["self_update_ready"] is True



def test_same_installed_commit_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installs: list[list[str]] = []
    source = FakeSource()

    def installer(command, **kwargs):
        installs.append(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    manager, _root, exits = make_manager(
        tmp_path,
        source=source,
        installer_runner=installer,
    )
    commit = "1" * 40
    manager._record_installed_commit(commit)
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda root: {"commit": commit, "clean": True},
    )

    started = manager.start(commit)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "completed"
    assert result["restart_required"] is False
    assert source.calls == [("runner-mcp", commit)]
    assert installs == []
    assert exits == []
    assert manager.runtime_status()["install_recovery_pending"] is False


def test_failed_target_install_rolls_back_known_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = "2" * 40
    target = "3" * 40
    current = {"commit": baseline}

    class StatefulSource(FakeSource):
        def sync_project_main_commit(self, project: str, commit: str):
            result = super().sync_project_main_commit(project, commit)
            current["commit"] = commit
            return result

    source = StatefulSource()
    installs: list[list[str]] = []

    def installer(command, **kwargs):
        command = list(command)
        installs.append(command)
        if len(command) > 3 and command[3] == "wheel":
            stage_fake_wheel(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        if len(command) > 3 and command[3] == "install" and "/target/" in command[-1]:
            return subprocess.CompletedProcess(command, 1, "", "synthetic failure")
        return subprocess.CompletedProcess(command, 0, "", "")

    manager, _root, _exits = make_manager(
        tmp_path,
        source=source,
        installer_runner=installer,
    )
    manager._record_installed_commit(baseline)
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda root: {"commit": current["commit"], "clean": True},
    )

    started = manager.start(target)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "failed"
    assert result["error_category"] == "install_rolled_back"
    assert result["restart_required"] is False
    assert source.calls == [("runner-mcp", target), ("runner-mcp", baseline)]
    assert current["commit"] == baseline
    assert [
        command[3] if len(command) > 3 else command[1]
        for command in installs
    ] == [
        "wheel",
        "wheel",
        "install",
        "install",
        "-c",
    ]
    status = manager.runtime_status()
    assert status["last_installed_commit"] == baseline
    assert status["install_recovery_pending"] is False
    assert status["self_update_ready"] is True


def test_failed_first_install_requires_explicit_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = "4" * 40
    current = {"commit": "5" * 40}

    class StatefulSource(FakeSource):
        def sync_project_main_commit(self, project: str, commit: str):
            result = super().sync_project_main_commit(project, commit)
            current["commit"] = commit
            return result

    source = StatefulSource()

    def installer(command, **kwargs):
        command = list(command)
        if len(command) > 3 and command[3] == "wheel":
            stage_fake_wheel(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 1, "", "synthetic failure")

    manager, _root, _exits = make_manager(
        tmp_path,
        source=source,
        installer_runner=installer,
    )
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda root: {"commit": current["commit"], "clean": True},
    )

    started = manager.start(target)
    result = wait_terminal(manager, started["job_id"])

    assert result["state"] == "failed"
    assert result["error_category"] == "install_recovery_required"
    assert result["restart_required"] is False
    status = manager.runtime_status()
    assert status["install_recovery_pending"] is True
    assert status["self_update_ready"] is False
    with pytest.raises(SelfUpdateError, match="recovery is still pending"):
        manager.start("6" * 40)


def test_restart_failure_restores_pending_marker(tmp_path: Path) -> None:
    config = tmp_path / "config-restart"
    config.mkdir()
    commit = "e" * 40
    _write_restart_marker(config, "github-watcher", commit)

    def fail_restart() -> None:
        raise OSError("synthetic exec failure")

    with pytest.raises(SelfUpdateError, match="could not restart"):
        run_restart_if_requested(config, "github-watcher", fail_restart)

    assert restart_marker_commit(config, "github-watcher") == commit
    assert restart_pending_count(config) == 1


def test_restart_marker_batch_rolls_back_partial_write(tmp_path: Path) -> None:
    config = tmp_path / "config-batch"
    config.mkdir()
    unsafe = restart_marker_path(config, "github-watcher")
    unsafe.symlink_to(tmp_path / "missing-target")

    with pytest.raises(SelfUpdateError, match="unsafe"):
        _write_restart_markers(config, "f" * 40)

    assert not restart_marker_path(config, "completion-watcher").exists()
    assert not restart_marker_path(config, "server").exists()


def test_invalid_installed_state_fails_closed(tmp_path: Path) -> None:
    manager, _root, _exits = make_manager(tmp_path)
    state = manager._state_path()
    state.write_text('{"commit":"not-a-commit"}', encoding="utf-8")

    with pytest.raises(SelfUpdateError, match="state is invalid"):
        manager.runtime_status()


def test_pending_activation_blocks_next_self_update(tmp_path: Path) -> None:
    manager, _root, _exits = make_manager(tmp_path)
    _write_restart_marker(manager.config_dir, "server", "a" * 40)

    with pytest.raises(SelfUpdateError, match="activation is still pending"):
        manager.start("b" * 40)


def test_post_install_activation_failure_is_distinguished(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installs: list[list[str]] = []

    def installer(command, **kwargs):
        installs.append(list(command))
        if len(command) > 3 and command[3] == "wheel":
            stage_fake_wheel(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    manager, _root, _exits = make_manager(
        tmp_path,
        installer_runner=installer,
    )
    commit = "c" * 40
    monkeypatch.setattr(
        "runner_mcp.self_update.clean_head",
        lambda root: {"commit": commit, "clean": True},
    )
    monkeypatch.setattr(
        "runner_mcp.self_update._write_restart_markers",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            SelfUpdateError("synthetic activation failure")
        ),
    )

    started = manager.start(commit)
    result = wait_terminal(manager, started["job_id"])

    assert installs
    assert result["state"] == "failed"
    assert result["error_category"] == "activation_failed"
    assert result["restart_required"] is True


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
