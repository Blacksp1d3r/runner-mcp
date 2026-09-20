from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .deployment_manager import DeploymentError, DeploymentManager
from .operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    SafetyConfigurationError,
)


class DeploymentJobError(RuntimeError):
    pass


class DeploymentJobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"
    INTERRUPTED = "interrupted"


TERMINAL_STATES = {
    DeploymentJobState.COMPLETED,
    DeploymentJobState.STOPPED,
    DeploymentJobState.ERROR,
    DeploymentJobState.INTERRUPTED,
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass
class DeploymentJob:
    job_id: str
    project: str
    operation: str
    state: DeploymentJobState
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None
    error_category: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project": self.project,
            "operation": self.operation,
            "state": self.state.value,
            "created_at": iso_or_none(self.created_at),
            "started_at": iso_or_none(self.started_at),
            "finished_at": iso_or_none(self.finished_at),
            "result": self.result,
            "error_category": self.error_category,
        }


class DeploymentJobRunner:
    def __init__(
        self,
        *,
        manager: DeploymentManager,
        safety: OperatorSafetyGuard,
        jobs_root: Path,
    ) -> None:
        if not jobs_root.is_absolute():
            raise DeploymentJobError("Deployment jobs root must be absolute")
        if jobs_root.exists() and jobs_root.is_symlink():
            raise DeploymentJobError("Deployment jobs root must not be a symlink")
        jobs_root.mkdir(parents=True, exist_ok=True)
        os.chmod(jobs_root, 0o700)
        self.jobs_root = jobs_root.resolve(strict=True)
        if not self.jobs_root.is_dir():
            raise DeploymentJobError("Deployment jobs root is unavailable")

        self.manager = manager
        self.safety = safety
        self._lock = threading.RLock()
        self._jobs: dict[str, DeploymentJob] = {}
        self._load_existing_metadata()

    def _metadata_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.json"

    def _persist(self, job: DeploymentJob) -> None:
        path = self._metadata_path(job.job_id)
        temp = path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(job.public_dict(), sort_keys=True, separators=(",", ":")),
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
            if path.is_symlink():
                continue
            job_id = path.stem
            if len(job_id) != 32 or any(char not in "0123456789abcdef" for char in job_id):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                job = DeploymentJob(
                    job_id=job_id,
                    project=str(raw["project"]),
                    operation=str(raw.get("operation", "deploy")),
                    state=DeploymentJobState(raw["state"]),
                    created_at=self._parse_datetime(raw["created_at"]) or utc_now(),
                    started_at=self._parse_datetime(raw.get("started_at")),
                    finished_at=self._parse_datetime(raw.get("finished_at")),
                    result=raw.get("result"),
                    error_category=raw.get("error_category"),
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue

            if job.operation not in {"deploy", "rollback"}:
                continue
            if job.state in {DeploymentJobState.QUEUED, DeploymentJobState.RUNNING}:
                job.state = DeploymentJobState.INTERRUPTED
                job.finished_at = utc_now()
                job.error_category = "runner_restart"
                job.result = None
                self._persist(job)
            self._jobs[job_id] = job

    def _project_has_active_job(self, project: str) -> bool:
        return any(
            job.project == project
            and job.state in {DeploymentJobState.QUEUED, DeploymentJobState.RUNNING}
            for job in self._jobs.values()
        )

    def _enqueue(self, project: str, operation: str) -> dict[str, Any]:
        with self._lock:
            if self._project_has_active_job(project):
                raise DeploymentJobError(
                    "A deployment or rollback job is already active for this project"
                )

            job_id = uuid4().hex
            job = DeploymentJob(
                job_id=job_id,
                project=project,
                operation=operation,
                state=DeploymentJobState.QUEUED,
                created_at=utc_now(),
            )
            self._jobs[job_id] = job
            self._persist(job)

        worker = threading.Thread(
            target=self._run_job,
            args=(job_id,),
            name=f"runner-mcp-{operation}-{job_id[:8]}",
            daemon=True,
        )
        worker.start()
        return job.public_dict()

    def start(self, project: str) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        self.manager.plan(project)
        return self._enqueue(project, "deploy")

    def start_rollback(self, project: str) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.CODE_ROLLBACK)
        self.safety.assert_code_rollback_steps(1)
        plan = self.manager.rollback_plan(project)
        if not plan.get("allowed", False):
            raise DeploymentJobError(
                "Code rollback is blocked across a database migration boundary"
            )
        return self._enqueue(project, "rollback")

    def _set_job(
        self,
        job_id: str,
        *,
        state: DeploymentJobState | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        result: dict[str, Any] | None = None,
        error_category: str | None = None,
    ) -> DeploymentJob:
        with self._lock:
            job = self._jobs[job_id]
            if state is not None:
                job.state = state
            if started_at is not None:
                job.started_at = started_at
            if finished_at is not None:
                job.finished_at = finished_at
            if result is not None:
                job.result = result
            if error_category is not None:
                job.error_category = error_category
            self._persist(job)
            return job

    def _run_job(self, job_id: str) -> None:
        self._set_job(
            job_id,
            state=DeploymentJobState.RUNNING,
            started_at=utc_now(),
        )
        with self._lock:
            project = self._jobs[job_id].project
            operation = self._jobs[job_id].operation

        try:
            result = (
                self.manager.deploy(project)
                if operation == "deploy"
                else self.manager.rollback_one(project)
            )
            self._set_job(
                job_id,
                state=DeploymentJobState.COMPLETED,
                finished_at=utc_now(),
                result=result,
            )
        except OperatorStopActive:
            self._set_job(
                job_id,
                state=DeploymentJobState.STOPPED,
                finished_at=utc_now(),
                error_category="operator_stop",
            )
        except SafetyConfigurationError:
            self._set_job(
                job_id,
                state=DeploymentJobState.ERROR,
                finished_at=utc_now(),
                error_category="safety_configuration",
            )
        except DeploymentError:
            self._set_job(
                job_id,
                state=DeploymentJobState.ERROR,
                finished_at=utc_now(),
                error_category=(
                    "deployment_error" if operation == "deploy" else "rollback_error"
                ),
            )
        except Exception:  # noqa: BLE001 - background jobs must fail closed
            self._set_job(
                job_id,
                state=DeploymentJobState.ERROR,
                finished_at=utc_now(),
                error_category="unexpected_error",
            )

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise DeploymentJobError("Unknown deployment job")
            return job.public_dict()
