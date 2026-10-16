from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight
from runner_mcp.offline_receipt_writer import write_offline_receipt_candidate


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
    sha = lambda data: hashlib.sha256(data).hexdigest()
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
