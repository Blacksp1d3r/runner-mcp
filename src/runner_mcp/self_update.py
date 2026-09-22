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
from .self_update_install import PackageInstallError, SelfUpdatePackageInstaller
from .source_control import SourceControlError, SourceSynchronizer, clean_head
from .test_runner import TERMINAL_STATUSES, TestJobStatus, TestRunner, TestRunnerError

SELF_PROJECT = "runner-mcp"
SELF_REPOSITORY = "Blacksp1d3r/runner-mcp"
SELF_TEST_PROFILES = ("lint", "unit")
SELF_UPDATE_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_RESTART_COMPONENTS = {"server", "github-watcher", "completion-watcher"}
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


def restart_marker_commit(config_dir: Path, component: str) -> str | None:
    path = restart_marker_path(config_dir, component)
    if path.is_symlink():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    if not path.exists():
        return None
    if not path.is_file():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SelfUpdateError("Self-update restart marker could not be read") from exc
    commit = raw.strip()
    if not _COMMIT_RE.fullmatch(commit):
        raise SelfUpdateError("Self-update restart marker is invalid")
    return commit


def restart_pending_count(config_dir: Path) -> int:
    return sum(
        restart_marker_commit(config_dir, component) is not None
        for component in _RESTART_COMPONENTS
    )


