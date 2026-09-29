from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from runner_mcp.self_update_install import (
    PackageInstallError,
    SelfUpdatePackageInstaller,
    install_recovery_state,
)


def make_installer(tmp_path: Path, runner=subprocess.run) -> SelfUpdatePackageInstaller:
    config = tmp_path / "config"
    config.mkdir()
    return SelfUpdatePackageInstaller(
        config_dir=config,
        python_executable=Path(sys.executable),
        runner=runner,
    )


def test_transaction_is_private_and_strict(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    job_id = "a" * 32
    target = "b" * 40
    baseline = "c" * 40

    installer.begin_transaction(
        job_id=job_id,
        target_commit=target,
        baseline_commit=baseline,
    )

    transaction = installer.pending_transaction()
    assert transaction == {
        "job_id": job_id,
        "target_commit": target,
        "baseline_commit": baseline,
        "rollback_capable": True,
    }
    assert stat.S_IMODE(installer.transaction_path.stat().st_mode) == 0o600

    installer.clear_transaction()
    assert installer.pending_transaction() is None


def test_transaction_fsyncs_file_and_parent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installer = make_installer(tmp_path)
    observed: list[str] = []
    real_fsync = os.fsync

    def tracking_fsync(fd: int) -> None:
        mode = os.fstat(fd).st_mode
        if stat.S_ISREG(mode):
            observed.append("file")
        elif stat.S_ISDIR(mode):
            observed.append("directory")
        else:
            observed.append("other")
        real_fsync(fd)

    monkeypatch.setattr("runner_mcp.self_update_install.os.fsync", tracking_fsync)

    installer.begin_transaction(
        job_id="a" * 32,
        target_commit="b" * 40,
        baseline_commit="c" * 40,
    )

    assert observed == ["file", "directory"]


def test_transaction_symlink_fails_closed(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    target = tmp_path / "outside"
    target.write_text("{}", encoding="utf-8")
    installer.transaction_path.symlink_to(target)

    with pytest.raises(PackageInstallError, match="unsafe"):
        installer.pending_transaction()


def test_build_wheel_uses_fixed_offline_arguments(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict]] = []
    source = tmp_path / "source"
    source.mkdir()

    def runner(command, **kwargs):
        calls.append((list(command), dict(kwargs)))
        if "--wheel-dir" in command:
            wheel_dir = Path(command[command.index("--wheel-dir") + 1])
            (wheel_dir / "runner_mcp-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    wheel = installer.build_wheel(
        source_root=source,
        job_id="d" * 32,
        label="target",
    )

    assert [call[0][1:] for call in calls[:2]] == [
        ["-m", "pip", "--version"],
        ["-c", "import setuptools.build_meta"],
    ]
    command, kwargs = calls[2]
    assert command[1:4] == ["-m", "pip", "wheel"]
    assert "--no-deps" in command
    assert "--no-build-isolation" in command
    for _preflight_command, preflight_kwargs in calls[:2]:
        assert preflight_kwargs["shell"] is False
        assert preflight_kwargs["timeout"] == 30
        assert preflight_kwargs["env"]["PIP_NO_INDEX"] == "1"
    assert kwargs["shell"] is False
    assert kwargs["env"]["PIP_NO_INDEX"] == "1"
    assert stat.S_IMODE(wheel.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    ("stderr", "category"),
    [
        ("python: No module named pip", "pip_unavailable"),
        ("BackendUnavailable: Cannot import 'setuptools.build_meta'", "build_backend_unavailable"),
        ("error: invalid command 'bdist_wheel'", "build_tooling_incompatible"),
        ("Permission denied: private path", "permission_denied"),
        ("No space left on device: private path", "storage_exhausted"),
        ("invalid pyproject.toml configuration error: private detail", "invalid_project_metadata"),
        ("private unknown build failure", "unknown"),
    ],
)
def test_wheel_failure_is_safely_classified(
    tmp_path: Path,
    stderr: str,
    category: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()

    def runner(command, **kwargs):
        if command[1:] in (
            ["-m", "pip", "--version"],
            ["-c", "import setuptools.build_meta"],
        ):
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 1, "private stdout", stderr)

    installer = make_installer(tmp_path, runner=runner)

    with pytest.raises(PackageInstallError) as exc_info:
        installer.build_wheel(
            source_root=source,
            job_id="7" * 32,
            label="target",
        )

    assert str(exc_info.value) == f"Runner MCP wheel staging failed ({category})"
    assert "private" not in str(exc_info.value)

@pytest.mark.parametrize(
    ("failed_check", "category"),
    [
        ("pip", "pip_unavailable"),
        ("setuptools", "build_backend_unavailable"),
    ],
)
def test_packaging_preflight_fails_before_job_stage_or_transaction(
    tmp_path: Path,
    failed_check: str,
    category: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    sensitive = str(tmp_path / "private-runtime-detail")
    calls: list[list[str]] = []

    def runner(command, **kwargs):
        calls.append(list(command))
        if (
            failed_check == "pip"
            and command[1:] == ["-m", "pip", "--version"]
        ) or (
            failed_check == "setuptools"
            and command[1:] == ["-c", "import setuptools.build_meta"]
        ):
            return subprocess.CompletedProcess(
                command,
                1,
                "private stdout",
                sensitive,
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    job_id = "6" * 32

    with pytest.raises(PackageInstallError) as captured:
        installer.build_wheel(
            source_root=source,
            job_id=job_id,
            label="target",
        )

    assert str(captured.value) == (
        f"Runner MCP wheel staging failed ({category})"
    )
    assert sensitive not in str(captured.value)
    assert not (installer.artifacts_root / job_id).exists()
    assert installer.pending_transaction() is None
    assert all("--wheel-dir" not in command for command in calls)


def test_packaging_preflight_subprocess_error_is_bounded_and_non_mutating(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    sensitive = str(tmp_path / "private-python-error")

    def runner(command, **kwargs):
        raise OSError(sensitive)

    installer = make_installer(tmp_path, runner=runner)
    job_id = "5" * 32

    with pytest.raises(PackageInstallError) as captured:
        installer.build_wheel(
            source_root=source,
            job_id=job_id,
            label="baseline",
        )

    assert str(captured.value) == (
        "Runner MCP wheel staging failed (pip_unavailable)"
    )
    assert sensitive not in str(captured.value)
    assert not (installer.artifacts_root / job_id).exists()
    assert installer.pending_transaction() is None


def test_packaging_preflight_runs_before_any_wheel_stage_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    job_id = "4" * 32
    observed: list[tuple[list[str], bool]] = []
    installer_holder: dict[str, SelfUpdatePackageInstaller] = {}

    def runner(command, **kwargs):
        installer = installer_holder["installer"]
        observed.append(
            (
                list(command),
                (installer.artifacts_root / job_id).exists(),
            )
        )
        if "--wheel-dir" in command:
            wheel_dir = Path(command[command.index("--wheel-dir") + 1])
            (wheel_dir / "runner_mcp-0.1.0-py3-none-any.whl").write_bytes(
                b"wheel"
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    installer_holder["installer"] = installer

    installer.build_wheel(
        source_root=source,
        job_id=job_id,
        label="target",
    )

    assert observed[0][0][1:] == ["-m", "pip", "--version"]
    assert observed[1][0][1:] == ["-c", "import setuptools.build_meta"]
    assert observed[0][1] is False
    assert observed[1][1] is False
    assert observed[2][1] is True


def test_runtime_verification_uses_fixed_python_import(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict]] = []

    def runner(command, **kwargs):
        calls.append((list(command), dict(kwargs)))
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    installer.verify_runtime()

    command, kwargs = calls[0]
    assert command[1] == "-c"
    assert command[2] == "import runner_mcp; import runner_mcp.self_update"
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == 60


def test_install_rejects_wheel_outside_private_artifacts(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    outside = tmp_path / "outside.whl"
    outside.write_bytes(b"wheel")

    with pytest.raises(PackageInstallError, match="unsafe"):
        installer.install_wheel(outside)


def test_real_project_wheel_can_stage_without_index(tmp_path: Path) -> None:
    try:
        import setuptools.build_meta  # noqa: F401
    except ImportError:
        pytest.skip("test interpreter has no setuptools build backend")

    installer = make_installer(tmp_path)
    repository_root = Path(__file__).resolve().parents[2]

    wheel = installer.build_wheel(
        source_root=repository_root,
        job_id="e" * 32,
        label="target",
    )

    assert wheel.is_file()
    assert wheel.suffix == ".whl"
    assert stat.S_IMODE(wheel.stat().st_mode) == 0o600
    installer.cleanup_job("e" * 32)
    assert not wheel.exists()


def test_cleanup_rejects_symlinked_job_root(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    job_root = installer.artifacts_root / ("f" * 32)
    job_root.symlink_to(outside)

    with pytest.raises(PackageInstallError, match="unsafe"):
        installer.cleanup_job("f" * 32)

    assert os.path.isdir(outside)


def test_staged_wheel_returns_only_private_named_stage(tmp_path: Path) -> None:
    def runner(command, **kwargs):
        if "--wheel-dir" in command:
            wheel_dir = Path(command[command.index("--wheel-dir") + 1])
            (wheel_dir / "runner_mcp-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    source = tmp_path / "source"
    source.mkdir()
    built = installer.build_wheel(
        source_root=source,
        job_id="1" * 32,
        label="baseline",
    )

    recovered = installer.staged_wheel(job_id="1" * 32, label="baseline")

    assert recovered == built
    assert recovered.is_relative_to(installer.artifacts_root)


def test_staged_wheel_rejects_symlinked_stage(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    job_root = installer.artifacts_root / ("2" * 32)
    job_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (job_root / "baseline").symlink_to(outside)

    with pytest.raises(PackageInstallError, match="unsafe"):
        installer.staged_wheel(job_id="2" * 32, label="baseline")

def test_install_recovery_state_is_safe_and_bounded(tmp_path: Path) -> None:
    installer = make_installer(tmp_path)
    assert install_recovery_state(installer.transaction_path.parent) == "clear"

    installer.begin_transaction(
        job_id="9" * 32,
        target_commit="8" * 40,
        baseline_commit="7" * 40,
    )
    assert install_recovery_state(installer.transaction_path.parent) == "pending"

    installer.transaction_path.write_text("{", encoding="utf-8")
    assert install_recovery_state(installer.transaction_path.parent) == "invalid"
