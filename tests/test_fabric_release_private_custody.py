"""Isolated 0700 Q7 custody lifecycle: no network, genuine binaries or installation."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

import pytest

from runner_mcp.fabric_release_independent_roster import PinnedReleaseAsset, PinnedReleaseRoster
from runner_mcp.fabric_release_private_custody import (
    Q7CustodyUnqualified, _stage_verified_bytes, stage_pinned_q7_bundle_once,
)

COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"


def _synthetic():
    bodies = {f"file_{i:02d}.whl": f"synthetic-{i}".encode() for i in range(33)}
    pins = PinnedReleaseRoster(
        COMMIT, "fabric-q7-bundle-" + COMMIT, 415955374,
        tuple(PinnedReleaseAsset(
            name, index + 1, len(data), hashlib.sha256(data).hexdigest()
        ) for index, (name, data) in enumerate(sorted(bodies.items()))),
    )
    return pins, bodies


def _private(tmp_path: Path) -> Path:
    root = tmp_path / "control-plane-update"
    root.mkdir(mode=0o700)
    return root


def test_complete_stage_written_once_as_owner_private_fixed_bundle(tmp_path):
    root = _private(tmp_path)
    pins, bodies = _synthetic()
    receipt = _stage_verified_bytes(root, pins, bodies)
    assert receipt["state"] == "owner_private_bytes_custodied"
    assert receipt["asset_count"] == 33
    assert receipt["independent_signer_verified"] is False
    assert receipt["install_authorized"] is False
    assert receipt["original_client_ack"] is False
    assert not (root / ".q7-bundle-inflight").exists()
    stage = root / "bundle"
    assert stat.S_IMODE(stage.stat().st_mode) == 0o700
    assert sorted(p.name for p in stage.iterdir()) == sorted(bodies)
    for name, content in bodies.items():
        file = stage / name
        assert file.read_bytes() == content
        assert stat.S_IMODE(file.stat().st_mode) == 0o600
        assert file.stat().st_nlink == 1

    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)
    assert all((stage / name).read_bytes() == content for name, content in bodies.items())


def test_existing_bundle_never_overwritten(tmp_path):
    root = _private(tmp_path)
    already = root / "bundle"
    already.mkdir(mode=0o700)
    (already / "source.txt").write_text("original")
    pins, bodies = _synthetic()
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)
    assert (already / "source.txt").read_text() == "original"


def test_partial_stage_blocks_replay_and_is_preserved(tmp_path, monkeypatch):
    root = _private(tmp_path)
    pins, bodies = _synthetic()
    original_write = os.write
    calls = 0

    def fail_after_first(fd, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic disk failure")
        return original_write(fd, data)

    monkeypatch.setattr(os, "write", fail_after_first)
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)
    assert not (root / "bundle").exists()
    assert (root / ".q7-bundle-inflight").is_dir()
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)


@pytest.mark.parametrize("mode", [0o755, 0o750, 0o770])
def test_nonprivate_root_refused_without_side_effects(tmp_path, mode):
    root = _private(tmp_path)
    root.chmod(mode)
    pins, bodies = _synthetic()
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)
    assert list(root.iterdir()) == []


def test_symlinked_root_refused(tmp_path):
    actual = _private(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    pins, bodies = _synthetic()
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(alias, pins, bodies)
    assert list(actual.iterdir()) == []


def test_symlinked_preexisting_stage_refused_and_preserved(tmp_path):
    root = _private(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    (root / ".q7-bundle-inflight").symlink_to(target, target_is_directory=True)
    pins, bodies = _synthetic()
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bodies)
    assert list(target.iterdir()) == []


def test_duplicate_or_unsafe_names_refused_before_any_write(tmp_path):
    root = _private(tmp_path)
    pins, bodies = _synthetic()
    bad = dict(bodies)
    bad["../escape"] = bad.pop("file_00.whl")
    with pytest.raises(Q7CustodyUnqualified):
        _stage_verified_bytes(root, pins, bad)
    assert list(root.iterdir()) == []


def test_public_entry_requires_real_independent_bundle_verification(monkeypatch, tmp_path):
    root = _private(tmp_path)
    monkeypatch.setattr(
        "runner_mcp.fabric_release_private_custody._fixed_root", lambda: root
    )
    pins, bodies = _synthetic()
    with pytest.raises(ValueError):
        stage_pinned_q7_bundle_once(None, pins, bodies)  # type: ignore[arg-type]
    assert list(root.iterdir()) == []
