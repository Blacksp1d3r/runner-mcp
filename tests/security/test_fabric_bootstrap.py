from __future__ import annotations

import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.fabric_bootstrap import (
    FabricBootstrapError,
    FabricBootstrapJob,
    FabricBootstrapManager,
    FabricBootstrapState,
)
from runner_mcp.onboarding import SetupAnswers, install_private_configuration
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy

COMMIT = "d" * 40
TOKEN = "g" * 48


def private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "private"
    paths = install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"RUNNER_MCP_GITHUB_TOKEN={TOKEN}\n")
    return paths


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def healthy_self_update_status() -> dict[str, object]:
    return {
        "active_update": False,
        "restart_pending": False,
        "install_recovery_pending": False,
    }


class FakeRunner:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.calls: list[tuple[list[str], dict]] = []
        self.fail_on = fail_on

    def __call__(self, command, **kwargs):
        argv = list(command)
        self.calls.append((argv, dict(kwargs)))
        joined = " ".join(argv)
        if self.fail_on and self.fail_on in joined:
            return subprocess.CompletedProcess(argv, 1, "", "private failure detail")

        if argv[:2] == ["git", "clone"]:
            source = Path(argv[-1])
            source.mkdir(parents=True)
        elif "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, COMMIT + "\n", "")
        elif "status" in argv and "--porcelain" in argv:
            return subprocess.CompletedProcess(argv, 0, "", "")
        elif len(argv) >= 4 and argv[1:4] == ["-m", "pip", "wheel"]:
            wheel_dir = Path(argv[argv.index("--wheel-dir") + 1])
            wheel_dir.mkdir(parents=True, exist_ok=True)
            (wheel_dir / "runner_fabric-0.0.1-py3-none-any.whl").write_bytes(
                b"wheel"
            )
        elif len(argv) >= 4 and argv[1:4] == ["-m", "pip", "install"]:
            target = Path(argv[argv.index("--target") + 1])
            package = target / "runner_fabric"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text(
                '__version__ = "0.0.1"\n',
                encoding="utf-8",
            )

        return subprocess.CompletedProcess(argv, 0, "", "")


def manager(
    tmp_path: Path,
    runner: FakeRunner,
    *,
    self_update_status_provider=healthy_self_update_status,
) -> tuple[FabricBootstrapManager, Path]:
    paths = private_config(tmp_path)
    data_root = tmp_path / "local" / "share" / "runner-fabric"
    result = FabricBootstrapManager(
        config_dir=paths.config_dir.resolve(),
        safety=safety(tmp_path),
        runner=runner,
        data_root=data_root,
        self_update_status_provider=self_update_status_provider,
    )
    return result, paths.config_dir


def wait_terminal(
    bootstrap: FabricBootstrapManager,
    job_id: str,
) -> dict[str, object]:
    for _ in range(200):
        status = bootstrap.status(job_id)
        if status["state"] in {
            "completed",
            "error",
            "stopped",
            "interrupted",
        }:
            return status
        time.sleep(0.005)
    raise AssertionError("bootstrap job did not finish")


def test_runtime_preflight_is_fixed_and_runs_before_git(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)

    started = bootstrap.start(COMMIT)
    assert wait_terminal(bootstrap, started["job_id"])["state"] == "completed"

    assert fake.calls[0][0][1:] == ["-m", "pip", "--version"]
    assert fake.calls[1][0][1:] == ["-c", "import setuptools.build_meta"]
    assert fake.calls[2][0][1:] == [
        "-c",
        "import mcp; import pydantic; import starlette; import uvicorn",
    ]
    assert fake.calls[3][0][:2] == ["git", "clone"]
    for _argv, kwargs in fake.calls[:3]:
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == 15
        assert kwargs["env"]["PIP_NO_INDEX"] == "1"
        assert kwargs["env"]["PYTHONNOUSERSITE"] == "1"


@pytest.mark.parametrize(
    ("state_key", "category"),
    [
        ("active_update", "runner_mcp_self_update_active"),
        ("restart_pending", "runner_mcp_restart_pending"),
        ("install_recovery_pending", "runner_mcp_install_recovery_pending"),
    ],
)
def test_runner_mcp_state_blocks_bootstrap_before_subprocess(
    tmp_path: Path,
    state_key: str,
    category: str,
) -> None:
    fake = FakeRunner()
    state = healthy_self_update_status()
    state[state_key] = True
    bootstrap, _config_dir = manager(
        tmp_path,
        fake,
        self_update_status_provider=lambda: state,
    )

    with pytest.raises(FabricBootstrapError, match=category):
        bootstrap.start(COMMIT)

    assert fake.calls == []


