import json
import sys
import time
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.config import TestProfile as RunnerTestProfile
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.test_runner import TestRunner as Runner
from runner_mcp.test_runner import TestRunnerError as RunnerError


def _profile(code: str, *, parallel_safe: bool = False) -> RunnerTestProfile:
    return RunnerTestProfile(
        argv=[sys.executable, "-c", code],
        timeout_seconds=5,
        max_log_bytes=4096,
        parallel_safe=parallel_safe,
    )


def _runner(
    tmp_path: Path,
    projects: dict[str, ProjectConfig],
    *,
    workers: int = 2,
    queue_limit: int = 16,
) -> Runner:
    for project in projects.values():
        project.root.mkdir(parents=True, exist_ok=True)
    return Runner(
        registry=ProjectRegistry(projects=projects),
        safety=OperatorSafetyGuard(
            stop_file=tmp_path / "operator.stop",
            retention=RetentionPolicy(),
            retention_confirmed=True,
        ),
        jobs_root=tmp_path / "jobs",
        max_concurrent_jobs=workers,
        max_queued_jobs=queue_limit,
        poll_interval_seconds=0.01,
        terminate_grace_seconds=0.1,
    )


def _wait_status(
    runner: Runner,
    job_id: str,
    wanted: set[str],
    *,
    timeout: float = 3.0,
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = runner.status(job_id)
        if status["status"] in wanted:
            return status
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not reach {wanted}")


def test_two_projects_run_at_the_same_time(tmp_path: Path) -> None:
    slow = "import time; time.sleep(2)"
    runner = _runner(
        tmp_path,
        {
            "alpha": ProjectConfig(
                display_name="Alpha",
                repository="example/alpha",
                root=tmp_path / "alpha",
                test_profiles={"unit": _profile(slow)},
            ),
            "beta": ProjectConfig(
                display_name="Beta",
                repository="example/beta",
                root=tmp_path / "beta",
                test_profiles={"unit": _profile(slow)},
            ),
        },
        workers=2,
    )
    try:
        first = runner.start_test("alpha", "unit")
        second = runner.start_test("beta", "unit")

        _wait_status(runner, first["job_id"], {"running"})
        _wait_status(runner, second["job_id"], {"running"})
        status = runner.queue_status()

        assert status["running_jobs"] == 2
        assert status["available_workers"] == 0
    finally:
        runner.cancel(first["job_id"])
        runner.cancel(second["job_id"])
        runner.shutdown()


def test_parallel_safe_profiles_can_share_one_project(tmp_path: Path) -> None:
    slow = "import time; time.sleep(2)"
    runner = _runner(
        tmp_path,
        {
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "demo",
                max_parallel_tests=2,
                test_profiles={
                    "unit": _profile(slow, parallel_safe=True),
                    "lint": _profile(slow, parallel_safe=True),
                },
            )
        },
        workers=2,
    )
    try:
        first = runner.start_test("demo", "unit")
        second = runner.start_test("demo", "lint")

        _wait_status(runner, first["job_id"], {"running"})
        _wait_status(runner, second["job_id"], {"running"})

        assert runner.queue_status()["jobs_per_project"]["demo"]["running"] == 2
    finally:
        runner.cancel(first["job_id"])
        runner.cancel(second["job_id"])
        runner.shutdown()


def test_non_parallel_safe_profile_keeps_project_lock(tmp_path: Path) -> None:
    slow = "import time; time.sleep(2)"
    runner = _runner(
        tmp_path,
        {
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "demo",
                max_parallel_tests=2,
                test_profiles={
                    "unsafe": _profile(slow, parallel_safe=False),
                    "safe": _profile(slow, parallel_safe=True),
                },
            )
        },
        workers=2,
    )
    try:
        first = runner.start_test("demo", "unsafe")
        _wait_status(runner, first["job_id"], {"running"})
        second = runner.start_test("demo", "safe")

        status = _wait_status(runner, second["job_id"], {"queued"})
        assert status["waiting_reason"] == "project_lock"
        assert runner.queue_status()["jobs_per_project"]["demo"]["project_lock"] is True
    finally:
        runner.cancel(first["job_id"])
        runner.cancel(second["job_id"])
        runner.shutdown()


def test_global_worker_limit_applies_without_rejecting_work(tmp_path: Path) -> None:
    slow = "import time; time.sleep(2)"
    projects = {
        name: ProjectConfig(
            display_name=name,
            repository=f"example/{name}",
            root=tmp_path / name,
            test_profiles={"unit": _profile(slow)},
        )
        for name in ("alpha", "beta", "gamma")
    }
    runner = _runner(tmp_path, projects, workers=2)
    jobs = []
    try:
        jobs = [runner.start_test(name, "unit") for name in projects]
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            status = runner.queue_status()
            if status["running_jobs"] == 2 and status["queued_jobs"] == 1:
                break
            time.sleep(0.01)
        else:
            raise AssertionError("expected two running jobs and one queued job")

        assert status["concurrency_limit"] == 2
        assert status["available_workers"] == 0
    finally:
        for job in jobs:
            runner.cancel(job["job_id"])
        runner.shutdown()


