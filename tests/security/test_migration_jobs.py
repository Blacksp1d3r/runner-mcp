from __future__ import annotations

import json
import stat
import threading
import time
from pathlib import Path

import pytest

from runner_mcp import migration_jobs as migration_jobs_module
from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.database_manager import DatabaseManagerError
from runner_mcp.migration_jobs import (
    MigrationJobError,
    MigrationJobRunner,
    migration_binding_fingerprint,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy

COMMIT = "a" * 40


def registry(tmp_path: Path) -> ProjectRegistry:
    root = tmp_path / "project"
    root.mkdir()
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment="staging",
                root=root,
            )
        }
    )


def guard(
    tmp_path: Path,
    *,
    stopped: bool = False,
    retention_confirmed: bool = True,
) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=retention_confirmed,
    )


def binding() -> dict:
    return {
        "environment": "staging",
        "repository": "example/demo",
        "database": {"engine": "postgresql"},
        "source": {"commit": COMMIT, "clean": True},
    }


def material(_registry: ProjectRegistry, project: str) -> tuple[dict, dict]:
    assert project == "demo"
    return (
        binding(),
        {
            "action": "migration",
            "environment": "staging",
            "commit": COMMIT,
            "pre_migration_backup_required": True,
            "automatic_database_restore": False,
        },
    )


class FakeDatabaseManager:
    def __init__(
        self,
        *,
        status: str = "applied",
        error: Exception | None = None,
        block: threading.Event | None = None,
    ) -> None:
        self.status = status
        self.error = error
        self.block = block
        self.calls: list[str] = []

    def apply_migrations(self, project: str) -> dict:
        self.calls.append(project)
        if self.block is not None:
            self.block.wait(timeout=3)
        if self.error is not None:
            raise self.error
        return {
            "project": project,
            "status": self.status,
            "exit_code": 0 if self.status == "applied" else 9,
            "pre_migration_backup": {
                "backup_id": "20260928T060000Z-" + ("b" * 12),
                "available": True,
            },
            "output": "sensitive output must not persist",
            "output_truncated": self.status == "timed_out",
            "database_restore_performed": False,
        }


def expected_fingerprint() -> str:
    return migration_binding_fingerprint(binding())


def wait_terminal(runner: MigrationJobRunner, job_id: str) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        status = runner.status(job_id)
        if status["state"] not in {"queued", "running"}:
            return status
        time.sleep(0.01)
    raise AssertionError("migration job did not finish")


def runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    manager: FakeDatabaseManager | None = None,
    stopped: bool = False,
    retention_confirmed: bool = True,
) -> MigrationJobRunner:
    monkeypatch.setattr(migration_jobs_module, "migration_plan_material", material)
    return MigrationJobRunner(
        manager=manager or FakeDatabaseManager(),
        registry=registry(tmp_path),
        safety=guard(
            tmp_path,
            stopped=stopped,
            retention_confirmed=retention_confirmed,
        ),
        jobs_root=tmp_path / "migration-jobs",
    )


def test_queued_metadata_is_durable_before_worker_starts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_start(thread: threading.Thread) -> None:
        root = tmp_path / "migration-jobs"
        files = list(root.glob("*.json"))
        assert len(files) == 1
        observed["payload"] = json.loads(files[0].read_text(encoding="utf-8"))
        observed["mode"] = stat.S_IMODE(files[0].stat().st_mode)

    monkeypatch.setattr(threading.Thread, "start", fake_start)
    active = runner(tmp_path, monkeypatch)

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )

    assert started["state"] == "queued"
    assert observed["mode"] == 0o600
    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["state"] == "queued"
    assert payload["expected_binding_fingerprint"] == expected_fingerprint()
    assert stat.S_IMODE((tmp_path / "migration-jobs").stat().st_mode) == 0o700


def test_success_calls_existing_database_manager_once_and_persists_no_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDatabaseManager(status="applied")
    active = runner(tmp_path, monkeypatch, manager=manager)

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert manager.calls == ["demo"]
    assert finished["state"] == "completed"
    assert finished["migration_state"] == "applied"
    assert finished["pre_migration_backup_created"] is True
    assert "output" not in finished
    assert "expected_binding_fingerprint" not in finished
    assert "expected_commit" not in finished
    raw = (tmp_path / "migration-jobs" / f"{started['job_id']}.json").read_text()
    assert "sensitive output" not in raw


