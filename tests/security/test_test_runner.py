import json
import os
import sys
import time
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.config import TestProfile as RunnerTestProfile
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.test_runner import (
    TestJobStatus as RunnerJobStatus,
)
from runner_mcp.test_runner import (
    TestRunner as Runner,
)
from runner_mcp.test_runner import (
    TestRunnerError as RunnerError,
)


def make_registry(root: Path, profiles: dict[str, RunnerTestProfile]) -> ProjectRegistry:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=root,
                test_profiles=profiles,
            )
        }
    )


def make_runner(
    tmp_path: Path,
    profiles: dict[str, RunnerTestProfile],
    *,
    max_concurrent_jobs: int = 2,
) -> tuple[Runner, Path, Path]:
    root = tmp_path / "project"
    stop_file = tmp_path / "operator.stop"
    guard = OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=make_registry(root, profiles),
        safety=guard,
        jobs_root=tmp_path / "jobs",
        max_concurrent_jobs=max_concurrent_jobs,
        poll_interval_seconds=0.02,
        terminate_grace_seconds=0.2,
    )
    return runner, root, stop_file


def python_profile(
    code: str,
    *,
    timeout_seconds: int = 5,
    max_log_bytes: int = 4096,
    env_passthrough: list[str] | None = None,
    extra_args: list[str] | None = None,
) -> RunnerTestProfile:
    argv = [sys.executable, "-c", code]
    if extra_args:
        argv.extend(extra_args)
    return RunnerTestProfile(
        argv=argv,
        timeout_seconds=timeout_seconds,
        max_log_bytes=max_log_bytes,
        env_passthrough=env_passthrough or [],
    )


def wait_terminal(
    runner: Runner,
    job_id: str,
    *,
    timeout: float = 5.0,
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = runner.status(job_id)
        if status["status"] in {
            item.value
            for item in RunnerJobStatus
            if item.value not in {"queued", "claimed", "running"}
        }:
            return status
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not finish in time")


def wait_running(runner: Runner, job_id: str, *, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if runner.status(job_id)["status"] == RunnerJobStatus.RUNNING.value:
            return
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not start in time")


def test_successful_job_and_paged_log(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"ok": python_profile("print('alpha'); print('beta')")},
    )

    started = runner.start_test("demo", "ok")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"], offset=0, length=1)

    assert finished["status"] == "passed"
    assert finished["exit_code"] == 0
    assert log["content"] == "alpha\n"
    assert log["next_offset"] == 1
    assert log["eof"] is False


def test_failed_process_reports_exit_code(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"fail": python_profile("raise SystemExit(7)")},
    )

    started = runner.start_test("demo", "fail")
    finished = wait_terminal(runner, started["job_id"])

    assert finished["status"] == "failed"
    assert finished["exit_code"] == 7


def test_timeout_terminates_process_group(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)", timeout_seconds=1)},
    )

    started = runner.start_test("demo", "slow")
    finished = wait_terminal(runner, started["job_id"], timeout=4)

    assert finished["status"] == "timed_out"
    assert finished["finished_at"] is not None


def test_cancel_terminates_running_job(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
    )

    started = runner.start_test("demo", "slow")
    wait_running(runner, started["job_id"])
    runner.cancel(started["job_id"])
    finished = wait_terminal(runner, started["job_id"])

    assert finished["status"] == "cancelled"


def test_external_operator_stop_terminates_running_job(tmp_path: Path) -> None:
    runner, _, stop_file = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
    )

    started = runner.start_test("demo", "slow")
    wait_running(runner, started["job_id"])
    stop_file.write_text("stop\n", encoding="utf-8")
    finished = wait_terminal(runner, started["job_id"])

    assert finished["status"] == "stopped"


def test_secret_and_private_paths_are_scrubbed_from_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "very-private-test-secret-12345"
    monkeypatch.setenv("RUNNER_TEST_SECRET", secret)
    code = (
        "import os; "
        "print(os.environ['RUNNER_TEST_SECRET']); "
        "print(os.getcwd())"
    )
    runner, root, _ = make_runner(
        tmp_path,
        {
            "scrub": python_profile(
                code,
                env_passthrough=["RUNNER_TEST_SECRET"],
            )
        },
    )

    started = runner.start_test("demo", "scrub")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"])

    assert finished["status"] == "passed"
    assert secret not in log["content"]
    assert str(root) not in log["content"]
    assert "[REDACTED]" in log["content"]
    assert "[PRIVATE_PATH]" in log["content"]