def test_round_robin_fairness_prevents_one_project_monopoly(tmp_path: Path) -> None:
    slow = "import time; time.sleep(30)"
    runner = _runner(
        tmp_path,
        {
            "alpha": ProjectConfig(
                display_name="Alpha",
                repository="example/alpha",
                root=tmp_path / "alpha",
                test_profiles={"unit": _profile(slow)},
            ),
            "beta": ProjectConfig(
                display_name="Beta",
                repository="example/beta",
                root=tmp_path / "beta",
                test_profiles={"unit": _profile(slow)},
            ),
        },
        workers=1,
    )
    try:
        alpha1 = runner.start_test("alpha", "unit")
        _wait_status(runner, alpha1["job_id"], {"running"})
        alpha2 = runner.start_test("alpha", "unit")
        alpha3 = runner.start_test("alpha", "unit")
        beta1 = runner.start_test("beta", "unit")

        runner.cancel(alpha1["job_id"])
        _wait_status(runner, alpha1["job_id"], {"cancelled"})

        _wait_status(runner, beta1["job_id"], {"running"})
        assert runner.status(alpha2["job_id"])["status"] == "queued"
        assert runner.status(alpha3["job_id"])["status"] == "queued"
    finally:
        for job in (alpha2, alpha3, beta1):
            runner.cancel(job["job_id"])
        runner.shutdown()


def test_queue_overflow_fails_closed_with_backpressure(tmp_path: Path) -> None:
    slow = "import time; time.sleep(30)"
    runner = _runner(
        tmp_path,
        {
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "demo",
                test_profiles={"unit": _profile(slow)},
            )
        },
        workers=1,
        queue_limit=1,
    )
    try:
        first = runner.start_test("demo", "unit")
        _wait_status(runner, first["job_id"], {"running"})
        second = runner.start_test("demo", "unit")
        _wait_status(runner, second["job_id"], {"queued"})

        with pytest.raises(RunnerError, match="queue capacity"):
            runner.start_test("demo", "unit")
    finally:
        runner.cancel(first["job_id"])
        runner.cancel(second["job_id"])
        runner.shutdown()


def test_queued_job_can_be_cancelled_before_claim(tmp_path: Path) -> None:
    slow = "import time; time.sleep(30)"
    runner = _runner(
        tmp_path,
        {
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "demo",
                test_profiles={"unit": _profile(slow)},
            )
        },
        workers=1,
    )
    try:
        first = runner.start_test("demo", "unit")
        _wait_status(runner, first["job_id"], {"running"})
        second = runner.start_test("demo", "unit")
        _wait_status(runner, second["job_id"], {"queued"})

        cancelled = runner.cancel(second["job_id"])

        assert cancelled["status"] == "cancelled"
        assert cancelled["error_category"] == "cancelled_before_claim"
    finally:
        runner.cancel(first["job_id"])
        runner.shutdown()


def test_queued_job_survives_runner_restart_and_is_dispatched(tmp_path: Path) -> None:
    jobs_root = tmp_path / "jobs"
    jobs_root.mkdir()
    project_root = tmp_path / "demo"
    project_root.mkdir()
    job_id = "d" * 32
    metadata = {
        "job_id": job_id,
        "project": "demo",
        "suite": "unit",
        "status": "queued",
        "created_at": "2026-09-21T00:00:00+00:00",
        "claimed_at": None,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "log_truncated": False,
        "error_category": None,
    }
    (jobs_root / f"{job_id}.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    runner = Runner(
        registry=ProjectRegistry(
            projects={
                "demo": ProjectConfig(
                    display_name="Demo",
                    repository="example/demo",
                    root=project_root,
                    test_profiles={
                        "unit": _profile("import time; time.sleep(30)")
                    },
                )
            }
        ),
        safety=OperatorSafetyGuard(
            stop_file=tmp_path / "operator.stop",
            retention=RetentionPolicy(),
            retention_confirmed=True,
        ),
        jobs_root=jobs_root,
        max_concurrent_jobs=1,
        poll_interval_seconds=0.01,
        terminate_grace_seconds=0.1,
    )
    try:
        _wait_status(runner, job_id, {"running"})
    finally:
        runner.cancel(job_id)
        runner.shutdown()


def test_claimed_or_running_job_is_not_replayed_after_restart(tmp_path: Path) -> None:
    jobs_root = tmp_path / "jobs"
    jobs_root.mkdir()
    project_root = tmp_path / "demo"
    project_root.mkdir()
    job_id = "c" * 32
    metadata = {
        "job_id": job_id,
        "project": "demo",
        "suite": "unit",
        "status": "claimed",
        "created_at": "2026-09-21T00:00:00+00:00",
        "claimed_at": "2026-09-21T00:00:01+00:00",
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "log_truncated": False,
        "error_category": None,
    }
    (jobs_root / f"{job_id}.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    runner = Runner(
        registry=ProjectRegistry(
            projects={
                "demo": ProjectConfig(
                    display_name="Demo",
                    repository="example/demo",
                    root=project_root,
                    test_profiles={"unit": _profile("raise SystemExit(99)")},
                )
            }
        ),
        safety=OperatorSafetyGuard(
            stop_file=tmp_path / "operator.stop",
            retention=RetentionPolicy(),
            retention_confirmed=True,
        ),
        jobs_root=jobs_root,
        max_concurrent_jobs=1,
        poll_interval_seconds=0.01,
    )
    try:
        status = runner.status(job_id)
        assert status["status"] == "interrupted"
        assert status["error_category"] == "runner_restart"
    finally:
        runner.shutdown()
