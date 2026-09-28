from __future__ import annotations

import json
import os
import re
import stat
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import ProjectRegistry
from .database_manager import BACKUP_ID_RE, DatabaseManager, DatabaseManagerError
from .migration_planning import migration_binding_fingerprint, migration_plan_material
from .operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    SafetyConfigurationError,
)
from .secure_io import PrivateAtomicWriteError, atomic_replace_private
from .source_control import SourceControlError

MIGRATION_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_PROJECT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_MIGRATION_JOB_METADATA_BYTES = 16_384
MAX_MIGRATION_JOB_METADATA_FILES = 10_000
_PERSISTED_KEYS = {
    "job_id",
    "project",
    "operation",
    "state",
    "created_at",
    "started_at",
    "finished_at",
    "migration_state",
    "error_category",
    "pre_migration_backup_created",
    "output_truncated",
    "expected_binding_fingerprint",
    "expected_commit",
}
_MIGRATION_STATES = {None, "applied", "failed", "timed_out"}
_ERROR_CATEGORIES = {
    None,
    "operator_stop",
    "safety_configuration",
    "plan_changed",
    "database_busy",
    "migration_failed",
    "migration_timed_out",
    "runner_restart",
    "unexpected_error",
}


class MigrationJobError(RuntimeError):
    """Bounded migration-job substrate failure."""


class MigrationJobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"
    INTERRUPTED = "interrupted"


TERMINAL_MIGRATION_JOB_STATES = {
    MigrationJobState.COMPLETED,
    MigrationJobState.STOPPED,
    MigrationJobState.ERROR,
    MigrationJobState.INTERRUPTED,
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: Any, *, optional: bool, label: str) -> datetime | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise MigrationJobError(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise MigrationJobError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        raise MigrationJobError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC)


def _validate_jobs_root(
    root: Path,
    *,
    create: bool,
) -> Path:
    if not root.is_absolute():
        raise MigrationJobError("Migration jobs root must be absolute")
    if root.exists() and root.is_symlink():
        raise MigrationJobError("Migration jobs root must not be a symlink")
    if create and not root.exists():
        try:
            root.mkdir(parents=False, mode=0o700)
        except OSError as exc:
            raise MigrationJobError("Migration jobs root is unavailable") from exc
    current = Path(root.anchor)
    try:
        for part in root.parts[1:]:
            current = current / part
            if current.is_symlink():
                raise MigrationJobError("Migration jobs root contains a symlink")
    except OSError as exc:
        raise MigrationJobError("Migration jobs root is unavailable") from exc
    try:
        resolved = root.resolve(strict=True)
        metadata = os.stat(resolved, follow_symlinks=False)
    except OSError as exc:
        raise MigrationJobError("Migration jobs root is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise MigrationJobError("Migration jobs root is unavailable")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise MigrationJobError("Migration jobs root permissions are unsafe")
    if metadata.st_uid != os.getuid():
        raise MigrationJobError("Migration jobs root ownership is unsafe")
    return resolved


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise MigrationJobError("Migration job storage could not be synchronized") from exc
    try:
        os.fsync(fd)
    except OSError as exc:
        raise MigrationJobError("Migration job storage could not be synchronized") from exc
    finally:
        os.close(fd)


def _strict_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise MigrationJobError("Migration job metadata is unsafe")
    if not hasattr(os, "O_NOFOLLOW"):
        raise MigrationJobError("Safe migration job metadata reads are unavailable")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise MigrationJobError("Migration job metadata is unavailable") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise MigrationJobError("Migration job metadata is unsafe")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise MigrationJobError("Migration job metadata permissions are unsafe")
        if metadata.st_uid != os.getuid():
            raise MigrationJobError("Migration job metadata ownership is unsafe")
        if metadata.st_size <= 0 or metadata.st_size > MAX_MIGRATION_JOB_METADATA_BYTES:
            raise MigrationJobError("Migration job metadata size is unsafe")
        remaining = metadata.st_size
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if (
            remaining
            or after.st_size != metadata.st_size
            or stat.S_IMODE(after.st_mode) != 0o600
            or after.st_uid != metadata.st_uid
        ):
            raise MigrationJobError("Migration job metadata changed while being read")
    finally:
        os.close(fd)

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise MigrationJobError("Migration job metadata contains duplicate keys")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise MigrationJobError("Migration job metadata contains non-standard JSON")

    try:
        raw = json.loads(
            b"".join(chunks).decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except MigrationJobError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise MigrationJobError("Migration job metadata is invalid") from exc
    if not isinstance(raw, dict) or set(raw) != _PERSISTED_KEYS:
        raise MigrationJobError("Migration job metadata has an unsupported shape")
    return raw


@dataclass(frozen=True)
class MigrationJob:
    job_id: str
    project: str
    state: MigrationJobState
    created_at: datetime
    expected_binding_fingerprint: str
    expected_commit: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    migration_state: str | None = None
    error_category: str | None = None
    pre_migration_backup_created: bool = False
    output_truncated: bool = False

    def persisted_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project": self.project,
            "operation": "migration",
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "migration_state": self.migration_state,
            "error_category": self.error_category,
            "pre_migration_backup_created": self.pre_migration_backup_created,
            "output_truncated": self.output_truncated,
            "expected_binding_fingerprint": self.expected_binding_fingerprint,
            "expected_commit": self.expected_commit,
        }

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project": self.project,
            "operation": "migration",
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "migration_state": self.migration_state,
            "error_category": self.error_category,
            "pre_migration_backup_created": self.pre_migration_backup_created,
            "output_truncated": self.output_truncated,
        }