def test_plan_change_fails_before_database_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDatabaseManager()
    active = runner(tmp_path, monkeypatch, manager=manager)

    started = active.start(
        "demo",
        expected_binding_fingerprint="f" * 64,
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert finished["state"] == "error"
    assert finished["error_category"] == "plan_changed"
    assert manager.calls == []


def test_operator_stop_becomes_terminal_stopped_without_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDatabaseManager()
    active = runner(tmp_path, monkeypatch, manager=manager, stopped=True)

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert finished["state"] == "stopped"
    assert finished["error_category"] == "operator_stop"
    assert manager.calls == []


def test_safety_configuration_failure_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = FakeDatabaseManager()
    active = runner(
        tmp_path,
        monkeypatch,
        manager=manager,
        retention_confirmed=False,
    )

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert finished["state"] == "error"
    assert finished["error_category"] == "safety_configuration"
    assert manager.calls == []


@pytest.mark.parametrize(
    ("manager", "category", "migration_state"),
    [
        (
            FakeDatabaseManager(
                error=DatabaseManagerError(
                    "Another database operation is already in progress"
                )
            ),
            "database_busy",
            None,
        ),
        (
            FakeDatabaseManager(error=DatabaseManagerError("/private/db/path")),
            "migration_failed",
            None,
        ),
        (
            FakeDatabaseManager(status="failed"),
            "migration_failed",
            "failed",
        ),
        (
            FakeDatabaseManager(status="timed_out"),
            "migration_timed_out",
            "timed_out",
        ),
    ],
)
def test_database_failures_are_bounded_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manager: FakeDatabaseManager,
    category: str,
    migration_state: str | None,
) -> None:
    active = runner(tmp_path, monkeypatch, manager=manager)

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert manager.calls == ["demo"]
    assert finished["state"] == "error"
    assert finished["error_category"] == category
    assert finished["migration_state"] == migration_state
    assert "/private/db/path" not in json.dumps(finished)


def test_only_one_active_migration_job_per_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    block = threading.Event()
    manager = FakeDatabaseManager(block=block)
    active = runner(tmp_path, monkeypatch, manager=manager)
    first = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )

    deadline = time.monotonic() + 1
    while time.monotonic() < deadline and active.status(first["job_id"])["state"] != "running":
        time.sleep(0.01)

    with pytest.raises(MigrationJobError, match="already active"):
        active.start(
            "demo",
            expected_binding_fingerprint=expected_fingerprint(),
            expected_commit=COMMIT,
        )

    block.set()
    wait_terminal(active, first["job_id"])


def _job_payload(
    job_id: str,
    *,
    state: str,
    started_at: str | None,
    finished_at: str | None,
    error_category: str | None,
) -> dict:
    return {
        "job_id": job_id,
        "project": "demo",
        "operation": "migration",
        "state": state,
        "created_at": "2026-09-28T06:00:00+00:00",
        "started_at": started_at,
        "finished_at": finished_at,
        "migration_state": None,
        "error_category": error_category,
        "pre_migration_backup_created": False,
        "output_truncated": False,
        "expected_binding_fingerprint": "e" * 64,
        "expected_commit": COMMIT,
    }


