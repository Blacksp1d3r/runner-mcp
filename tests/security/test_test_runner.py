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


def make_registry(
    root: Path,
    profiles: dict[str, RunnerTestProfile],
    *,
    max_parallel_tests: int = 1,
    max_queued_tests: int = 16,
) -> ProjectRegistry:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=root,
                test_profiles=profiles,
                max_parallel_tests=max_parallel_tests,
                max_queued_tests=max_queued_tests,
            )
        }
    )


def make_runner(
    tmp_path: Path,
    profiles: dict[str, RunnerTestProfile],
    *,
    max_concurrent_jobs: int = 2,
    max_queued_jobs: int = 64,
    max_parallel_tests: int = 1,
    max_queued_tests: int = 16,
    playwright_browsers_path: Path | None = None,
) -> tuple[Runner, Path, Path]:
    root = tmp_path / "project"
    stop_file = tmp_path / "operator.stop"
    guard = OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=make_registry(
            root,
            profiles,
            max_parallel_tests=max_parallel_tests,
            max_queued_tests=max_queued_tests,
        ),
        safety=guard,
        jobs_root=tmp_path / "jobs",
        playwright_browsers_path=playwright_browsers_path,
        max_concurrent_jobs=max_concurrent_jobs,
        max_queued_jobs=max_queued_jobs,
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
    runtime: str = "default",
    parallel_safe: bool = False,
) -> RunnerTestProfile:
    argv = [sys.executable, "-c", code]
    if extra_args:
        argv.extend(extra_args)
    return RunnerTestProfile(
        argv=argv,
        timeout_seconds=timeout_seconds,
        max_log_bytes=max_log_bytes,
        env_passthrough=env_passthrough or [],
        runtime=runtime,
        parallel_safe=parallel_safe,
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


def test_playwright_runtime_requires_configured_browser_cache(
    tmp_path: Path,
) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {
            "e2e": python_profile(
                "print('should not run')",
                runtime="playwright",
            )
        },
    )

    started = runner.start_test("demo", "e2e")
    finished = wait_terminal(runner, started["job_id"])

    assert finished["status"] == "error"
    assert finished["error_category"] == "execution_error"


def test_playwright_runtime_injects_and_scrubs_browser_cache(
    tmp_path: Path,
) -> None:
    browser_cache = tmp_path / "shared-browser-cache"
    browser_cache.mkdir()
    code = (
        "import os; "
        "print(os.environ['PLAYWRIGHT_BROWSERS_PATH']); "
        "print(os.environ['HOME'])"
    )
    runner, _, _ = make_runner(
        tmp_path,
        {
            "e2e": python_profile(
                code,
                runtime="playwright",
            )
        },
        playwright_browsers_path=browser_cache,
    )

    started = runner.start_test("demo", "e2e")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"])

    assert finished["status"] == "passed"
    assert str(browser_cache) not in log["content"]
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
        max_concurrent_jobs=2,
    )

    first = runner.start_test("demo", "slow")
    wait_running(runner, first["job_id"])
    second = runner.start_test("demo", "slow")
    second_status = runner.job_status(second["job_id"])

    assert second_status["status"] == "queued"
    assert second_status["waiting_reason"] in {
        "project_parallel_limit",
        "project_exclusive_test",
    }
    queue = runner.queue_status()
    demo = next(item for item in queue["projects"] if item["project"] == "demo")
    assert demo["project_lock_active"] is True

    runner.cancel(first["job_id"])
    runner.cancel(second["job_id"])
    wait_terminal(runner, first["job_id"])
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


def test_existing_running_metadata_fails_closed_after_restart(tmp_path: Path) -> None:
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


def test_job_uses_short_private_tmpdir_and_cleans_it(tmp_path: Path) -> None:
    long_root = tmp_path / ("nested-" + ("x" * 120))
    code = (
        "import os, pathlib, stat; "
        "p = pathlib.Path(os.environ['TMPDIR']); "
        "print(p.name); "
        "print(len(str(p))); "
        "print(oct(p.stat().st_mode & 0o777))"
    )
    runner, _, _ = make_runner(
        long_root,
        {"tmp": python_profile(code)},
    )

    started = runner.start_test("demo", "tmp")
    finished = wait_terminal(runner, started["job_id"])
    log = runner.get_log(started["job_id"])
    lines = log["content"].splitlines()

    assert finished["status"] == "passed"
    assert lines[0].startswith("runner-mcp-")
    assert int(lines[1]) < 80
    assert lines[2] == "0o700"
    temp_path = Path("/tmp") / lines[0]
    deadline = time.monotonic() + 1.0
    while temp_path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not temp_path.exists()