def _write_restart_marker(config_dir: Path, component: str, commit: str) -> None:
    if not _COMMIT_RE.fullmatch(commit):
        raise SelfUpdateError("Invalid self-update commit")
    path = restart_marker_path(config_dir, component)
    if path.is_symlink():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    if path.exists():
        if not path.is_file():
            raise SelfUpdateError("Self-update restart marker is unsafe")
        raise SelfUpdateError("Self-update restart is already pending")
    temporary = path.with_suffix(".tmp")
    if temporary.is_symlink():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    if temporary.exists():
        if not temporary.is_file():
            raise SelfUpdateError("Self-update restart marker is unsafe")
        raise SelfUpdateError("Self-update restart staging file already exists")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(commit + "\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SelfUpdateError("Self-update restart marker could not be written") from exc


def _remove_restart_marker(config_dir: Path, component: str) -> None:
    path = restart_marker_path(config_dir, component)
    if path.is_symlink():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    if not path.exists():
        return
    if not path.is_file():
        raise SelfUpdateError("Self-update restart marker is unsafe")
    try:
        path.unlink()
    except OSError as exc:
        raise SelfUpdateError("Self-update restart marker could not be consumed") from exc


def consume_restart_marker(config_dir: Path, component: str) -> bool:
    commit = restart_marker_commit(config_dir, component)
    if commit is None:
        return False
    _remove_restart_marker(config_dir, component)
    return True


def run_restart_if_requested(
    config_dir: Path,
    component: str,
    restart_fn: Callable[[], object],
) -> bool:
    commit = restart_marker_commit(config_dir, component)
    if commit is None:
        return False
    _remove_restart_marker(config_dir, component)
    try:
        restart_fn()
    except Exception as exc:
        try:
            _write_restart_marker(config_dir, component, commit)
        except SelfUpdateError as restore_exc:
            raise SelfUpdateError(
                "Runner MCP restart failed and restart state could not be restored"
            ) from restore_exc
        raise SelfUpdateError("Runner MCP component could not restart") from exc
    return True


def _write_restart_markers(config_dir: Path, commit: str) -> None:
    written: list[str] = []
    try:
        for component in sorted(_RESTART_COMPONENTS):
            _write_restart_marker(config_dir, component, commit)
            written.append(component)
    except SelfUpdateError:
        for component in reversed(written):
            try:
                _remove_restart_marker(config_dir, component)
            except SelfUpdateError:
                pass
        raise

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
        try:
            self._package_installer = SelfUpdatePackageInstaller(
                config_dir=self.config_dir,
                python_executable=Path(sys.executable),
                runner=installer_runner,
            )
        except PackageInstallError as exc:
            raise SelfUpdateError("Self-update package installer is unavailable") from exc
        self._restart_delay_seconds = restart_delay_seconds
        self._server_port: int | None = None
        try:
            parsed_resource = urlsplit(resource_url)
            port = parsed_resource.port
        except ValueError:
            parsed_resource = None
            port = None
        if (
            parsed_resource is not None
            and parsed_resource.scheme in {"http", "https"}
            and parsed_resource.hostname in _LOOPBACK_HOSTS
            and parsed_resource.path.rstrip("/") == "/mcp"
            and parsed_resource.username is None
            and parsed_resource.password is None
            and not parsed_resource.query
            and not parsed_resource.fragment
        ):
            if port is None:
                port = 443 if parsed_resource.scheme == "https" else 80
            if 1 <= port <= 65_535:
                self._server_port = port
        self._server_reexec = server_reexec
        self._lock = threading.RLock()
        self._jobs: dict[str, SelfUpdateJob] = {}
        self._load_existing_jobs()

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.json"

    def _state_path(self) -> Path:
        return self.config_dir / "self-update-state.json"

    def _installed_commit(self) -> str | None:
        path = self._state_path()
        if path.is_symlink():
            raise SelfUpdateError("Self-update state is unsafe")
        if not path.exists():
            return None
        if not path.is_file():
            raise SelfUpdateError("Self-update state is unsafe")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SelfUpdateError("Self-update state is unavailable") from exc
        candidate = raw.get("commit") if isinstance(raw, dict) else None
        if not isinstance(candidate, str) or not _COMMIT_RE.fullmatch(candidate):
            raise SelfUpdateError("Self-update state is invalid")
        return candidate

    def _pending_install_transaction(self) -> dict[str, Any] | None:
        try:
            return self._package_installer.pending_transaction()
        except PackageInstallError as exc:
            raise SelfUpdateError("Self-update install recovery state is unsafe") from exc

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
        transaction = self._pending_install_transaction()
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
                job.error_category = (
                    "install_recovery_required"
                    if transaction is not None and transaction["job_id"] == job_id
                    else "runner_restart"
                )
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

    def _restart_ready(self) -> bool:
        return self._server_reexec is not None or self._server_port is not None

    def runtime_status(self) -> dict[str, Any]:
        try:
            package_version = version("runner-mcp")
        except PackageNotFoundError:
            package_version = "development"

        last_commit = self._installed_commit()
        recovery_pending = self._pending_install_transaction() is not None

        try:
            self._project_config()
            project_ready = True
        except SelfUpdateError:
            project_ready = False
        pending_restarts = restart_pending_count(self.config_dir)

        return {
            "version": package_version,
            "self_update_ready": (
                project_ready
                and self._required_profiles_available()
                and self._restart_ready()
                and pending_restarts == 0
                and not recovery_pending
            ),
            "last_installed_commit": last_commit,
            "active_update": any(
                job.state not in _TERMINAL_SELF_UPDATE_STATES
                for job in self._jobs.values()
            ),
            "restart_pending": pending_restarts > 0,
            "pending_restart_count": pending_restarts,
            "install_recovery_pending": recovery_pending,
        }

    def start(self, commit: str) -> dict[str, Any]:
        if not _COMMIT_RE.fullmatch(commit):
            raise SelfUpdateError("Self-update requires a full lowercase commit ID")
        config = self._project_config()
        if not self._required_profiles_available():
            raise SelfUpdateError("Runner MCP self-update validation profiles are unavailable")
        if not self._restart_ready():
            raise SelfUpdateError(
                "Runner MCP self-update requires a safe loopback restart runtime"
            )
        self.safety.assert_project_action_allowed(
            ActionClass.TEST,
            environment=config.environment,
        )
        if restart_pending_count(self.config_dir):
            raise SelfUpdateError(
                "Runner MCP self-update activation is still pending"
            )
        if self._pending_install_transaction() is not None:
            raise SelfUpdateError(
                "Runner MCP self-update installation recovery is still pending"
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

    def _cleanup_install_artifacts(self, job_id: str) -> None:
        try:
            self._package_installer.cleanup_job(job_id)
        except PackageInstallError:
            pass

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
        def restart_component() -> object:
            if self._server_reexec is not None:
                return self._server_reexec()
            if self._server_port is None:
                raise SelfUpdateError("Runner MCP server restart is unavailable")
            return reexec_component(
                self.config_dir,
                "server",
                server_port=self._server_port,
            )

        def restart() -> None:
            time.sleep(self._restart_delay_seconds)
            for retry_delay in (0.0, 2.0, 5.0):
                if retry_delay:
                    time.sleep(retry_delay)
                try:
                    requested = run_restart_if_requested(
                        self.config_dir,
                        "server",
                        restart_component,
                    )
                except SelfUpdateError:
                    continue
                if not requested:
                    return
                return

        threading.Thread(
            target=restart,
            name="runner-mcp-self-restart",
            daemon=True,
        ).start()

    def _run_job(self, job_id: str) -> None:
        job = self._jobs[job_id]
        installed = False
        failure_category = "self_update_failed"
        preserve_artifacts = False
        try:
            if self.tests is None:
                raise SelfUpdateError("Runner MCP test runner is unavailable")

            with self.tests.project_source_guard(SELF_PROJECT):
                config = self._project_config()
                root = config.root.resolve(strict=True)
                source_state = clean_head(root)
                current_commit = source_state["commit"]
                if not isinstance(current_commit, str):
                    raise SelfUpdateError("Self-update source state is invalid")
                baseline_commit = self._installed_commit()
                if baseline_commit is not None and current_commit != baseline_commit:
                    raise SelfUpdateError(
                        "Self-update source does not match the installed baseline"
                    )

                self._set_job(
                    job_id,
                    state=SelfUpdateJobState.SYNCING,
                    started_at=_utc_now(),
                    current_step="noop" if baseline_commit == job.commit else "sync",
                )
                if baseline_commit == job.commit:
                    self.source.sync_project_main_commit(SELF_PROJECT, job.commit)
                    verified = clean_head(root)
                    if verified["commit"] != job.commit:
                        raise SelfUpdateError("Self-update no-op verification failed")
                    self._set_job(
                        job_id,
                        state=SelfUpdateJobState.COMPLETED,
                        finished_at=_utc_now(),
                        current_step=None,
                        restart_required=False,
                    )
                    return

                baseline_wheel: Path | None = None
                if baseline_commit is not None:
                    self._set_job(
                        job_id,
                        state=SelfUpdateJobState.SYNCING,
                        current_step="stage-baseline",
                    )
                    try:
                        baseline_wheel = self._package_installer.build_wheel(
                            source_root=root,
                            job_id=job_id,
                            label="baseline",
                        )
                    except PackageInstallError as exc:
                        raise SelfUpdateError(
                            "Self-update recovery wheel could not be staged"
                        ) from exc
                    if clean_head(root)["commit"] != baseline_commit:
                        raise SelfUpdateError(
                            "Self-update source changed while staging recovery"
                        )

                self._set_job(
                    job_id,
                    state=SelfUpdateJobState.SYNCING,
                    current_step="sync",
                )
                self.source.sync_project_main_commit(SELF_PROJECT, job.commit)
                source_state = clean_head(root)
                if source_state["commit"] != job.commit:
                    raise SelfUpdateError("Self-update source changed before validation")

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
                    current_step="stage-target",
                )
                try:
                    target_wheel = self._package_installer.build_wheel(
                        source_root=root,
                        job_id=job_id,
                        label="target",
                    )
                except PackageInstallError as exc:
                    raise SelfUpdateError(
                        "Self-update target wheel could not be staged"
                    ) from exc
                if clean_head(root)["commit"] != job.commit:
                    raise SelfUpdateError(
                        "Self-update source changed while staging target"
                    )

                self.safety.assert_project_action_allowed(
                    ActionClass.TEST,
                    environment=config.environment,
                )
                try:
                    self._package_installer.begin_transaction(
                        job_id=job_id,
                        target_commit=job.commit,
                        baseline_commit=baseline_commit,
                    )
                except PackageInstallError as exc:
                    raise SelfUpdateError(
                        "Self-update install transaction could not start"
                    ) from exc
                preserve_artifacts = True
                self._set_job(
                    job_id,
                    state=SelfUpdateJobState.INSTALLING,
                    current_step="install",
                )
                try:
                    self._package_installer.install_wheel(target_wheel)
                    installed = True
                except PackageInstallError as install_exc:
                    if baseline_commit is None or baseline_wheel is None:
                        failure_category = "install_recovery_required"
                        raise SelfUpdateError(
                            "Runner MCP self-install failed without a recovery baseline"
                        ) from install_exc

                    self._set_job(
                        job_id,
                        state=SelfUpdateJobState.INSTALLING,
                        current_step="rollback",
                    )
                    rollback_succeeded = True
                    try:
                        self._package_installer.install_wheel(baseline_wheel)
                    except PackageInstallError:
                        rollback_succeeded = False
                    try:
                        self.source.sync_project_main_commit(
                            SELF_PROJECT,
                            baseline_commit,
                        )
                        restored = clean_head(root)
                        if restored["commit"] != baseline_commit:
                            rollback_succeeded = False
                    except (SourceControlError, RuntimeError, OSError):
                        rollback_succeeded = False

                    if not rollback_succeeded:
                        failure_category = "install_recovery_required"
                        raise SelfUpdateError(
                            "Runner MCP self-install recovery is required"
                        ) from install_exc

                    try:
                        self._package_installer.clear_transaction()
                    except PackageInstallError as exc:
                        failure_category = "install_recovery_required"
                        raise SelfUpdateError(
                            "Runner MCP self-install recovery could not be finalized"
                        ) from exc
                    preserve_artifacts = False
                    failure_category = "install_rolled_back"
                    raise SelfUpdateError(
                        "Runner MCP self-install failed and was rolled back"
                    ) from install_exc

            self._record_installed_commit(job.commit)
            _write_restart_markers(self.config_dir, job.commit)
            try:
                self._package_installer.clear_transaction()
            except PackageInstallError as exc:
                raise SelfUpdateError(
                    "Self-update install transaction could not be finalized"
                ) from exc
            preserve_artifacts = False
            self._set_job(
                job_id,
                state=SelfUpdateJobState.COMPLETED,
                finished_at=_utc_now(),
                current_step=None,
                restart_required=True,
            )
            self._schedule_server_restart()
        except (
            PackageInstallError,
            SelfUpdateError,
            SourceControlError,
            TestRunnerError,
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
            OSError,
        ):
            if installed and failure_category == "self_update_failed":
                failure_category = "activation_failed"
            self._set_job(
                job_id,
                state=SelfUpdateJobState.FAILED,
                finished_at=_utc_now(),
                current_step=None,
                error_category=failure_category,
                restart_required=installed,
            )
        finally:
            if not preserve_artifacts:
                self._cleanup_install_artifacts(job_id)

