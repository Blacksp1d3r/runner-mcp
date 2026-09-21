from __future__ import annotations

import codecs
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .adapters import get_adapter
from .config import ProjectRegistry, TestProfile
from .operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    SafetyConfigurationError,
)


class TestRunnerError(RuntimeError):
    pass


class TestJobStatus(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    STOPPED = "stopped"
    CANCELLED = "cancelled"
    ERROR = "error"
    INTERRUPTED = "interrupted"


TERMINAL_STATUSES = {
    TestJobStatus.PASSED,
    TestJobStatus.FAILED,
    TestJobStatus.TIMED_OUT,
    TestJobStatus.STOPPED,
    TestJobStatus.CANCELLED,
    TestJobStatus.ERROR,
    TestJobStatus.INTERRUPTED,
}

GENERIC_SECRET_PATTERNS = (
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?im)(\b(?:password|passwd|token|secret|api[_-]?key)\b"
        r"\s*[:=]\s*)([^\s,;]{8,})"
    ),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
)

JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
SAFE_ADAPTER_TEST_PRESETS = {"pytest", "ruff"}


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass
class TestJob:
    job_id: str
    project: str
    suite: str
    status: TestJobStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    log_truncated: bool = False
    error_category: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project": self.project,
            "suite": self.suite,
            "status": self.status.value,
            "created_at": iso_or_none(self.created_at),
            "started_at": iso_or_none(self.started_at),
            "finished_at": iso_or_none(self.finished_at),
            "exit_code": self.exit_code,
            "log_truncated": self.log_truncated,
            "error_category": self.error_category,
        }

    def metadata_dict(self) -> dict[str, Any]:
        return self.public_dict()