def test_two_projects_run_at_the_same_time(tmp_path: Path) -> None:
    roots = {"alpha": tmp_path / "alpha", "beta": tmp_path / "beta"}
    for root in roots.values():
        root.mkdir()
    profile = python_profile(
        "import time; print('start', flush=True); time.sleep(0.6)",
        parallel_safe=False,
    )
    registry = ProjectRegistry(
        projects={
            code: ProjectConfig(
                display_name=code.title(),
                repository=f"example/{code}",
                root=root,
                test_profiles={"slow": profile},
            )
            for code, root in roots.items()
        }
    )
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=registry,
        safety=guard,
        jobs_root=tmp_path / "jobs-parallel-projects",
        max_concurrent_jobs=2,
        poll_interval_seconds=0.02,
    )

    alpha = runner.start_test("alpha", "slow")
    beta = runner.start_test("beta", "slow")
    wait_running(runner, alpha["job_id"])
    wait_running(runner, beta["job_id"])

    status = runner.worker_status()
    assert status["running_jobs"] == 2
    assert status["available_workers"] == 0

    runner.cancel(alpha["job_id"])
    runner.cancel(beta["job_id"])
    wait_terminal(runner, alpha["job_id"])
    wait_terminal(runner, beta["job_id"])


def test_parallel_safe_profiles_can_overlap_within_one_project(tmp_path: Path) -> None:
    profiles = {
        "one": python_profile(
            "import time; time.sleep(0.6)",
            parallel_safe=True,
        ),
        "two": python_profile(
            "import time; time.sleep(0.6)",
            parallel_safe=True,
        ),
    }
    runner, _, _ = make_runner(
        tmp_path,
        profiles,
        max_concurrent_jobs=2,
        max_parallel_tests=2,
    )

    one = runner.start_test("demo", "one")
    two = runner.start_test("demo", "two")
    wait_running(runner, one["job_id"])
    wait_running(runner, two["job_id"])

    project = next(
        item for item in runner.queue_status()["projects"]
        if item["project"] == "demo"
    )
    assert project["running_jobs"] == 2
    assert project["project_lock_active"] is False

    runner.cancel(one["job_id"])
    runner.cancel(two["job_id"])
    wait_terminal(runner, one["job_id"])
    wait_terminal(runner, two["job_id"])


def test_unsafe_profile_remains_exclusive_even_with_project_capacity(tmp_path: Path) -> None:
    profiles = {
        "unsafe": python_profile("import time; time.sleep(30)"),
        "safe": python_profile(
            "import time; time.sleep(30)",
            parallel_safe=True,
        ),
    }
    runner, _, _ = make_runner(
        tmp_path,
        profiles,
        max_concurrent_jobs=2,
        max_parallel_tests=2,
    )

    first = runner.start_test("demo", "unsafe")
    wait_running(runner, first["job_id"])
    second = runner.start_test("demo", "safe")

    assert runner.job_status(second["job_id"])["status"] == "queued"
    assert runner.job_status(second["job_id"])["waiting_reason"] == "project_exclusive_test"

    runner.cancel(first["job_id"])
    runner.cancel(second["job_id"])
    wait_terminal(runner, first["job_id"])
    wait_terminal(runner, second["job_id"])


def test_queue_backpressure_is_bounded(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
        max_concurrent_jobs=1,
        max_queued_jobs=1,
        max_queued_tests=8,
    )

    running = runner.start_test("demo", "slow")
    wait_running(runner, running["job_id"])
    queued = runner.start_test("demo", "slow")
    with pytest.raises(RunnerError, match="queue capacity"):
        runner.start_test("demo", "slow")

    assert runner.queue_status()["queued_jobs"] == 1
    runner.cancel(running["job_id"])
    runner.cancel(queued["job_id"])
    wait_terminal(runner, running["job_id"])
    wait_terminal(runner, queued["job_id"])


def test_project_queue_backpressure_is_bounded(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
        max_concurrent_jobs=1,
        max_queued_jobs=8,
        max_queued_tests=1,
    )

    running = runner.start_test("demo", "slow")
    wait_running(runner, running["job_id"])
    queued = runner.start_test("demo", "slow")

    with pytest.raises(RunnerError, match="Project test queue capacity"):
        runner.start_test("demo", "slow")

    assert runner.job_status(queued["job_id"])["status"] == "queued"
    runner.cancel(running["job_id"])
    runner.cancel(queued["job_id"])
    wait_terminal(runner, running["job_id"])
    wait_terminal(runner, queued["job_id"])


