import json
import stat
import threading
import time
from pathlib import Path

import pytest

from runner_mcp.deployment_jobs import DeploymentJobRunner
from runner_mcp.deployment_manager import DeploymentError
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


class FakeManager:
    def __init__(self, *, block: threading.Event | None = None, fail: bool = False) -> None:
        self.block = block
        self.fail = fail
        self.plans: list[str] = []
        self.deploys: list[str] = []

    def plan(self, project: str) -> dict:
        self.plans.append(project)
        return {"project": project, "environment": "staging", "commit": "a" * 40}

    def rollback_plan(self, project: str) -> dict:
        return {
            "project": project,
            "current_release": "new",
            "target_release": "old",
            "allowed": True,
            "one_step_only": True,
            "blocked_by_database_migration": False,
            "database_restore_performed": False,
        }

    def rollback_one(
        self,
        project: str,
        *,
        expected_current_release: str | None = None,
        expected_target_release: str | None = None,
    ) -> dict:
        return {
            "project": project,
            "status": "rolled_back",
            "current_release": "old",
            "target_release": "old",
            "database_restore_performed": False,
        }

    def deploy(self, project: str, *, expected_commit: str | None = None) -> dict:
        self.deploys.append(project)
        if self.block is not None:
            self.block.wait(timeout=3)
        if self.fail:
            raise DeploymentError("private path should never persist")
        return {
            "project": project,
            "status": "deployed",
            "release_id": "safe-release",
            "commit": "a" * 40,
        }


def guard(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def wait_terminal(runner: DeploymentJobRunner, job_id: str) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        status = runner.status(job_id)
        if status["state"] not in {"queued", "running"}:
            return status
        time.sleep(0.01)
    raise AssertionError("deployment job did not finish")


def test_deployment_job_completes_and_persists_safe_result(tmp_path: Path) -> None:
    manager = FakeManager()
    runner = DeploymentJobRunner(
        manager=manager,
        safety=guard(tmp_path),
        jobs_root=tmp_path / "jobs",
    )

    started = runner.start("demo")
    finished = wait_terminal(runner, started["job_id"])

    assert finished["state"] == "completed"
    assert finished["result"]["status"] == "deployed"
    assert stat.S_IMODE((tmp_path / "jobs").stat().st_mode) == 0o700
    metadata = tmp_path / "jobs" / f"{started['job_id']}.json"
    assert stat.S_IMODE(metadata.stat().st_mode) == 0o600


def test_only_one_active_deployment_per_project(tmp_path: Path) -> None:
    block = threading.Event()
    runner = DeploymentJobRunner(
        manager=FakeManager(block=block),
        safety=guard(tmp_path),
        jobs_root=tmp_path / "jobs",
    )
    first = runner.start("demo")

    deadline = time.monotonic() + 1
    while time.monotonic() < deadline and runner.status(first["job_id"])["state"] != "running":
        time.sleep(0.01)

    with pytest.raises(Exception, match="already active"):
        runner.start("demo")

    block.set()
    wait_terminal(runner, first["job_id"])


def test_deployment_error_is_categorized_without_message(tmp_path: Path) -> None:
    runner = DeploymentJobRunner(
        manager=FakeManager(fail=True),
        safety=guard(tmp_path),
        jobs_root=tmp_path / "jobs",
    )

    started = runner.start("demo")
    finished = wait_terminal(runner, started["job_id"])

    assert finished["state"] == "error"
    assert finished["error_category"] == "deployment_error"
    assert "private path" not in json.dumps(finished)


def test_running_job_is_marked_interrupted_after_restart(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir(mode=0o700)
    job_id = "a" * 32
    (jobs / f"{job_id}.json").write_text(
        json.dumps(
            {
                "job_id": job_id,
                "project": "demo",
                "state": "running",
                "created_at": "2026-09-20T08:00:00+00:00",
                "started_at": "2026-09-20T08:00:01+00:00",
                "finished_at": None,
                "result": None,
                "error_category": None,
            }
        ),
        encoding="utf-8",
    )

    runner = DeploymentJobRunner(
        manager=FakeManager(),
        safety=guard(tmp_path),
        jobs_root=jobs,
    )

    status = runner.status(job_id)
    assert status["state"] == "interrupted"
    assert status["error_category"] == "runner_restart"


def test_rollback_job_uses_same_persisted_job_model(tmp_path: Path) -> None:
    runner = DeploymentJobRunner(
        manager=FakeManager(),
        safety=guard(tmp_path),
        jobs_root=tmp_path / "jobs",
    )

    started = runner.start_rollback("demo")
    finished = wait_terminal(runner, started["job_id"])

    assert started["operation"] == "rollback"
    assert finished["operation"] == "rollback"
    assert finished["state"] == "completed"
    assert finished["result"]["status"] == "rolled_back"


def test_rollback_job_is_blocked_when_plan_crosses_migration_boundary(tmp_path: Path) -> None:
    class BlockedManager(FakeManager):
        def rollback_plan(self, project: str) -> dict:
            return {"project": project, "allowed": False}

    runner = DeploymentJobRunner(
        manager=BlockedManager(),
        safety=guard(tmp_path),
        jobs_root=tmp_path / "jobs",
    )

    with pytest.raises(Exception, match="database migration boundary"):
        runner.start_rollback("demo")
