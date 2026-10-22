"""#669 initial-install original wheel receipt, never serving-process attestation."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path

import pytest

from runner_mcp.artifact_receipt_capture import (
    WheelReceiptCaptureError,
    WheelReceiptPublicationUncertain,
    capture_candidate_wheel_receipt,
)
from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight

_REV = "a" * 40


def fixture(tmp_path: Path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    pkg = root / "runner_mcp"
    pkg.mkdir(mode=0o700)
    (pkg / "__init__.py").write_bytes(b'__version__ = "0.1.78"\n')
    (pkg / "core.py").write_bytes(b"def value():\n    return 42\n")
    wheel = root / "candidate.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in ("__init__.py", "core.py"):
            archive.writestr("runner_mcp/" + name, (pkg / name).read_bytes())
        archive.writestr("aifordable_runner_mcp-0.1.78.dist-info/WHEEL", "Wheel-Version: 1.0\n")
    wheel.chmod(0o600)
    return wheel, pkg, root / "receipt.json"


def capture(wheel, pkg, receipt, revision=_REV):
    return capture_candidate_wheel_receipt(
        wheel=wheel, installed_package=pkg,
        receipt=receipt, source_revision=revision,
    )


def test_exact_original_wheel_produces_private_non_authoritative_receipt(
    tmp_path: Path,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    result = capture(wheel, pkg, receipt)
    assert result["state"] == "retained_original_wheel_modules_match"
    assert result["active_build_provenance_verified"] is False
    assert result["original_client_ack_proven"] is False
    assert result["update_authorized"] is False
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    raw = json.loads(receipt.read_text())
    assert raw["wheel_sha256"] == hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert raw["source_revision"] == _REV
    assert set(raw["modules"]) == {"__init__.py", "core.py"}
    assert offline_artifact_receipt_preflight(
        receipt, wheel, pkg,
    )["state"] == "offline_bytes_match"
    assert offline_artifact_receipt_preflight(
        receipt, wheel, pkg,
    )["active_build_provenance_verified"] is False


def test_read_only_recheck_detects_post_capture_mutation(tmp_path: Path) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    capture(wheel, pkg, receipt)
    (pkg / "core.py").write_bytes(b"tampered on disk")
    result = offline_artifact_receipt_preflight(receipt, wheel, pkg)
    assert result["state"] == "unverified"


def test_fail_does_not_leave_stale_receipt_when_installed_files_mismatch(
    tmp_path: Path,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    (pkg / "core.py").write_bytes(b"old process generation")
    with pytest.raises(WheelReceiptCaptureError, match="installed modules differ"):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()


def test_existing_receipt_cannot_be_replaced_even_with_other_wheel(
    tmp_path: Path,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    capture(wheel, pkg, receipt)
    original = receipt.read_bytes()
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert receipt.read_bytes() == original


def test_symlinked_wheel_and_receipt_parent_are_rejected(
    tmp_path: Path,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    alias = wheel.parent / "wheel-alias.whl"
    alias.symlink_to(wheel)
    with pytest.raises(WheelReceiptCaptureError):
        capture(alias, pkg, receipt)
    linked = tmp_path / "alias"
    linked.symlink_to(wheel.parent, target_is_directory=True)
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, linked / "receipt.json")
    assert not receipt.exists()


def test_incomplete_or_invalid_source_does_not_create_receipt(tmp_path: Path) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt, "historical-marker-not-revision")
    assert not receipt.exists()


@pytest.mark.parametrize("bad_member", [
    "../bad.py",
    "runner_mcp/../../escape.py",
    "runner_mcp/evil.so",
])
def test_invalid_wheel_members_fail_closed(
    tmp_path: Path, bad_member: str,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr(bad_member, "unsafe")
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()


def test_missing_package_module_fails_without_partial_receipt(
    tmp_path: Path,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    (pkg / "extra.py").write_text("extra = True")
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()


def test_corrupt_wheel_cannot_create_receipt(tmp_path: Path) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    wheel.write_bytes(b"not a wheel" * 15)
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()


def test_private_parent_required(tmp_path: Path) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    receipt.parent.chmod(0o755)
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()


def test_directory_fsync_failure_keeps_receipt_for_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)
    real_fsync = os.fsync
    calls = 0

    def fail_directory_sync(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic parent directory sync failure")
        real_fsync(fd)

    monkeypatch.setattr("runner_mcp.artifact_receipt_capture.os.fsync", fail_directory_sync)
    with pytest.raises(
        WheelReceiptPublicationUncertain, match="requires reconciliation"
    ):
        capture(wheel, pkg, receipt)

    assert calls == 2
    assert receipt.is_file()
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    assert offline_artifact_receipt_preflight(
        receipt, wheel, pkg,
    )["state"] == "offline_bytes_match"
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert receipt.is_file()


def test_file_fsync_failure_cleans_unvalidated_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel, pkg, receipt = fixture(tmp_path)

    def fail_file_sync(_fd: int) -> None:
        raise OSError("synthetic file sync failure")

    monkeypatch.setattr("runner_mcp.artifact_receipt_capture.os.fsync", fail_file_sync)
    with pytest.raises(WheelReceiptCaptureError):
        capture(wheel, pkg, receipt)
    assert not receipt.exists()
