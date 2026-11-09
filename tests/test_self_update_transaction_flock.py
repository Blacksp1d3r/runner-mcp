"""#341 — originele Runner-MCP install-recovery: één lock én juiste jobhouder.

Deze tests gebruiken alleen een tijdelijke owner-map, echte lokale flock en
optioneel een onafhankelijk Python-kindproces. Er wordt geen echte package
geïnstalleerd of dienst gestart. A6/A7/SQL/Claude/Qwen blijven ongemoeid.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from runner_mcp.self_update_install import (
    PackageInstallError,
    SelfUpdatePackageInstaller,
    _exclusive_install_transaction_lock,
)

FIRST = "a" * 32
SECOND = "b" * 32
BASELINE = "c" * 40
TARGET = "d" * 40


def _installer(root: Path) -> SelfUpdatePackageInstaller:
    return SelfUpdatePackageInstaller(
        config_dir=root, python_executable=Path(sys.executable),
    )


def _begin(installer: SelfUpdatePackageInstaller, job_id: str) -> None:
    installer.begin_transaction(
        job_id=job_id, target_commit=TARGET,
        baseline_commit=BASELINE,
    )


def test_wrong_job_must_not_remove_existing_rollback_transaction(tmp_path: Path) -> None:
    installer = _installer(tmp_path)
    _begin(installer, FIRST)
    before = installer.transaction_path.read_bytes()
    with pytest.raises(PackageInstallError, match="owner mismatch"):
        installer.clear_transaction(job_id=SECOND)
    assert installer.transaction_path.read_bytes() == before
    assert installer.pending_transaction()["job_id"] == FIRST
    installer.clear_transaction(job_id=FIRST)
    assert installer.pending_transaction() is None


def test_stale_clearer_cannot_delete_new_job_after_old_job_finished(tmp_path: Path) -> None:
    """De twee voormalige afsluiters mogen geen nieuwe generatie verwijderen."""
    first = _installer(tmp_path)
    second = _installer(tmp_path)
    _begin(first, FIRST)
    first.clear_transaction(job_id=FIRST)
    _begin(second, SECOND)
    prior = second.transaction_path.read_bytes()
    with pytest.raises(PackageInstallError, match="owner mismatch"):
        first.clear_transaction(job_id=FIRST)
    assert second.pending_transaction()["job_id"] == SECOND
    assert second.transaction_path.read_bytes() == prior
    second.clear_transaction(job_id=SECOND)


def test_begin_and_clear_share_same_exclusive_kernel_lock(tmp_path: Path) -> None:
    """Twee onafhankelijke installerobjecten mogen niet tussendoor publiceren."""
    owner = _installer(tmp_path)
    other = _installer(tmp_path)
    with _exclusive_install_transaction_lock(owner.transaction_path):
        with pytest.raises(PackageInstallError, match="lock is unavailable"):
            _begin(other, FIRST)
        with pytest.raises(PackageInstallError, match="lock is unavailable"):
            other.clear_transaction(job_id=FIRST)
    assert owner.pending_transaction() is None
    _begin(owner, FIRST)
    owner.clear_transaction(job_id=FIRST)


@pytest.mark.parametrize("bad", ["symlink", "mode", "hardlink"])
def test_unsafe_or_aliased_lock_fails_closed(
    tmp_path: Path, bad: str,
) -> None:
    installer = _installer(tmp_path)
    lock = installer.transaction_path.with_name(
        installer.transaction_path.name + ".lock"
    )
    if bad == "symlink":
        lock.symlink_to(tmp_path / "missing")
    else:
        lock.write_bytes(b"")
        lock.chmod(0o600)
        if bad == "mode":
            lock.chmod(0o644)
        else:
            os.link(lock, tmp_path / "foreign-alias")
    with pytest.raises(PackageInstallError, match="lock"):
        _begin(installer, FIRST)
    assert installer.pending_transaction() is None


def test_missing_flock_primitive_must_not_fall_back_to_unlocked_write(
    tmp_path: Path,
) -> None:
    installer = _installer(tmp_path)
    with patch(
        "runner_mcp.self_update_install.fcntl.flock",
        side_effect=OSError("synthetic missing kernel lock"),
    ):
        with pytest.raises(PackageInstallError, match="lock is unavailable"):
            _begin(installer, FIRST)
    assert installer.pending_transaction() is None


@pytest.mark.parametrize("wrong", ["", "not-hex", "f" * 31, None, 4, False])
def test_clear_requires_real_exact_job_id(
    tmp_path: Path, wrong: object,
) -> None:
    installer = _installer(tmp_path)
    _begin(installer, FIRST)
    original = installer.transaction_path.read_bytes()
    with pytest.raises(PackageInstallError, match="job identifier"):
        installer.clear_transaction(job_id=wrong)
    assert installer.transaction_path.read_bytes() == original


def test_previous_process_exits_without_leaving_stale_flock(tmp_path: Path) -> None:
    """De OS-kernel geeft een vergrendeling vrij na procesverlies/herstart."""
    installer = _installer(tmp_path)
    command = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; "
            "from runner_mcp.self_update_install import "
            "_exclusive_install_transaction_lock; "
            "root = Path(__import__('sys').argv[1]); "
            "ctx = _exclusive_install_transaction_lock(root); "
            "ctx.__enter__(); "
            "assert root.with_name(root.name+'.lock').is_file()"
        ),
        str(installer.transaction_path),
    ]
    result = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr[-400:]
    lock = installer.transaction_path.with_name(
        installer.transaction_path.name + ".lock"
    )
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600
    _begin(installer, FIRST)
    assert installer.pending_transaction()["job_id"] == FIRST
    installer.clear_transaction(job_id=FIRST)