def parse_migration_job_metadata(path: Path) -> MigrationJob:
    job_id = path.stem
    if not MIGRATION_JOB_ID_RE.fullmatch(job_id):
        raise MigrationJobError("Migration job metadata identity is invalid")
    raw = _strict_json(path)
    if raw["job_id"] != job_id or raw["operation"] != "migration":
        raise MigrationJobError("Migration job metadata identity is invalid")
    project = raw["project"]
    if not isinstance(project, str) or not _PROJECT_RE.fullmatch(project):
        raise MigrationJobError("Migration job project is invalid")
    try:
        state = MigrationJobState(raw["state"])
    except (TypeError, ValueError) as exc:
        raise MigrationJobError("Migration job state is invalid") from exc
    migration_state = raw["migration_state"]
    if migration_state not in _MIGRATION_STATES:
        raise MigrationJobError("Migration job result state is invalid")
    error_category = raw["error_category"]
    if error_category not in _ERROR_CATEGORIES:
        raise MigrationJobError("Migration job error category is invalid")
    if not isinstance(raw["pre_migration_backup_created"], bool):
        raise MigrationJobError("Migration job backup state is invalid")
    if not isinstance(raw["output_truncated"], bool):
        raise MigrationJobError("Migration job output state is invalid")
    fingerprint = raw["expected_binding_fingerprint"]
    commit = raw["expected_commit"]
    if not isinstance(fingerprint, str) or not _FINGERPRINT_RE.fullmatch(fingerprint):
        raise MigrationJobError("Migration job binding is invalid")
    if not isinstance(commit, str) or not _COMMIT_RE.fullmatch(commit):
        raise MigrationJobError("Migration job commit is invalid")

    created_at = _parse_datetime(raw["created_at"], optional=False, label="created_at")
    started_at = _parse_datetime(raw["started_at"], optional=True, label="started_at")
    finished_at = _parse_datetime(raw["finished_at"], optional=True, label="finished_at")
    assert created_at is not None
    if state in TERMINAL_MIGRATION_JOB_STATES and finished_at is None:
        raise MigrationJobError("Terminal migration job has no finished timestamp")
    if state in {MigrationJobState.QUEUED, MigrationJobState.RUNNING} and finished_at is not None:
        raise MigrationJobError("Active migration job has a finished timestamp")
    if state == MigrationJobState.QUEUED and started_at is not None:
        raise MigrationJobError("Queued migration job has a started timestamp")
    if state == MigrationJobState.RUNNING and started_at is None:
        raise MigrationJobError("Running migration job has no started timestamp")
    if state in {MigrationJobState.QUEUED, MigrationJobState.RUNNING} and (
        migration_state is not None
        or error_category is not None
        or raw["pre_migration_backup_created"]
        or raw["output_truncated"]
    ):
        raise MigrationJobError("Active migration job state is inconsistent")
    if (
        state == MigrationJobState.COMPLETED
        and (migration_state != "applied" or error_category is not None)
    ):
        raise MigrationJobError("Completed migration job state is inconsistent")
    if state == MigrationJobState.STOPPED and (
        error_category != "operator_stop" or migration_state is not None
    ):
        raise MigrationJobError("Stopped migration job state is inconsistent")
    if state == MigrationJobState.ERROR and error_category is None:
        raise MigrationJobError("Failed migration job has no error category")
    if migration_state in {"applied", "failed", "timed_out"} and not raw[
        "pre_migration_backup_created"
    ]:
        raise MigrationJobError("Migration job backup evidence is inconsistent")
    if migration_state == "failed" and error_category != "migration_failed":
        raise MigrationJobError("Failed migration result category is inconsistent")
    if migration_state == "timed_out" and error_category != "migration_timed_out":
        raise MigrationJobError("Timed-out migration result category is inconsistent")
    if state == MigrationJobState.INTERRUPTED and (
        error_category != "runner_restart" or migration_state is not None
    ):
        raise MigrationJobError("Interrupted migration job state is inconsistent")

    return MigrationJob(
        job_id=job_id,
        project=project,
        state=state,
        created_at=created_at,
        expected_binding_fingerprint=fingerprint,
        expected_commit=commit,
        started_at=started_at,
        finished_at=finished_at,
        migration_state=migration_state,
        error_category=error_category,
        pre_migration_backup_created=raw["pre_migration_backup_created"],
        output_truncated=raw["output_truncated"],
    )


