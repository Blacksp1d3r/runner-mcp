from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from .config import ProjectRegistry
from .operational_safety import ActionClass, OperatorSafetyGuard
from .source_control import SourceControlError, SourceSynchronizer, clean_head
from .test_runner import TERMINAL_STATUSES, TestJobStatus, TestRunner, TestRunnerError

SELF_PROJECT = "runner-mcp"
SELF_REPOSITORY = "Blacksp1d3r/runner-mcp"
SELF_TEST_PROFILES = ("lint", "unit")
SELF_UPDATE_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_RESTART_COMPONENTS = {"github-watcher", "completion-watcher"}
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


class SelfUpdateError(RuntimeError):
    """Safe self-update failure without private path or process output."""


class SelfUpdateJobState(StrEnum):
    QUEUED = "queued"
    SYNCING = "syncing"
    TESTING = "testing"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


_TERMINAL_SELF_UPDATE_STATES = {
    SelfUpdateJobState.COMPLETED,
    SelfUpdateJobState.FAILED,
    SelfUpdateJobState.INTERRUPTED,
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass
class SelfUpdateJob:
    job_id: str
    commit: str
    state: SelfUpdateJobState
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    current_step: str | None = None
    error_category: str | None = None
    restart_required: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "commit": self.commit,
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "current_step": self.current_step,
            "error_category": self.error_category,
            "restart_required": self.restart_required,
        }


def restart_marker_path(config_dir: Path, component: str) -> Path:
    if component not in _RESTART_COMPONENTS:
        raise SelfUpdateError("Unknown self-update restart component")
    return config_dir.expanduser().resolve() / f"self-update-restart-{component}.marker"


