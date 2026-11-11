"""#341 local provisional baseline SHA custody; no host/signer/A7 qualification."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from runner_mcp.self_update import SelfUpdateError, SelfUpdateManager
from runner_mcp.self_update_install import (
    PackageInstallError,
    SelfUpdatePackageInstaller,
)

JOB = "a" * 32
BASELINE = "b" * 40
TARGET = "c" * 40


def _staged(tmp_path: Path) -> tuple[SelfUpdatePackageInstaller, Path]:
    installer = SelfUpdatePackageInstaller(
        config_dir=tmp_path, python_executable=Path(sys.executable)
    )
    stage = installer.artifacts_root / JOB / "baseline"
    stage.mkdir(parents=True)
    wheel = stage / "baseline.whl"
    wheel.write_bytes(b"independently untrusted but locally sealed wheel")
    return installer, wheel


def test_retained_wheel_digest_refuses_metadata_change_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ook bij identieke wheelbytes mag een nieuwe inodegeneratie niet slagen."""
    installer, wheel = _staged(tmp_path)
    wheel.chmod(0o644)
    original_file_digest = hashlib.file_digest

    def change_mode_after_hash(handle, algorithm):
        result = original_file_digest(handle, algorithm)
        # De bytes en mtime blijven gelijk. Alleen de metadata/ctime wijzigen.
        wheel.chmod(0o600)
        return result

    monkeypatch.setattr(
        "runner_mcp.self_update_install.hashlib.file_digest",
        change_mode_after_hash,
    )
    assert installer.staged_wheel_sha256(job_id=JOB, label="baseline") is None
    # De echte bytes zijn nog intact; de wijziging was enkel in mode/ctime.
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() is not None


def test_retained_wheel_digest_refuses_missing_nofollow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Zonder OS-bescherming tegen symlinks wordt geen digest uitgegeven."""
    installer, _wheel = _staged(tmp_path)
    monkeypatch.delattr(
        "runner_mcp.self_update_install.os.O_NOFOLLOW", raising=False,
    )
    assert installer.staged_wheel_sha256(job_id=JOB, label="baseline") is None


def test_new_transaction_pins_staged_wheel_and_detects_same_path_tamper(
    tmp_path: Path,
) -> None:
    installer, wheel = _staged(tmp_path)
    digest = installer.staged_wheel_sha256(job_id=JOB, label="baseline")
    assert digest is not None and len(digest) == 64
    installer.begin_transaction(
        job_id=JOB,
        target_commit=TARGET,
        baseline_commit=BASELINE,
        baseline_wheel_sha256=digest,
    )
    assert installer.pending_transaction()["baseline_wheel_sha256"] == digest
    assert installer.staged_wheel_sha256(job_id=JOB, label="baseline") == digest
    wheel.write_bytes(b"same path with changed contents")
    assert installer.staged_wheel_sha256(job_id=JOB, label="baseline") != digest
    assert installer.pending_transaction()["baseline_wheel_sha256"] == digest


@pytest.mark.parametrize("bad", ["F" * 64, "a" * 63, "", "not-a-digest"])
def test_invalid_baseline_digest_rejected_before_transaction_write(
    tmp_path: Path, bad: str
) -> None:
    installer, _wheel = _staged(tmp_path)
    with pytest.raises(PackageInstallError, match="digest"):
        installer.begin_transaction(
            job_id=JOB, target_commit=TARGET,
            baseline_commit=BASELINE, baseline_wheel_sha256=bad,
        )
    assert installer.pending_transaction() is None


def test_legacy_transaction_remains_readable_but_has_no_integrity_claim(
    tmp_path: Path,
) -> None:
    installer, _wheel = _staged(tmp_path)
    installer.begin_transaction(
        job_id=JOB, target_commit=TARGET, baseline_commit=BASELINE
    )
    transaction = installer.pending_transaction()
    assert transaction is not None
    assert "baseline_wheel_sha256" not in transaction
    # A malformed purportedly sealed transaction must fail closed.
    data = {**transaction, "baseline_wheel_sha256": "not-a-digest"}
    installer.transaction_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PackageInstallError, match="invalid"):
        installer.pending_transaction()


def test_manual_recovery_refuses_tampered_wheel_before_pip(
    tmp_path: Path,
) -> None:
    installer, wheel = _staged(tmp_path)
    digest = installer.staged_wheel_sha256(job_id=JOB, label="baseline")
    assert digest is not None
    installer.begin_transaction(
        job_id=JOB, target_commit=TARGET,
        baseline_commit=BASELINE, baseline_wheel_sha256=digest,
    )
    wheel.write_bytes(b"changed after durable seal")
    installer.install_wheel = Mock(side_effect=AssertionError("pip must not run"))

    manager = object.__new__(SelfUpdateManager)
    manager.config_dir = tmp_path
    manager._package_installer = installer
    manager.safety = SimpleNamespace(
        retention_confirmed=True,
        status=lambda: SimpleNamespace(configured=True, stop_active=True),
    )
    manager._project_config = lambda: SimpleNamespace(root=tmp_path)
    with pytest.raises(SelfUpdateError, match="recovery remains required"):
        manager.recover_installation()
    installer.install_wheel.assert_not_called()
    assert installer.pending_transaction()["baseline_wheel_sha256"] == digest
