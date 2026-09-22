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
        wheel_dir = Path(command[command.index("--wheel-dir") + 1])
        (wheel_dir / "runner_mcp-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0, "", "")

    installer = make_installer(tmp_path, runner=runner)
    wheel = installer.build_wheel(
        source_root=source,
        job_id="d" * 32,
        label="target",
    )

    command, kwargs = calls[0]
    assert command[1:4] == ["-m", "pip", "wheel"]
    assert "--no-deps" in command
    assert "--no-build-isolation" in command
    assert kwargs["shell"] is False
    assert kwargs["env"]["PIP_NO_INDEX"] == "1"
    assert stat.S_IMODE(wheel.stat().st_mode) == 0o600


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