def _write_restart_marker(config_dir: Path, component: str, commit: str) -> None:
    if not _COMMIT_RE.fullmatch(commit):
        raise SelfUpdateError("Invalid self-update commit")
    path = restart_marker_path(config_dir, component)
    if path.exists() and path.is_symlink():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(commit + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SelfUpdateError("Self-update restart marker could not be written") from exc


def _runner_console_executable() -> Path:
    candidate = Path(sys.prefix) / "bin" / "runner-mcp"
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SelfUpdateError("Runner MCP console executable is unavailable") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise SelfUpdateError("Runner MCP console executable is unavailable")
    return candidate


def reexec_component(
    config_dir: Path,
    component: str,
    *,
    server_port: int | None = None,
    exec_fn: Callable[[str, list[str]], object] = os.execv,
) -> None:
    executable = _runner_console_executable()
    config = str(config_dir.expanduser().resolve())
    argv = [str(executable), "--config-dir", config]
    if component == "server":
        if server_port is None or not 1 <= server_port <= 65_535:
            raise SelfUpdateError("Runner MCP server restart port is invalid")
        argv.extend(
            [
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                str(server_port),
            ]
        )
    elif component == "github-watcher":
        argv.extend(["github-watcher", "run"])
    elif component == "completion-watcher":
        argv.extend(["completion-watcher", "run"])
    else:
        raise SelfUpdateError("Unknown Runner MCP restart component")
    try:
        exec_fn(str(executable), argv)
    except OSError as exc:
        raise SelfUpdateError("Runner MCP component could not restart") from exc


def consume_restart_marker(config_dir: Path, component: str) -> bool:
    path = restart_marker_path(config_dir, component)
    if not path.exists():
        return False
    if path.is_symlink() or not path.is_file():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SelfUpdateError("Self-update restart marker could not be read") from exc
    commit = raw.strip()
    if not _COMMIT_RE.fullmatch(commit):
        raise SelfUpdateError("Self-update restart marker is invalid")
    try:
        path.unlink()
    except OSError as exc:
        raise SelfUpdateError("Self-update restart marker could not be consumed") from exc
    return True


class SelfUpdateManager:
    def __init__(
        self,
        *,
        config_dir: Path,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        tests: TestRunner | None,
        source: SourceSynchronizer,
        installer_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        resource_url: str,
        server_reexec: Callable[[], object] | None = None,
        restart_delay_seconds: float = 5.0,
    ) -> None:
        root = config_dir.expanduser()
        if root.exists() and root.is_symlink():
            raise SelfUpdateError("Self-update configuration directory is unsafe")
        try:
            root.mkdir(parents=True, exist_ok=True)
            os.chmod(root, 0o700)
            self.config_dir = root.resolve(strict=True)
        except OSError as exc:
            raise SelfUpdateError("Self-update configuration directory is unavailable") from exc

        jobs_root = self.config_dir / "self-update-jobs"
        if jobs_root.exists() and jobs_root.is_symlink():
            raise SelfUpdateError("Self-update job storage is unsafe")
        try:
            jobs_root.mkdir(parents=True, exist_ok=True)
            os.chmod(jobs_root, 0o700)
            self.jobs_root = jobs_root.resolve(strict=True)
        except OSError as exc:
            raise SelfUpdateError("Self-update job storage is unavailable") from exc

        if restart_delay_seconds < 1 or restart_delay_seconds > 30:
            raise SelfUpdateError("Self-update restart delay is outside the supported range")

        self.registry = registry
        self.safety = safety
        self.tests = tests
        self.source = source
        self._installer_runner = installer_runner
        self._restart_delay_seconds = restart_delay_seconds
        try:
            parsed_resource = urlsplit(resource_url)
            port = parsed_resource.port
        except ValueError as exc:
            raise SelfUpdateError("Runner MCP resource URL is invalid") from exc
        if (
            parsed_resource.scheme not in {"http", "https"}
            or parsed_resource.hostname not in _LOOPBACK_HOSTS
            or parsed_resource.path.rstrip("/") != "/mcp"
            or parsed_resource.username is not None
            or parsed_resource.password is not None
            or parsed_resource.query
            or parsed_resource.fragment
        ):
            raise SelfUpdateError("Runner MCP resource URL is not a safe loopback MCP URL")
        if port is None:
            port = 443 if parsed_resource.scheme == "https" else 80
        if not 1 <= port <= 65_535:
            raise SelfUpdateError("Runner MCP resource URL port is invalid")
        self._server_port = port
        self._server_reexec = server_reexec or (
            lambda: reexec_component(
                self.config_dir,
                "server",
                server_port=self._server_port,
            )
        )
        self._lock = threading.RLock()
        self._jobs: dict[str, SelfUpdateJob] = {}
        self._load_existing_jobs()

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.json"

    def _state_path(self) -> Path:
        return self.config_dir / "self-update-state.json"

    def _persist_job(self, job: SelfUpdateJob) -> None:
        path = self._job_path(job.job_id)
        if path.exists() and path.is_symlink():
            raise SelfUpdateError("Self-update job metadata is unsafe")
        temporary = path.with_suffix(".tmp")
        try:
            temporary.write_text(
                json.dumps(job.public_dict(), sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise SelfUpdateError("Self-update job metadata could not be persisted") from exc

    def _load_existing_jobs(self) -> None:
        for path in self.jobs_root.glob("*.json"):
            if path.is_symlink() or not path.is_file():
                continue
            job_id = path.stem
            if not SELF_UPDATE_JOB_ID_RE.fullmatch(job_id):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    continue
                job = SelfUpdateJob(
                    job_id=job_id,
                    commit=str(raw["commit"]),
                    state=SelfUpdateJobState(str(raw["state"])),
                    created_at=datetime.fromisoformat(str(raw["created_at"])).astimezone(UTC),
                    started_at=(
                        datetime.fromisoformat(str(raw["started_at"])).astimezone(UTC)
                        if raw.get("started_at")
                        else None
                    ),
                    finished_at=(
                        datetime.fromisoformat(str(raw["finished_at"])).astimezone(UTC)
                        if raw.get("finished_at")
                        else None
                    ),
                    current_step=(
                        str(raw["current_step"]) if raw.get("current_step") else None
                    ),
                    error_category=(
                        str(raw["error_category"]) if raw.get("error_category") else None
                    ),
                    restart_required=bool(raw.get("restart_required", False)),
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
            if not _COMMIT_RE.fullmatch(job.commit):
                continue
            if job.state not in _TERMINAL_SELF_UPDATE_STATES:
                job.state = SelfUpdateJobState.INTERRUPTED
                job.finished_at = _utc_now()
                job.current_step = None
                job.error_category = "runner_restart"
                job.restart_required = False
                self._persist_job(job)
            self._jobs[job_id] = job

    def _project_config(self):
        config = self.registry.projects.get(SELF_PROJECT)
        if config is None:
            raise SelfUpdateError("Runner MCP self-update project is not configured")
        if config.repository.lower() != SELF_REPOSITORY.lower():
            raise SelfUpdateError("Runner MCP self-update repository is not canonical")
        if config.environment == "production":
            raise SelfUpdateError("Runner MCP self-update is disabled for production projects")
        return config

    def _required_profiles_available(self) -> bool:
        if self.tests is None:
            return False
        try:
            names = {row["name"] for row in self.tests.list_profiles(SELF_PROJECT)}
        except (TestRunnerError, KeyError, TypeError):
            return False
        return all(name in names for name in SELF_TEST_PROFILES)

    def runtime_status(self) -> dict[str, Any]:
        try:
            package_version = version("runner-mcp")
        except PackageNotFoundError:
            package_version = "development"

        last_commit = None
        state_path = self._state_path()
        if state_path.exists():
            if state_path.is_symlink() or not state_path.is_file():
                raise SelfUpdateError("Self-update state is unsafe")
            try:
                raw = json.loads(state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SelfUpdateError("Self-update state is unavailable") from exc
            candidate = raw.get("commit") if isinstance(raw, dict) else None
            if isinstance(candidate, str) and _COMMIT_RE.fullmatch(candidate):
                last_commit = candidate

        try:
            self._project_config()
            project_ready = True
        except SelfUpdateError:
            project_ready = False

        return {
            "version": package_version,
            "self_update_ready": project_ready and self._required_profiles_available(),
            "last_installed_commit": last_commit,
            "active_update": any(
                job.state not in _TERMINAL_SELF_UPDATE_STATES
                for job in self._jobs.values()
            ),
        }

    def start(self, commit: str) -> dict[str, Any]:
        commit = commit.lower()
        if not _COMMIT_RE.fullmatch(commit):
            raise SelfUpdateError("Self-update requires a full lowercase commit ID")
        config = self._project_config()
        if not self._required_profiles_available():
            raise SelfUpdateError("Runner MCP self-update validation profiles are unavailable")
        self.safety.assert_project_action_allowed(
            ActionClass.TEST,
            environment=config.environment,
        )

        with self._lock:
            if any(
                job.state not in _TERMINAL_SELF_UPDATE_STATES
                for job in self._jobs.values()
            ):
                raise SelfUpdateError("A Runner MCP self-update is already active")
            job = SelfUpdateJob(
                job_id=uuid4().hex,
                commit=commit,
                state=SelfUpdateJobState.QUEUED,
                created_at=_utc_now(),
            )
            self._jobs[job.job_id] = job
            self._persist_job(job)

        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id,),
            name=f"runner-mcp-self-update-{job.job_id[:8]}",
            daemon=True,
        )
        worker.start()
        return job.public_dict()

    def status(self, job_id: str) -> dict[str, Any]:
        if not SELF_UPDATE_JOB_ID_RE.fullmatch(job_id):
            raise SelfUpdateError("Invalid self-update job identifier")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise SelfUpdateError("Unknown self-update job")
            return job.public_dict()

    def _set_job(
        self,
        job_id: str,
        *,
        state: SelfUpdateJobState | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        current_step: str | None = None,
        error_category: str | None = None,
        restart_required: bool | None = None,
    ) -> SelfUpdateJob:
        with self._lock:
            job = self._jobs[job_id]
            if state is not None:
                job.state = state
            if started_at is not None:
                job.started_at = started_at
            if finished_at is not None:
                job.finished_at = finished_at
            job.current_step = current_step
            job.error_category = error_category
            if restart_required is not None:
                job.restart_required = restart_required
            self._persist_job(job)
            return job

    def _wait_for_profile(self, profile: str) -> None:
        if self.tests is None:
            raise SelfUpdateError("Runner MCP test runner is unavailable")
        profiles = {
            row["name"]: row
            for row in self.tests.list_profiles(SELF_PROJECT)
        }
        metadata = profiles.get(profile)
        if metadata is None:
            raise SelfUpdateError("Required self-update test profile is unavailable")
        timeout = int(metadata["timeout_seconds"])
        started = self.tests.start_test(SELF_PROJECT, profile)
        job_id = str(started["job_id"])
        deadline = time.monotonic() + min(3_900, timeout + 300)
        while time.monotonic() < deadline:
            status = self.tests.job_status(job_id)
            state = TestJobStatus(str(status["status"]))
            if state in TERMINAL_STATUSES:
                if state != TestJobStatus.PASSED:
                    raise SelfUpdateError("Self-update validation failed")
                return
            time.sleep(0.2)
        raise SelfUpdateError("Self-update validation timed out")

    def _install_from_checked_source(self, expected_commit: str) -> None:
        config = self._project_config()
        root = config.root.resolve(strict=True)
        source_state = clean_head(root)
        if source_state["commit"] != expected_commit:
            raise SelfUpdateError("Self-update source changed after validation")

        self.safety.assert_project_action_allowed(
            ActionClass.TEST,
            environment=config.environment,
        )

        executable = Path(sys.executable)
        try:
            resolved_executable = executable.resolve(strict=True)
        except OSError as exc:
            raise SelfUpdateError("Runner MCP Python runtime is unavailable") from exc
        if (
            not executable.is_absolute()
            or not resolved_executable.is_file()
            or not os.access(resolved_executable, os.X_OK)
        ):
            raise SelfUpdateError("Runner MCP Python runtime is unavailable")
        command = [
            str(executable),
            "-m",
            "pip",
            "install",
            "--no-input",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-build-isolation",
            "--force-reinstall",
            str(root),
        ]
        environment = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "PYTHONNOUSERSITE": "1",
        }
        home = os.environ.get("HOME", "").strip()
        if home and Path(home).is_absolute():
            environment["HOME"] = home

        try:
            completed = self._installer_runner(
                command,
                cwd=str(root),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SelfUpdateError("Runner MCP self-install failed") from exc
        if completed.returncode != 0:
            raise SelfUpdateError("Runner MCP self-install failed")

    def _record_installed_commit(self, commit: str) -> None:
        path = self._state_path()
        if path.exists() and path.is_symlink():
            raise SelfUpdateError("Self-update state is unsafe")
        temporary = path.with_suffix(".tmp")
        payload = {
            "commit": commit,
            "installed_at": _iso(_utc_now()),
        }
        try:
            temporary.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise SelfUpdateError("Self-update state could not be persisted") from exc

    def _schedule_server_restart(self) -> None:
        def restart() -> None:
            time.sleep(self._restart_delay_seconds)
            self._server_reexec()

        threading.Thread(
            target=restart,
            name="runner-mcp-self-restart",
            daemon=True,
        ).start()

    def _run_job(self, job_id: str) -> None:
        job = self._jobs[job_id]
        try:
            self._set_job(
                job_id,
                state=SelfUpdateJobState.SYNCING,
                started_at=_utc_now(),
                current_step="sync",
            )
            self.source.sync_project_main_commit(SELF_PROJECT, job.commit)

            self._set_job(
                job_id,
                state=SelfUpdateJobState.TESTING,
                current_step="lint",
            )
            self._wait_for_profile("lint")
            self._set_job(
                job_id,
                state=SelfUpdateJobState.TESTING,
                current_step="unit",
            )
            self._wait_for_profile("unit")

            self._set_job(
                job_id,
                state=SelfUpdateJobState.INSTALLING,
                current_step="install",
            )
            self._install_from_checked_source(job.commit)
            self._record_installed_commit(job.commit)
            _write_restart_marker(self.config_dir, "github-watcher", job.commit)
            _write_restart_marker(self.config_dir, "completion-watcher", job.commit)
            self._set_job(
                job_id,
                state=SelfUpdateJobState.COMPLETED,
                finished_at=_utc_now(),
                current_step=None,
                restart_required=True,
            )
            self._schedule_server_restart()
        except (
            SelfUpdateError,
            SourceControlError,
            TestRunnerError,
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
            OSError,
        ):
            self._set_job(
                job_id,
                state=SelfUpdateJobState.FAILED,
                finished_at=_utc_now(),
                current_step=None,
                error_category="self_update_failed",
                restart_required=False,
            )