def test_log_output_is_bounded_and_marked_truncated(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {
            "large": python_profile(
                "print('x' * 12000)",
                max_log_bytes=4096,
            )
        },
    )

    started = runner.start_test("demo", "large")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"], length=500)

    assert finished["status"] == "passed"
    assert finished["log_truncated"] is True
    assert "[LOG TRUNCATED BY RUNNER MCP]" in log["content"]
    assert len(log["content"].encode()) < 5000


def test_arguments_are_not_interpreted_by_a_shell(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-exist"
    argument = f"literal; touch {marker}"
    code = "import sys; print(sys.argv[1])"
    runner, _, _ = make_runner(
        tmp_path,
        {
            "literal": python_profile(
                code,
                extra_args=[argument],
            )
        },
    )

    started = runner.start_test("demo", "literal")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"])

    assert finished["status"] == "passed"
    assert "literal; touch" in log["content"]
    assert not marker.exists()


def test_default_project_capacity_queues_second_job(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
    )

    first = runner.start_test("demo", "slow")
    wait_running(runner, first["job_id"])
    second = runner.start_test("demo", "slow")

    assert runner.status(second["job_id"])["status"] == "queued"
    queue = runner.queue_status()
    assert queue["jobs_per_project"]["demo"]["project_lock"] is True

    runner.cancel(first["job_id"])
    wait_terminal(runner, first["job_id"])
    wait_running(runner, second["job_id"])
    runner.cancel(second["job_id"])
    wait_terminal(runner, second["job_id"])


def test_unknown_profile_is_rejected(tmp_path: Path) -> None:
    runner, _, _ = make_runner(tmp_path, {})

    with pytest.raises(RunnerError, match="Unknown or disabled test profile"):
        runner.start_test("demo", "missing")


def test_profile_listing_does_not_expose_argv(tmp_path: Path) -> None:
    profile = python_profile("print('ok')")
    runner, _, _ = make_runner(tmp_path, {"ok": profile})

    listed = runner.list_profiles("demo")

    assert listed == [
        {
            "name": "ok",
            "timeout_seconds": 5,
            "max_log_bytes": 4096,
            "parallel_safe": False,
        }
    ]
    assert sys.executable not in repr(listed)


def test_existing_running_metadata_is_marked_interrupted(tmp_path: Path) -> None:
    jobs_root = tmp_path / "jobs"
    jobs_root.mkdir()
    job_id = "a" * 32
    metadata = {
        "job_id": job_id,
        "project": "demo",
        "suite": "old",
        "status": "running",
        "created_at": "2026-09-20T00:00:00+00:00",
        "started_at": "2026-09-20T00:00:01+00:00",
        "finished_at": None,
        "exit_code": None,
        "log_truncated": False,
        "error_category": None,
    }
    (jobs_root / f"{job_id}.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    root = tmp_path / "project"
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=make_registry(root, {}),
        safety=guard,
        jobs_root=jobs_root,
    )

    status = runner.status(job_id)

    assert status["status"] == "interrupted"
    assert status["error_category"] == "runner_restart"


def test_jobs_root_and_job_files_use_restrictive_permissions(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"ok": python_profile("print('ok')")},
    )

    started = runner.start_test("demo", "ok")
    wait_terminal(runner, started["job_id"])

    jobs_mode = stat_mode(runner.jobs_root)
    log_mode = stat_mode(runner.jobs_root / f"{started['job_id']}.log")
    metadata_mode = stat_mode(runner.jobs_root / f"{started['job_id']}.json")

    assert jobs_mode == 0o700
    assert log_mode == 0o600
    assert metadata_mode == 0o600


def stat_mode(path: Path) -> int:
    return os.stat(path).st_mode & 0o777


def test_multiline_passthrough_secret_is_fully_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "first-private-line-123\nsecond-private-line-456"
    monkeypatch.setenv("RUNNER_TEST_MULTI_SECRET", secret)
    runner, _, _ = make_runner(
        tmp_path,
        {
            "scrub": python_profile(
                "import os; print(os.environ['RUNNER_TEST_MULTI_SECRET'])",
                env_passthrough=["RUNNER_TEST_MULTI_SECRET"],
            )
        },
    )

    started = runner.start_test("demo", "scrub")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"])

    assert finished["status"] == "passed"
    assert "first-private-line-123" not in log["content"]
    assert "second-private-line-456" not in log["content"]
    assert log["content"].count("[REDACTED]") >= 2
