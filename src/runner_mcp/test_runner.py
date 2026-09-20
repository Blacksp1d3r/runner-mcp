from __future__ import annotations

import codecs
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

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
        poll_interval_seconds: float = 0.1,
        terminate_grace_seconds: float = 2.0,
    ) -> None:
        if not jobs_root.is_absolute():
            raise TestRunnerError("Test jobs root must be absolute")
        if max_concurrent_jobs < 1 or max_concurrent_jobs > 16:
            raise TestRunnerError("max_concurrent_jobs must be between 1 and 16")

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
        self.poll_interval_seconds = poll_interval_seconds
        self.terminate_grace_seconds = terminate_grace_seconds

        self._lock = threading.RLock()
        self._jobs: dict[str, TestJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._load_existing_metadata()

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

            if job.status in {TestJobStatus.QUEUED, TestJobStatus.RUNNING}:
                job.status = TestJobStatus.INTERRUPTED
                job.finished_at = utc_now()
                job.error_category = "runner_restart"
                self._persist(job)
            self._jobs[job_id] = job

    def list_profiles(self, project: str) -> list[dict[str, Any]]:
        config = self.registry.projects.get(project)
        if config is None:
            raise TestRunnerError("Unknown or disabled project")

        return [
            {
                "name": name,
                "timeout_seconds": profile.timeout_seconds,
                "max_log_bytes": profile.max_log_bytes,
            }
            for name, profile in sorted(config.test_profiles.items())
        ]

    def _lookup_profile(self, project: str, suite: str) -> tuple[Path, TestProfile]:
        config = self.registry.projects.get(project)
        if config is None:
            raise TestRunnerError("Unknown or disabled project")
        profile = config.test_profiles.get(suite)
        if profile is None:
            raise TestRunnerError("Unknown or disabled test profile")

        try:
            root = config.root.resolve(strict=True)
        except OSError as exc:
            raise TestRunnerError("Project root is unavailable") from exc
        if not root.is_dir():
            raise TestRunnerError("Project root is unavailable")
        return root, profile

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

    def _active_job_count(self) -> int:
        return sum(
            job.status in {TestJobStatus.QUEUED, TestJobStatus.RUNNING}
            for job in self._jobs.values()
        )

    def _project_has_active_job(self, project: str) -> bool:
        return any(
            job.project == project
            and job.status in {TestJobStatus.QUEUED, TestJobStatus.RUNNING}
            for job in self._jobs.values()
        )

    def start_test(self, project: str, suite: str) -> dict[str, Any]:
        project_config = self.registry.projects.get(project)
        if project_config is None:
            raise TestRunnerError("Unknown or disabled project")
        self.safety.assert_project_action_allowed(
            ActionClass.TEST,
            environment=project_config.environment,
        )
        self._lookup_profile(project, suite)

        with self._lock:
            if self._project_has_active_job(project):
                raise TestRunnerError("A test job is already active for this project")
            if self._active_job_count() >= self.max_concurrent_jobs:
                raise TestRunnerError("Maximum concurrent test jobs reached")

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

        worker = threading.Thread(
            target=self._run_job,
            args=(job_id,),
            name=f"runner-mcp-test-{job_id[:8]}",
            daemon=True,
        )
        worker.start()
        return job.public_dict()

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

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TestRunnerError("Unknown test job")
            return job.public_dict()

    def cancel(self, job_id: str) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.CANCEL)
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TestRunnerError("Unknown test job")
            event = self._cancel_events.get(job_id)
            if job.status in TERMINAL_STATUSES or event is None:
                return job.public_dict()
            event.set()
            return job.public_dict()

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

    def _build_environment(
        self,
        *,
        profile: TestProfile,
        work_dir: Path,
    ) -> tuple[dict[str, str], list[str]]:
        home = work_dir / "home"
        temp = work_dir / "tmp"
        home.mkdir(parents=True, exist_ok=True)
        temp.mkdir(parents=True, exist_ok=True)
        os.chmod(home, 0o700)
        os.chmod(temp, 0o700)

        env = {
            "HOME": str(home),
            "TMPDIR": str(temp),
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
        work_dir = self._job_directory(job_id)
        log_path = self._log_path(job_id)
        cancel_event = self._cancel_events[job_id]

        try:
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
            env, secret_values = self._build_environment(
                profile=profile,
                work_dir=work_dir,
            )
            private_paths = [
                str(root),
                str(cwd),
                str(work_dir),
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