def scan_migration_job_metadata(root: Path) -> list[MigrationJob]:
    resolved = _validate_jobs_root(root, create=False)
    try:
        entries = list(resolved.iterdir())
    except OSError as exc:
        raise MigrationJobError("Migration job storage is unavailable") from exc
    if len(entries) > MAX_MIGRATION_JOB_METADATA_FILES:
        raise MigrationJobError("Migration job metadata count exceeds limit")

    jobs: list[MigrationJob] = []
    for path in entries:
        if (
            path.is_symlink()
            or not path.is_file()
            or path.suffix != ".json"
            or not MIGRATION_JOB_ID_RE.fullmatch(path.stem)
        ):
            raise MigrationJobError("Migration job storage contains an unsafe entry")
        jobs.append(parse_migration_job_metadata(path))
    return jobs


class MigrationJobRunner:
    def __init__(
        self,
        *,
        manager: DatabaseManager,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        jobs_root: Path,
    ) -> None:
        self.jobs_root = _validate_jobs_root(jobs_root, create=True)
        self.manager = manager
        self.registry = registry
        self.safety = safety
        self._lock = threading.RLock()
        self._jobs: dict[str, MigrationJob] = {}
        self._load_existing_metadata()

    def _metadata_path(self, job_id: str) -> Path:
        if not MIGRATION_JOB_ID_RE.fullmatch(job_id):
            raise MigrationJobError("Invalid migration job identifier")
        return self.jobs_root / f"{job_id}.json"

    def _persist(
        self,
        job: MigrationJob,
        *,
        previous: MigrationJob | None = None,
    ) -> None:
        path = self._metadata_path(job.job_id)
        exists = path.exists() or path.is_symlink()
        if previous is None:
            if exists:
                raise MigrationJobError("Migration job metadata already exists")
        else:
            if not exists:
                raise MigrationJobError("Migration job metadata disappeared")
            persisted = parse_migration_job_metadata(path)
            if persisted != previous:
                raise MigrationJobError("Migration job metadata changed unexpectedly")
        content = (
            json.dumps(
                job.persisted_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if len(content) > MAX_MIGRATION_JOB_METADATA_BYTES:
            raise MigrationJobError("Migration job metadata exceeds size limit")
        try:
            atomic_replace_private(path, content)
        except PrivateAtomicWriteError as exc:
            raise MigrationJobError("Migration job metadata could not be written") from exc
        _fsync_directory(self.jobs_root)

    def _load_existing_metadata(self) -> None:
        jobs = scan_migration_job_metadata(self.jobs_root)
        for job in jobs:
            if job.state in {MigrationJobState.QUEUED, MigrationJobState.RUNNING}:
                interrupted = replace(
                    job,
                    state=MigrationJobState.INTERRUPTED,
                    finished_at=utc_now(),
                    error_category="runner_restart",
                    migration_state=None,
                )
                self._persist(interrupted, previous=job)
                job = interrupted
            self._jobs[job.job_id] = job

    def _project_has_active_job(self, project: str) -> bool:
        return any(
            job.project == project
            and job.state in {MigrationJobState.QUEUED, MigrationJobState.RUNNING}
            for job in self._jobs.values()
        )

    def start(
        self,
        project: str,
        *,
        expected_binding_fingerprint: str,
        expected_commit: str,
    ) -> dict[str, Any]:
        if not _PROJECT_RE.fullmatch(project):
            raise MigrationJobError("Migration job project is invalid")
        if not _FINGERPRINT_RE.fullmatch(expected_binding_fingerprint):
            raise MigrationJobError("Expected migration binding is invalid")
        if not _COMMIT_RE.fullmatch(expected_commit):
            raise MigrationJobError("Expected migration commit is invalid")
        with self._lock:
            if self._project_has_active_job(project):
                raise MigrationJobError("A migration job is already active for this project")
            job = MigrationJob(
                job_id=uuid4().hex,
                project=project,
                state=MigrationJobState.QUEUED,
                created_at=utc_now(),
                expected_binding_fingerprint=expected_binding_fingerprint,
                expected_commit=expected_commit,
            )
            self._persist(job)
            self._jobs[job.job_id] = job

        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id,),
            name=f"runner-mcp-migration-{job.job_id[:8]}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError as exc:
            self._finish_failure(
                job.job_id,
                state=MigrationJobState.ERROR,
                category="unexpected_error",
            )
            raise MigrationJobError("Migration worker could not start") from exc
        return job.public_dict()

    def _update(
        self,
        job_id: str,
        *,
        state: MigrationJobState | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        migration_state: str | None = None,
        error_category: str | None = None,
        pre_migration_backup_created: bool | None = None,
        output_truncated: bool | None = None,
    ) -> MigrationJob:
        with self._lock:
            previous = self._jobs[job_id]
            changes: dict[str, Any] = {}
            if state is not None:
                changes["state"] = state
            if started_at is not None:
                changes["started_at"] = started_at
            if finished_at is not None:
                changes["finished_at"] = finished_at
            if migration_state is not None:
                changes["migration_state"] = migration_state
            if error_category is not None:
                changes["error_category"] = error_category
            if pre_migration_backup_created is not None:
                changes["pre_migration_backup_created"] = pre_migration_backup_created
            if output_truncated is not None:
                changes["output_truncated"] = output_truncated
            updated = replace(previous, **changes)
            self._persist(updated, previous=previous)
            self._jobs[job_id] = updated
            return updated

    def _finish_failure(
        self,
        job_id: str,
        *,
        state: MigrationJobState,
        category: str,
        migration_state: str | None = None,
        pre_migration_backup_created: bool = False,
        output_truncated: bool = False,
    ) -> None:
        self._update(
            job_id,
            state=state,
            finished_at=utc_now(),
            migration_state=migration_state,
            error_category=category,
            pre_migration_backup_created=pre_migration_backup_created,
            output_truncated=output_truncated,
        )

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            project = job.project
            expected_fingerprint = job.expected_binding_fingerprint
            expected_commit = job.expected_commit

        try:
            binding, summary = migration_plan_material(self.registry, project)
            if (
                migration_binding_fingerprint(binding) != expected_fingerprint
                or summary["commit"] != expected_commit
            ):
                self._finish_failure(
                    job_id,
                    state=MigrationJobState.ERROR,
                    category="plan_changed",
                )
                return
            config = self.registry.projects.get(project)
            if config is None:
                self._finish_failure(
                    job_id,
                    state=MigrationJobState.ERROR,
                    category="plan_changed",
                )
                return
            self.safety.assert_project_action_allowed(
                ActionClass.MIGRATION,
                environment=config.environment,
            )
        except OperatorStopActive:
            self._finish_failure(
                job_id,
                state=MigrationJobState.STOPPED,
                category="operator_stop",
            )
            return
        except SafetyConfigurationError:
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="safety_configuration",
            )
            return
        except (SourceControlError, ValueError):
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="plan_changed",
            )
            return
        except Exception:  # noqa: BLE001 - worker must persist bounded terminal state
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="unexpected_error",
            )
            return

        self._update(
            job_id,
            state=MigrationJobState.RUNNING,
            started_at=utc_now(),
        )
        try:
            result = self.manager.apply_migrations(project)
        except OperatorStopActive:
            self._finish_failure(
                job_id,
                state=MigrationJobState.STOPPED,
                category="operator_stop",
            )
            return
        except SafetyConfigurationError:
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="safety_configuration",
            )
            return
        except DatabaseManagerError as exc:
            category = (
                "database_busy"
                if str(exc) == "Another database operation is already in progress"
                else "migration_failed"
            )
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category=category,
            )
            return
        except Exception:  # noqa: BLE001 - worker must persist bounded terminal state
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="unexpected_error",
            )
            return

        migration_state = result.get("status")
        backup = result.get("pre_migration_backup")
        backup_id = backup.get("backup_id") if isinstance(backup, dict) else None
        output_truncated = result.get("output_truncated")
        if (
            migration_state not in {"applied", "failed", "timed_out"}
            or result.get("project") != project
            or result.get("database_restore_performed") is not False
            or not isinstance(backup_id, str)
            or not BACKUP_ID_RE.fullmatch(backup_id)
            or not isinstance(output_truncated, bool)
        ):
            self._finish_failure(
                job_id,
                state=MigrationJobState.ERROR,
                category="unexpected_error",
            )
            return
        backup_created = True
        if migration_state == "applied":
            self._update(
                job_id,
                state=MigrationJobState.COMPLETED,
                finished_at=utc_now(),
                migration_state="applied",
                pre_migration_backup_created=backup_created,
                output_truncated=output_truncated,
            )
            return
        self._finish_failure(
            job_id,
            state=MigrationJobState.ERROR,
            category=(
                "migration_timed_out"
                if migration_state == "timed_out"
                else "migration_failed"
            ),
            migration_state=migration_state,
            pre_migration_backup_created=backup_created,
            output_truncated=output_truncated,
        )

    def status(self, job_id: str) -> dict[str, Any]:
        if not MIGRATION_JOB_ID_RE.fullmatch(job_id):
            raise MigrationJobError("Invalid migration job identifier")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise MigrationJobError("Unknown migration job")
            return job.public_dict()