def test_fair_round_robin_prevents_project_monopoly(tmp_path: Path) -> None:
    roots = {"alpha": tmp_path / "fair-alpha", "beta": tmp_path / "fair-beta"}
    for root in roots.values():
        root.mkdir()
    profile = python_profile("import time; time.sleep(0.12)")
    registry = ProjectRegistry(
        projects={
            code: ProjectConfig(
                display_name=code.title(),
                repository=f"example/{code}",
                root=root,
                test_profiles={"short": profile},
                max_queued_tests=16,
            )
            for code, root in roots.items()
        }
    )
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "fair-stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=registry,
        safety=guard,
        jobs_root=tmp_path / "fair-jobs",
        max_concurrent_jobs=1,
        poll_interval_seconds=0.01,
    )

    a1 = runner.start_test("alpha", "short")
    wait_running(runner, a1["job_id"])
    a2 = runner.start_test("alpha", "short")
    a3 = runner.start_test("alpha", "short")
    b1 = runner.start_test("beta", "short")

    b_finished = wait_terminal(runner, b1["job_id"], timeout=4)
    a3_finished = wait_terminal(runner, a3["job_id"], timeout=4)

    assert b_finished["finished_at"] <= a3_finished["finished_at"]
    assert wait_terminal(runner, a2["job_id"], timeout=4)["status"] == "passed"


def test_queued_job_is_resumed_after_runner_restart(tmp_path: Path) -> None:
    jobs_root = tmp_path / "resume-jobs"
    jobs_root.mkdir()
    job_id = "b" * 32
    metadata = {
        "job_id": job_id,
        "project": "demo",
        "suite": "resume",
        "status": "queued",
        "created_at": "2026-09-20T00:00:00+00:00",
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "log_truncated": False,
        "error_category": None,
    }
    (jobs_root / f"{job_id}.json").write_text(json.dumps(metadata), encoding="utf-8")
    root = tmp_path / "resume-project"
    profile = python_profile("print('resumed')")
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "resume-stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = Runner(
        registry=make_registry(root, {"resume": profile}),
        safety=guard,
        jobs_root=jobs_root,
        max_concurrent_jobs=1,
        poll_interval_seconds=0.01,
    )

    finished = wait_terminal(runner, job_id, timeout=3)
    assert finished["status"] == "passed"
    assert "resumed" in runner.get_log(job_id)["content"]


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



def test_safe_python_adapter_presets_are_available_without_private_profile_config(
    tmp_path: Path,
) -> None:
    runner, root, _ = make_runner(tmp_path, {})
    runner.registry.projects["demo"].adapter = "python"
    bin_dir = root / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    python = bin_dir / "python"
    python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python.chmod(0o755)
    ruff = bin_dir / "ruff"
    ruff.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    ruff.chmod(0o755)

    names = {item["name"] for item in runner.list_profiles("demo")}
    assert {"pytest", "ruff"} <= names

    pytest_job = runner.start_test("demo", "pytest")
    assert wait_terminal(runner, pytest_job["job_id"])["status"] == "passed"
    ruff_job = runner.start_test("demo", "ruff")
    assert wait_terminal(runner, ruff_job["job_id"])["status"] == "passed"


def test_custom_adapter_preset_is_never_implicitly_exposed(tmp_path: Path) -> None:
    runner, root, _ = make_runner(tmp_path, {})
    runner.registry.projects["demo"].adapter = "python"
    bin_dir = root / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    python = bin_dir / "python"
    python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python.chmod(0o755)

    names = {item["name"] for item in runner.list_profiles("demo")}
    assert "pytest" in names
    assert "custom" not in names
    with pytest.raises(RunnerError, match="Unknown or disabled test profile"):
        runner.start_test("demo", "custom")


def test_project_has_work_tracks_queued_or_active_tests(tmp_path: Path) -> None:
    runner, _, _ = make_runner(
        tmp_path,
        {"slow": python_profile("import time; time.sleep(30)")},
        max_concurrent_jobs=1,
    )
    assert runner.project_has_work("demo") is False

    job = runner.start_test("demo", "slow")
    wait_running(runner, job["job_id"])
    assert runner.project_has_work("demo") is True

    runner.cancel(job["job_id"])
    wait_terminal(runner, job["job_id"])
    assert runner.project_has_work("demo") is False