def test_unavailable_runner_mcp_state_fails_closed_before_subprocess(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()

    def unavailable():
        raise RuntimeError("private self-update state detail")

    bootstrap, _config_dir = manager(
        tmp_path,
        fake,
        self_update_status_provider=unavailable,
    )

    with pytest.raises(FabricBootstrapError) as captured:
        bootstrap.start(COMMIT)

    assert str(captured.value) == "runner_mcp_state_unavailable"
    assert "private" not in str(captured.value)
    assert fake.calls == []


@pytest.mark.parametrize(
    ("failure_marker", "category"),
    [
        ("pip --version", "pip_unavailable"),
        ("setuptools.build_meta", "build_backend_unavailable"),
        ("import mcp", "runtime_dependency_unavailable"),
    ],
)
def test_runtime_preflight_failure_is_bounded_before_git(
    tmp_path: Path,
    failure_marker: str,
    category: str,
) -> None:
    fake = FakeRunner(fail_on=failure_marker)
    bootstrap, _config_dir = manager(tmp_path, fake)

    with pytest.raises(FabricBootstrapError) as captured:
        bootstrap.start(COMMIT)

    assert str(captured.value) == category
    assert all(argv[:2] != ["git", "clone"] for argv, _kwargs in fake.calls)
    assert bootstrap.installed_commit() is None
    assert not list(bootstrap.jobs_root.glob("*.json"))


def test_bootstrap_installs_exact_canonical_commit_without_token_in_argv_or_env(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()
    bootstrap, config_dir = manager(tmp_path, fake)

    started = bootstrap.start(COMMIT)
    result = wait_terminal(bootstrap, started["job_id"])

    assert result["state"] == "completed"
    assert result["commit"] == COMMIT
    assert result["error_category"] is None
    assert bootstrap.installed_commit() == COMMIT
    assert bootstrap.current_link.is_symlink()
    assert bootstrap.launcher.is_symlink()
    assert bootstrap.launcher.resolve().name == "runner-fabric"

    clone = next(call for call in fake.calls if call[0][:2] == ["git", "clone"])
    assert "https://github.com/Blacksp1d3r/Runner-Fabric.git" in clone[0]

    for argv, kwargs in fake.calls:
        rendered = " ".join(argv)
        assert TOKEN not in rendered
        assert TOKEN not in repr(kwargs.get("env", {}))
        assert "--shell" not in argv
        assert kwargs["shell"] is False

    assert not list(bootstrap.jobs_root.glob(".work-*"))
    assert (config_dir / "fabric-bootstrap-state.json").stat().st_mode & 0o777 == 0o600
    assert (bootstrap.jobs_root / f"{started['job_id']}.json").stat().st_mode & 0o777 == 0o600


def test_bootstrap_failure_never_activates_unverified_release(tmp_path: Path) -> None:
    fake = FakeRunner(fail_on="pip wheel")
    bootstrap, _config_dir = manager(tmp_path, fake)

    started = bootstrap.start(COMMIT)
    result = wait_terminal(bootstrap, started["job_id"])

    assert result["state"] == "error"
    assert result["error_category"] == "build_failed"
    assert bootstrap.installed_commit() is None
    assert not bootstrap.current_link.exists()
    assert not bootstrap.launcher.exists()


def test_bootstrap_is_blocked_by_operator_stop(tmp_path: Path) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)
    stop_file = bootstrap.safety.stop_file
    assert stop_file is not None
    stop_file.write_text("stop\n", encoding="utf-8")

    with pytest.raises(FabricBootstrapError, match="emergency stop"):
        bootstrap.start(COMMIT)

    assert fake.calls == []


def test_different_installed_commit_fails_before_subprocess(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)
    first = bootstrap.start(COMMIT)
    assert wait_terminal(bootstrap, first["job_id"])["state"] == "completed"
    call_count = len(fake.calls)

    with pytest.raises(FabricBootstrapError) as captured:
        bootstrap.start("e" * 40)

    assert str(captured.value) == "already_installed_conflict"
    assert len(fake.calls) == call_count


def test_unmanaged_launcher_conflict_fails_before_preflight(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)
    bootstrap.launcher.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    bootstrap.launcher.write_text("unmanaged\n", encoding="utf-8")

    with pytest.raises(FabricBootstrapError) as captured:
        bootstrap.start(COMMIT)

    assert str(captured.value) == "already_installed_conflict"
    assert fake.calls == []


def test_matching_installed_commit_is_idempotent(tmp_path: Path) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)
    first = bootstrap.start(COMMIT)
    assert wait_terminal(bootstrap, first["job_id"])["state"] == "completed"
    call_count = len(fake.calls)

    second = bootstrap.start(COMMIT)

    assert second["state"] == "completed"
    assert second["already_installed"] is True
    assert len(fake.calls) == call_count


def test_restart_marks_queued_bootstrap_interrupted_without_reexecution(
    tmp_path: Path,
) -> None:
    fake = FakeRunner()
    bootstrap, config_dir = manager(tmp_path, fake)
    job = FabricBootstrapJob(
        job_id="a" * 32,
        commit=COMMIT,
        state=FabricBootstrapState.QUEUED,
        created_at=datetime.now(UTC),
    )
    bootstrap._persist(job)

    restarted = FabricBootstrapManager(
        config_dir=config_dir.resolve(),
        safety=safety(tmp_path),
        runner=fake,
        data_root=bootstrap.data_root,
    )

    status = restarted.status("a" * 32)
    assert status["state"] == "interrupted"
    assert status["error_category"] == "runner_restart"
    assert fake.calls == []


def test_invalid_commit_fails_before_worker_start(tmp_path: Path) -> None:
    fake = FakeRunner()
    bootstrap, _config_dir = manager(tmp_path, fake)

    for value in ("main", "D" * 40, "../" + "d" * 37):
        with pytest.raises(FabricBootstrapError, match="lowercase commit"):
            bootstrap.start(value)

    assert fake.calls == []
