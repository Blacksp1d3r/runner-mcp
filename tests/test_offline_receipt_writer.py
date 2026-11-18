from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight
from runner_mcp.offline_receipt_writer import (
    ReceiptPublicationUncertain,
    write_offline_receipt_candidate,
)


def test_atomic_candidate_create_once_and_owner_only(tmp_path: Path):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    target = folder / "manifest.json"
    assert write_offline_receipt_candidate(target, {"value": "first"}) is True
    assert target.stat().st_mode & 0o777 == 0o600
    assert json.loads(target.read_text(encoding="utf-8")) == {"value": "first"}
    assert not list(folder.glob("*.tmp"))
    assert write_offline_receipt_candidate(target, {"value": "second"}) is False
    assert json.loads(target.read_text(encoding="utf-8")) == {"value": "first"}


@pytest.mark.parametrize("mode", [0o777, 0o770, 0o733])
def test_rejects_writable_receipt_parent(tmp_path: Path, mode: int):
    folder = tmp_path / "writable"
    folder.mkdir()
    folder.chmod(mode)
    assert not write_offline_receipt_candidate(folder / "receipt.json", {"ok": True})


def test_rejects_linked_parent_and_target(tmp_path: Path):
    folder = tmp_path / "safe"
    folder.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(folder, target_is_directory=True)
    assert not write_offline_receipt_candidate(alias / "new.json", {"ok": True})
    target = folder / "receipt.json"
    existing = folder / "existing.json"
    existing.write_text("original", encoding="utf-8")
    target.symlink_to(existing)
    assert not write_offline_receipt_candidate(target, {"ok": True})
    assert existing.read_text(encoding="utf-8") == "original"


def test_oversized_candidate_fails_without_partial_file(tmp_path: Path):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    target = folder / "receipt.json"
    assert not write_offline_receipt_candidate(target, {"blob": "a" * 70000})
    assert not target.exists()
    assert list(folder.iterdir()) == []


def test_written_candidate_can_pass_offline_only_preflight(tmp_path: Path):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    package = tmp_path / "package"
    package.mkdir()
    module = package / "module.py"
    module.write_bytes(b"installed bytes")
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"wheel bytes")
    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    receipt = folder / "receipt.json"
    record = {
        "schema_version": "runner-mcp/offline-artifact-receipt/v1",
        "source_revision": "a" * 40,
        "wheel_sha256": sha(wheel.read_bytes()),
        "modules": {"module.py": sha(module.read_bytes())},
    }
    assert write_offline_receipt_candidate(receipt, record)
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "offline_bytes_match"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


def test_directory_fsync_failure_after_publish_requires_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    destination = folder / "receipt.json"
    real_fsync = os.fsync
    calls = 0

    def fail_second_fsync(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic directory sync failure")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_second_fsync)
    with pytest.raises(ReceiptPublicationUncertain):
        write_offline_receipt_candidate(destination, {"source": "untrusted"})
    assert destination.exists()
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "source": "untrusted"
    }
    assert not list(folder.glob("*.tmp"))


def test_file_fsync_failure_before_publish_has_no_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    destination = folder / "receipt.json"

    def fail_fsync(fd: int) -> None:
        raise OSError("synthetic file sync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    assert write_offline_receipt_candidate(destination, {"candidate": True}) is False
    assert not destination.exists()
    assert list(folder.iterdir()) == []


def test_competing_publication_does_not_overwrite_existing_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    destination = folder / "receipt.json"
    real_link = os.link

    def competing_link(src: Path, dst: Path, *, follow_symlinks: bool = True) -> None:
        dst.write_text('{"competitor":true}', encoding="utf-8")
        real_link(src, dst, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", competing_link)
    assert write_offline_receipt_candidate(destination, {"ours": True}) is False
    assert json.loads(destination.read_text(encoding="utf-8")) == {"competitor": True}
    assert sorted(path.name for path in folder.iterdir()) == ["receipt.json"]


def test_two_concurrent_writers_cannot_both_publish(tmp_path: Path):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    destination = folder / "receipt.json"

    def attempt(index: int) -> bool:
        return write_offline_receipt_candidate(destination, {"writer": index})

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, (1, 2)))

    assert sorted(results) == [False, True]
    assert json.loads(destination.read_text(encoding="utf-8"))["writer"] in (1, 2)
    assert sorted(p.name for p in folder.iterdir()) == ["receipt.json"]


def test_file_name_cannot_escape_parent(tmp_path: Path):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    destination = folder / "../escaped.json"
    assert not write_offline_receipt_candidate(destination, {"untrusted": True})
    assert not (tmp_path / "escaped.json").exists()


def test_rejects_symlink_in_grandparent_of_receipt_directory(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    child = real / "child"
    child.mkdir(mode=0o700)
    alias = tmp_path / "indirect"
    alias.symlink_to(real, target_is_directory=True)
    target = alias / "child" / "receipt.json"
    assert write_offline_receipt_candidate(target, {"candidate": True}) is False
    assert not (child / "receipt.json").exists()


def test_rejects_relative_receipt_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    folder = tmp_path / "receipts"
    folder.mkdir(mode=0o700)
    monkeypatch.chdir(folder)
    assert write_offline_receipt_candidate(Path("receipt.json"), {"ok": True}) is False
    assert not (folder / "receipt.json").exists()