class TestRunner:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        jobs_root: Path,
        max_concurrent_jobs: int = 2,
        max_queued_jobs: int = 64,
        poll_interval_seconds: float = 0.1,
        terminate_grace_seconds: float = 2.0,
    ) -> None:
        if not jobs_root.is_absolute():
            raise TestRunnerError("Test jobs root must be absolute")
        if max_concurrent_jobs < 1 or max_concurrent_jobs > 16:
            raise TestRunnerError("max_concurrent_jobs must be between 1 and 16")
        if max_queued_jobs < 1 or max_queued_jobs > 1024:
            raise TestRunnerError("max_queued_jobs must be between 1 and 1024")

        if jobs_root.exists() and jobs_root.is_symlink():
            raise TestRunnerError("Test jobs root must not be a symlink")
        jobs_root.mkdir(parents=True, exist_ok=True)
        os.chmod(jobs_root, 0o700)
        self.jobs_root = jobs_root.resolve(strict=True)
        if not self.jobs_root.is_dir():
            raise TestRunnerError("Test jobs root is unavailable")

        self.registry = registry
        self.safety = safety
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_queued_jobs = max_queued_jobs
        self.poll_interval_seconds = poll_interval_seconds
        self.terminate_grace_seconds = terminate_grace_seconds

        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._jobs: dict[str, TestJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._project_queues: dict[str, deque[str]] = {}
        self._project_source_locks: dict[str, threading.Lock] = {}
        self._project_round_robin: deque[str] = deque()
        self._stopping = False
        self._workers: list[threading.Thread] = []
        self._load_existing_metadata()
        for worker_index in range(self.max_concurrent_jobs):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"runner-mcp-worker-{worker_index + 1}",
                daemon=True,
            )
            self._workers.append(worker)
            worker.start()

    def _metadata_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.json"

    def _log_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.log"

    def _job_directory(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.work"

    def _persist(self, job: TestJob) -> None:
        path = self._metadata_path(job.job_id)
        temp = path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(job.metadata_dict(), sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.chmod(temp, 0o600)
        os.replace(temp, path)
        os.chmod(path, 0o600)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    def _load_existing_metadata(self) -> None:
        for path in self.jobs_root.glob("*.json"):
            job_id = path.stem
            if not JOB_ID_RE.fullmatch(job_id):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                status = TestJobStatus(raw["status"])
                job = TestJob(
                    job_id=job_id,
                    project=str(raw["project"]),
                    suite=str(raw["suite"]),
                    status=status,
                    created_at=self._parse_datetime(raw["created_at"]) or utc_now(),
                    started_at=self._parse_datetime(raw.get("started_at")),
                    finished_at=self._parse_datetime(raw.get("finished_at")),
                    exit_code=raw.get("exit_code"),
                    log_truncated=bool(raw.get("log_truncated", False)),
                    error_category=raw.get("error_category"),
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue

            if job.status in {TestJobStatus.CLAIMED, TestJobStatus.RUNNING}:
                job.status = TestJobStatus.INTERRUPTED
                job.finished_at = utc_now()
                job.error_category = "runner_restart"
                self._persist(job)
            self._jobs[job_id] = job
            if job.status == TestJobStatus.QUEUED:
                self._cancel_events[job_id] = threading.Event()
                self._enqueue_job_locked(job)

    @staticmethod
    def _detect_safe_project_executable(
        root: Path,
        names: tuple[str, ...],
    ) -> Path | None:
        for prefix in (root / ".venv" / "bin", root / "venv" / "bin"):
            for name in names:
                candidate = prefix / name
                if (
                    candidate.exists()
                    and candidate.is_file()
                    and not candidate.is_symlink()
                    and os.access(candidate, os.X_OK)
                ):
                    return candidate.resolve()
        return None

    def _adapter_profile(
        self,
        *,
        project: str,
        suite: str,
    ) -> tuple[Path, TestProfile] | None:
        config = self.registry.projects.get(project)
        if config is None:
            raise TestRunnerError("Unknown or disabled project")
        if suite not in SAFE_ADAPTER_TEST_PRESETS:
            return None

        try:
            root = config.root.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Project root is unavailable") from exc
        if not root.is_dir():
            raise TestRunnerError("Project root is unavailable")

        adapter = get_adapter(config.adapter)
        if suite not in adapter.info.test_presets:
            return None

        if suite == "pytest":
            executable = self._detect_safe_project_executable(
                root,
                ("python", "python3"),
            )
            if executable is None:
                return None
            profile = TestProfile(
                argv=[str(executable), "-m", "pytest", "-q"],
                cwd=".",
                timeout_seconds=1200,
                max_log_bytes=2_000_000,
                env_passthrough=[],
                parallel_safe=False,
            )
            return root, profile

        if suite == "ruff":
            executable = self._detect_safe_project_executable(root, ("ruff",))
            if executable is None:
                return None
            profile = TestProfile(
                argv=[str(executable), "check", "."],
                cwd=".",
                timeout_seconds=300,
                max_log_bytes=2_000_000,
                env_passthrough=[],
                parallel_safe=True,
            )
            return root, profile
        return None

    def list_profiles(self, project: str) -> list[dict[str, Any]]:
        config = self.registry.projects.get(project)
        if config is None:
            raise TestRunnerError("Unknown or disabled project")

        profiles = dict(config.test_profiles)
        for suite in sorted(SAFE_ADAPTER_TEST_PRESETS):
            if suite in profiles:
                continue
            adapter_profile = self._adapter_profile(
                project=project,
                suite=suite,
            )
            if adapter_profile is not None:
                _root, profile = adapter_profile
                profiles[suite] = profile

        return [
            {
                "name": name,
                "timeout_seconds": profile.timeout_seconds,
                "max_log_bytes": profile.max_log_bytes,
                "parallel_safe": profile.parallel_safe,
            }
            for name, profile in sorted(profiles.items())
        ]

    def _lookup_profile(self, project: str, suite: str) -> tuple[Path, TestProfile]:
        config = self.registry.projects.get(project)
        if config is None:
            raise TestRunnerError("Unknown or disabled project")
        profile = config.test_profiles.get(suite)

        try:
            root = config.root.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Project root is unavailable") from exc
        if not root.is_dir():
            raise TestRunnerError("Project root is unavailable")

        if profile is not None:
            return root, profile

        adapter_profile = self._adapter_profile(
            project=project,
            suite=suite,
        )
        if adapter_profile is not None:
            return adapter_profile

        raise TestRunnerError("Unknown or disabled test profile")

    @staticmethod
    def _safe_cwd(root: Path, relative: str) -> Path:
        current = root
        for part in Path(relative).parts:
            if part in {"", "."}:
                continue
            current = current / part
            if current.is_symlink():
                raise TestRunnerError("Test working directory must not contain symlinks")

        try:
            resolved = current.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Test working directory is unavailable") from exc
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise TestRunnerError("Test working directory escapes the project root") from exc
        if not resolved.is_dir():
            raise TestRunnerError("Test working directory is unavailable")
        return resolved

    @staticmethod
    def _resolve_executable(profile: TestProfile) -> Path:
        configured = Path(profile.argv[0])
        try:
            resolved = configured.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Configured test executable is unavailable") from exc
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise TestRunnerError("Configured test executable is not executable")
        return resolved

    def _active_jobs_locked(self, project: str | None = None) -> list[TestJob]:
        return [
            job
            for job in self._jobs.values()
            if job.status in {TestJobStatus.CLAIMED, TestJobStatus.RUNNING}
            and (project is None or job.project == project)
        ]

    def _queued_jobs_locked(self, project: str | None = None) -> list[TestJob]:
        return [
            job
            for job in self._jobs.values()
            if job.status == TestJobStatus.QUEUED
            and (project is None or job.project == project)
        ]

    def _enqueue_job_locked(self, job: TestJob) -> None:
        queue = self._project_queues.setdefault(job.project, deque())
        if not queue and job.project not in self._project_round_robin:
            self._project_round_robin.append(job.project)
        queue.append(job.job_id)

    def _profile_parallel_safe(self, job: TestJob) -> bool:
        try:
            _root, profile = self._lookup_profile(job.project, job.suite)
        except TestRunnerError:
            return False
        return profile.parallel_safe

    def project_has_work(self, project: str) -> bool:
        with self._lock:
            return bool(
                self._queued_jobs_locked(project)
                or self._active_jobs_locked(project)
            )

    def project_source_guard(self, project: str) -> threading.Lock:
        with self._lock:
            lock = self._project_source_locks.get(project)
            if lock is None:
                lock = threading.Lock()
                self._project_source_locks[project] = lock
            return lock

    def _project_can_claim_locked(self, job: TestJob) -> bool:
        project = self.registry.projects.get(job.project)
        if project is None:
            return False
        active = self._active_jobs_locked(job.project)
        if not active:
            return True
        if len(active) >= project.max_parallel_tests:
            return False
        if not self._profile_parallel_safe(job):
            return False
        return all(self._profile_parallel_safe(active_job) for active_job in active)

    def _claim_next_locked(self) -> str | None:
        projects_to_check = len(self._project_round_robin)
        for _ in range(projects_to_check):
            project = self._project_round_robin.popleft()
            queue = self._project_queues.get(project)
            if queue is None:
                continue
            while queue and self._jobs[queue[0]].status != TestJobStatus.QUEUED:
                queue.popleft()
            if not queue:
                self._project_queues.pop(project, None)
                continue

            candidate = self._jobs[queue[0]]
            if not self._project_can_claim_locked(candidate):
                self._project_round_robin.append(project)
                continue

            job_id = queue.popleft()
            if queue:
                self._project_round_robin.append(project)
            else:
                self._project_queues.pop(project, None)
            candidate.status = TestJobStatus.CLAIMED
            self._persist(candidate)
            return job_id
        return None

    def _worker_loop(self) -> None:
        while True:
            with self._condition:
                job_id = None
                while not self._stopping and job_id is None:
                    job_id = self._claim_next_locked()
                    if job_id is None:
                        self._condition.wait(timeout=0.5)
                if self._stopping:
                    return
            assert job_id is not None
            self._run_job(job_id)
            with self._condition:
                self._condition.notify_all()

    def shutdown(self, *, join_timeout_seconds: float = 2.0) -> None:
        with self._condition:
            self._stopping = True
            self._condition.notify_all()
        for worker in self._workers:
            worker.join(timeout=join_timeout_seconds)

    def start_test(self, project: str, suite: str) -> dict[str, Any]:
        source_guard = self.project_source_guard(project)
        with source_guard:
            project_config = self.registry.projects.get(project)
            if project_config is None:
                raise TestRunnerError("Unknown or disabled project")
            self.safety.assert_project_action_allowed(
                ActionClass.TEST,
                environment=project_config.environment,
            )
            self._lookup_profile(project, suite)

            with self._condition:
                if len(self._queued_jobs_locked()) >= self.max_queued_jobs:
                    raise TestRunnerError("Test queue capacity reached")
                if len(self._queued_jobs_locked(project)) >= project_config.max_queued_tests:
                    raise TestRunnerError("Project test queue capacity reached")

                job_id = uuid4().hex
                job = TestJob(
                    job_id=job_id,
                    project=project,
                    suite=suite,
                    status=TestJobStatus.QUEUED,
                    created_at=utc_now(),
                )
                self._jobs[job_id] = job
                self._cancel_events[job_id] = threading.Event()
                self._persist(job)
                self._enqueue_job_locked(job)
                self._condition.notify_all()
                return self.job_status(job_id)

    def _set_job(
        self,
        job_id: str,
        *,
        status: TestJobStatus | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        exit_code: int | None = None,
        log_truncated: bool | None = None,
        error_category: str | None = None,
    ) -> TestJob:
        with self._lock:
            job = self._jobs[job_id]
            if status is not None:
                job.status = status
            if started_at is not None:
                job.started_at = started_at
            if finished_at is not None:
                job.finished_at = finished_at
            if exit_code is not None:
                job.exit_code = exit_code
            if log_truncated is not None:
                job.log_truncated = log_truncated
            if error_category is not None:
                job.error_category = error_category
            self._persist(job)
            return job

    def _waiting_reason_locked(self, job: TestJob) -> str | None:
        if job.status != TestJobStatus.QUEUED:
            return None
        if len(self._active_jobs_locked()) >= self.max_concurrent_jobs:
            return "worker_capacity"
        project = self.registry.projects.get(job.project)
        if project is None:
            return "project_unavailable"
        active = self._active_jobs_locked(job.project)
        if len(active) >= project.max_parallel_tests:
            return "project_parallel_limit"
        if active and (
            not self._profile_parallel_safe(job)
            or not all(self._profile_parallel_safe(item) for item in active)
        ):
            return "project_exclusive_test"
        return "fair_scheduling"

    def job_status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TestRunnerError("Unknown test job")
            result = job.public_dict()
            waiting_reason = self._waiting_reason_locked(job)
            if waiting_reason is not None:
                result["waiting_reason"] = waiting_reason
            return result

    def status(self, job_id: str) -> dict[str, Any]:
        return self.job_status(job_id)

    def worker_status(self) -> dict[str, Any]:
        with self._lock:
            claimed = sum(job.status == TestJobStatus.CLAIMED for job in self._jobs.values())
            running = sum(job.status == TestJobStatus.RUNNING for job in self._jobs.values())
            active = claimed + running
            return {
                "concurrency_limit": self.max_concurrent_jobs,
                "available_workers": max(0, self.max_concurrent_jobs - active),
                "claimed_jobs": claimed,
                "running_jobs": running,
            }

    def queue_status(self) -> dict[str, Any]:
        with self._lock:
            queued = sorted(self._queued_jobs_locked(), key=lambda job: job.created_at)
            active = self._active_jobs_locked()
            projects: list[dict[str, Any]] = []
            for project_code in sorted(self.registry.projects):
                project = self.registry.projects[project_code]
                project_queued = [job for job in queued if job.project == project_code]
                project_active = [job for job in active if job.project == project_code]
                project_locked = bool(project_active) and (
                    project.max_parallel_tests == 1
                    or any(not self._profile_parallel_safe(job) for job in project_active)
                )
                projects.append(
                    {
                        "project": project_code,
                        "queued_jobs": len(project_queued),
                        "claimed_jobs": sum(
                            job.status == TestJobStatus.CLAIMED for job in project_active
                        ),
                        "running_jobs": sum(
                            job.status == TestJobStatus.RUNNING for job in project_active
                        ),
                        "max_parallel_tests": project.max_parallel_tests,
                        "project_lock_active": project_locked,
                    }
                )

            oldest = queued[0] if queued else None
            oldest_payload = None
            if oldest is not None:
                oldest_payload = {
                    "job_id": oldest.job_id,
                    "project": oldest.project,
                    "suite": oldest.suite,
                    "age_seconds": max(
                        0,
                        int((utc_now() - oldest.created_at).total_seconds()),
                    ),
                    "waiting_reason": self._waiting_reason_locked(oldest),
                }

            worker = self.worker_status()
            return {
                "queued_jobs": len(queued),
                "claimed_jobs": worker["claimed_jobs"],
                "running_jobs": worker["running_jobs"],
                "available_workers": worker["available_workers"],
                "concurrency_limit": self.max_concurrent_jobs,
                "queue_limit": self.max_queued_jobs,
                "oldest_queued_job": oldest_payload,
                "projects": projects,
            }

    def cancel(self, job_id: str) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.CANCEL)
        with self._condition:
            job = self._jobs.get(job_id)
            if job is None:
                raise TestRunnerError("Unknown test job")
            event = self._cancel_events.get(job_id)
            if job.status in TERMINAL_STATUSES or event is None:
                return self.job_status(job_id)
            event.set()
            if job.status == TestJobStatus.QUEUED:
                job.status = TestJobStatus.CANCELLED
                job.finished_at = utc_now()
                self._persist(job)
                self._condition.notify_all()
            return self.job_status(job_id)

    @staticmethod
    def _scrub_text(
        text: str,
        *,
        secret_values: list[str],
        private_paths: list[str],
    ) -> str:
        redacted = text
        for value in sorted((v for v in secret_values if len(v) >= 4), key=len, reverse=True):
            redacted = redacted.replace(value, "[REDACTED]")
        for value in sorted((v for v in private_paths if v), key=len, reverse=True):
            redacted = redacted.replace(value, "[PRIVATE_PATH]")

        for pattern in GENERIC_SECRET_PATTERNS:
            if pattern.pattern.startswith("(?i)(Bearer") or pattern.groups >= 2:
                redacted = pattern.sub(r"\1[REDACTED]", redacted)
            else:
                redacted = pattern.sub("[REDACTED]", redacted)
        return redacted

    @staticmethod
    def _short_job_tmp(job_id: str) -> Path:
        if not JOB_ID_RE.fullmatch(job_id):
            raise TestRunnerError("Invalid test job identifier")
        try:
            path = Path(
                tempfile.mkdtemp(
                    prefix=f"runner-mcp-{job_id[:8]}-",
                    dir="/tmp",
                )
            )
            os.chmod(path, 0o700)
            if path.is_symlink():
                raise TestRunnerError("Short test temporary directory is unsafe")
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Short test temporary directory is unavailable") from exc
        if not resolved.is_dir():
            raise TestRunnerError("Short test temporary directory is unsafe")
        metadata = resolved.stat()
        if metadata.st_uid != os.getuid():
            raise TestRunnerError("Short test temporary directory has unsafe ownership")
        return resolved

    def _build_environment(
        self,
        *,
        profile: TestProfile,
        work_dir: Path,
        temp_dir: Path,
    ) -> tuple[dict[str, str], list[str]]:
        home = work_dir / "home"
        home.mkdir(parents=True, exist_ok=True)
        os.chmod(home, 0o700)

        env = {
            "HOME": str(home),
            "TMPDIR": str(temp_dir),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        sensitive_values: list[str] = []
        for name in profile.env_passthrough:
            value = os.environ.get(name)
            if value is None:
                continue
            if len(value) > 32768:
                raise TestRunnerError("Passthrough environment value exceeds the safe size limit")
            env[name] = value
            sensitive_values.append(value)
            sensitive_values.extend(line for line in value.splitlines() if line)
        return env, sensitive_values

    @staticmethod
    def _terminate_process_group(
        process: subprocess.Popen[bytes],
        *,
        grace_seconds: float,
    ) -> None:
        if process.poll() is not None:
            return

        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            pass

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass

    def _write_log_chunk(
        self,
        handle,
        text: str,
        *,
        written_bytes: int,
        max_log_bytes: int,
        truncated: bool,
        secret_values: list[str],
        private_paths: list[str],
    ) -> tuple[int, bool]:
        if not text or truncated:
            return written_bytes, truncated

        scrubbed = self._scrub_text(
            text,
            secret_values=secret_values,
            private_paths=private_paths,
        )
        encoded = scrubbed.encode("utf-8", errors="replace")
        remaining = max_log_bytes - written_bytes

        if len(encoded) <= remaining:
            handle.write(encoded)
            handle.flush()
            return written_bytes + len(encoded), False

        if remaining > 0:
            handle.write(encoded[:remaining])
        marker = b"\n[LOG TRUNCATED BY RUNNER MCP]\n"
        handle.write(marker)
        handle.flush()
        return max_log_bytes, True

    def _run_job(self, job_id: str) -> None:
        process: subprocess.Popen[bytes] | None = None
        selector: selectors.BaseSelector | None = None
        short_tmp: Path | None = None
        work_dir = self._job_directory(job_id)
        log_path = self._log_path(job_id)
        cancel_event = self._cancel_events[job_id]

        try:
            if cancel_event.is_set():
                self._set_job(
                    job_id,
                    status=TestJobStatus.CANCELLED,
                    finished_at=utc_now(),
                )
                return
            with self._lock:
                job = self._jobs[job_id]
                project = job.project
                suite = job.suite

            project_config = self.registry.projects.get(job.project)
            if project_config is None:
                raise TestRunnerError("Unknown or disabled project")
            self.safety.assert_project_action_allowed(
                ActionClass.TEST,
                environment=project_config.environment,
            )
            root, profile = self._lookup_profile(project, suite)
            cwd = self._safe_cwd(root, profile.cwd)
            executable = self._resolve_executable(profile)

            work_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
            short_tmp = self._short_job_tmp(job_id)
            env, secret_values = self._build_environment(
                profile=profile,
                work_dir=work_dir,
                temp_dir=short_tmp,
            )
            private_paths = [
                str(root),
                str(cwd),
                str(work_dir),
                str(short_tmp),
                str(self.jobs_root),
                str(executable),
                str(executable.parent),
                *[
                    value
                    for value in profile.argv[1:]
                    if Path(value).is_absolute()
                ],
            ]
            carry_chars = max(
                1024,
                max(
                    (len(value) + 64 for value in [*secret_values, *private_paths] if value),
                    default=1024,
                ),
            )

            argv = [str(executable), *profile.argv[1:]]
            log_path.touch(mode=0o600, exist_ok=False)
            os.chmod(log_path, 0o600)
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                start_new_session=True,
                close_fds=True,
            )
            if process.stdout is None:
                raise TestRunnerError("Test process output pipe is unavailable")

            self._set_job(
                job_id,
                status=TestJobStatus.RUNNING,
                started_at=utc_now(),
            )

            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            decoder = codecs.getincrementaldecoder("utf-8")("replace")
            text_buffer = ""
            written_bytes = 0
            truncated = False
            started_monotonic = time.monotonic()
            forced_status: TestJobStatus | None = None

            with log_path.open("ab", buffering=0) as log_handle:
                while True:
                    for key, _ in selector.select(timeout=self.poll_interval_seconds):
                        try:
                            chunk = os.read(key.fileobj.fileno(), 4096)
                        except OSError:
                            chunk = b""
                        if not chunk:
                            try:
                                selector.unregister(key.fileobj)
                            except KeyError:
                                pass
                            continue

                        text_buffer += decoder.decode(chunk)
                        while "\n" in text_buffer:
                            line, text_buffer = text_buffer.split("\n", 1)
                            written_bytes, truncated = self._write_log_chunk(
                                log_handle,
                                line + "\n",
                                written_bytes=written_bytes,
                                max_log_bytes=profile.max_log_bytes,
                                truncated=truncated,
                                secret_values=secret_values,
                                private_paths=private_paths,
                            )

                        if len(text_buffer) > max(16384, carry_chars * 2):
                            prefix = text_buffer[:-carry_chars]
                            text_buffer = text_buffer[-carry_chars:]
                            written_bytes, truncated = self._write_log_chunk(
                                log_handle,
                                prefix,
                                written_bytes=written_bytes,
                                max_log_bytes=profile.max_log_bytes,
                                truncated=truncated,
                                secret_values=secret_values,
                                private_paths=private_paths,
                            )

                    if process.poll() is None and forced_status is None:
                        if cancel_event.is_set():
                            forced_status = TestJobStatus.CANCELLED
                        elif self.safety.status().stop_active:
                            forced_status = TestJobStatus.STOPPED
                        elif time.monotonic() - started_monotonic >= profile.timeout_seconds:
                            forced_status = TestJobStatus.TIMED_OUT

                        if forced_status is not None:
                            self._terminate_process_group(
                                process,
                                grace_seconds=self.terminate_grace_seconds,
                            )

                    if process.poll() is not None and not selector.get_map():
                        break

                text_buffer += decoder.decode(b"", final=True)
                written_bytes, truncated = self._write_log_chunk(
                    log_handle,
                    text_buffer,
                    written_bytes=written_bytes,
                    max_log_bytes=profile.max_log_bytes,
                    truncated=truncated,
                    secret_values=secret_values,
                    private_paths=private_paths,
                )

            return_code = process.wait()
            if forced_status is not None:
                final_status = forced_status
            elif return_code == 0:
                final_status = TestJobStatus.PASSED
            else:
                final_status = TestJobStatus.FAILED

            self._set_job(
                job_id,
                status=final_status,
                finished_at=utc_now(),
                exit_code=return_code,
                log_truncated=truncated,
            )

        except OperatorStopActive:
            self._set_job(
                job_id,
                status=TestJobStatus.STOPPED,
                finished_at=utc_now(),
                error_category="operator_stop",
            )
        except SafetyConfigurationError:
            self._set_job(
                job_id,
                status=TestJobStatus.ERROR,
                finished_at=utc_now(),
                error_category="safety_configuration",
            )
        except Exception:  # noqa: BLE001 - background jobs must fail closed
            if process is not None and process.poll() is None:
                self._terminate_process_group(
                    process,
                    grace_seconds=self.terminate_grace_seconds,
                )
            self._set_job(
                job_id,
                status=TestJobStatus.ERROR,
                finished_at=utc_now(),
                error_category="execution_error",
            )
        finally:
            if selector is not None:
                selector.close()
            if short_tmp is not None:
                try:
                    if short_tmp.is_symlink():
                        short_tmp.unlink()
                    elif short_tmp.exists():
                        shutil.rmtree(short_tmp)
                except OSError:
                    pass
            with self._condition:
                self._condition.notify_all()

    def get_log(
        self,
        job_id: str,
        *,
        offset: int = 0,
        length: int = 200,
    ) -> dict[str, Any]:
        if offset < 0:
            raise TestRunnerError("Offset must be zero or greater")
        if length < 1 or length > 500:
            raise TestRunnerError("Length must be between 1 and 500")

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TestRunnerError("Unknown test job")

        path = self._log_path(job_id)
        if not path.exists():
            return {
                "job_id": job_id,
                "offset": offset,
                "next_offset": None,
                "eof": job.status in TERMINAL_STATUSES,
                "line_count": 0,
                "content": "",
            }
        if path.is_symlink():
            raise TestRunnerError("Test log is unavailable")

        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise TestRunnerError("Test log is unavailable")

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        selected = lines[offset : offset + length]
        next_offset = offset + len(selected)
        eof = next_offset >= len(lines) and job.status in TERMINAL_STATUSES

        return {
            "job_id": job_id,
            "offset": offset,
            "next_offset": None if eof else next_offset,
            "eof": eof,
            "line_count": len(selected),
            "content": "".join(selected),
        }