@pytest.mark.parametrize(
    ("state", "started_at"),
    [
        ("queued", None),
        ("running", "2026-09-28T06:00:01+00:00"),
    ],
)
def test_restart_marks_active_job_interrupted_without_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    started_at: str | None,
) -> None:
    root = tmp_path / "migration-jobs"
    root.mkdir(mode=0o700)
    job_id = "d" * 32
    path = root / f"{job_id}.json"
    path.write_text(
        json.dumps(
            _job_payload(
                job_id,
                state=state,
                started_at=started_at,
                finished_at=None,
                error_category=None,
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)
    manager = FakeDatabaseManager()
    monkeypatch.setattr(migration_jobs_module, "migration_plan_material", material)

    restarted = MigrationJobRunner(
        manager=manager,
        registry=registry(tmp_path),
        safety=guard(tmp_path),
        jobs_root=root,
    )

    status = restarted.status(job_id)
    assert status["state"] == "interrupted"
    assert status["error_category"] == "runner_restart"
    assert manager.calls == []


def test_duplicate_key_metadata_fails_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "migration-jobs"
    root.mkdir(mode=0o700)
    job_id = "c" * 32
    path = root / f"{job_id}.json"
    path.write_text(
        '{"job_id":"' + job_id + '","job_id":"' + job_id + '"}',
        encoding="utf-8",
    )
    path.chmod(0o600)

    with pytest.raises(MigrationJobError, match="duplicate"):
        MigrationJobRunner(
            manager=FakeDatabaseManager(),
            registry=registry(tmp_path),
            safety=guard(tmp_path),
            jobs_root=root,
        )


def test_nonstandard_json_metadata_fails_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "migration-jobs"
    root.mkdir(mode=0o700)
    job_id = "b" * 32
    payload = _job_payload(
        job_id,
        state="error",
        started_at=None,
        finished_at="2026-09-28T06:00:01+00:00",
        error_category="unexpected_error",
    )
    text = json.dumps(payload).replace(
        '"pre_migration_backup_created": false',
        '"pre_migration_backup_created": NaN',
    )
    path = root / f"{job_id}.json"
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)

    with pytest.raises(MigrationJobError, match="non-standard"):
        MigrationJobRunner(
            manager=FakeDatabaseManager(),
            registry=registry(tmp_path),
            safety=guard(tmp_path),
            jobs_root=root,
        )


def test_symlink_or_broad_metadata_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "migration-jobs"
    root.mkdir(mode=0o700)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    outside.chmod(0o600)
    (root / (("a" * 32) + ".json")).symlink_to(outside)

    with pytest.raises(MigrationJobError, match="unsafe"):
        MigrationJobRunner(
            manager=FakeDatabaseManager(),
            registry=registry(tmp_path),
            safety=guard(tmp_path),
            jobs_root=root,
        )

    (root / (("a" * 32) + ".json")).unlink()
    job_id = "f" * 32
    path = root / f"{job_id}.json"
    path.write_text(
        json.dumps(
            _job_payload(
                job_id,
                state="error",
                started_at=None,
                finished_at="2026-09-28T06:00:01+00:00",
                error_category="unexpected_error",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o644)

    with pytest.raises(MigrationJobError, match="permissions"):
        MigrationJobRunner(
            manager=FakeDatabaseManager(),
            registry=registry(tmp_path),
            safety=guard(tmp_path),
            jobs_root=root,
        )


def test_existing_broad_jobs_root_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "migration-jobs"
    root.mkdir(mode=0o755)
    root.chmod(0o755)
    monkeypatch.setattr(migration_jobs_module, "migration_plan_material", material)

    with pytest.raises(MigrationJobError, match="permissions"):
        MigrationJobRunner(
            manager=FakeDatabaseManager(),
            registry=registry(tmp_path),
            safety=guard(tmp_path),
            jobs_root=root,
        )

    assert stat.S_IMODE(root.stat().st_mode) == 0o755


def test_invalid_terminal_manager_evidence_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InvalidEvidenceManager(FakeDatabaseManager):
        def apply_migrations(self, project: str) -> dict:
            self.calls.append(project)
            return {
                "project": project,
                "status": "applied",
                "exit_code": 0,
                "pre_migration_backup": None,
                "output": "must not persist",
                "output_truncated": False,
                "database_restore_performed": False,
            }

    manager = InvalidEvidenceManager()
    active = runner(tmp_path, monkeypatch, manager=manager)

    started = active.start(
        "demo",
        expected_binding_fingerprint=expected_fingerprint(),
        expected_commit=COMMIT,
    )
    finished = wait_terminal(active, started["job_id"])

    assert manager.calls == ["demo"]
    assert finished["state"] == "error"
    assert finished["error_category"] == "unexpected_error"
    assert finished["migration_state"] is None
    raw = (tmp_path / "migration-jobs" / f"{started['job_id']}.json").read_text()
    assert "must not persist" not in raw
