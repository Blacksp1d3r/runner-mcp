"""Geïsoleerde Linux-tests voor de bestaande inactieve Fabric-local-bundles stage.

De productiefunctie bouwt via de bestaande manager en plaatst de complete
bundel in dezelfde privémap. Hier testen we UITSLUITEND de laatste atomaire
directorypromotie op pytest-tmp_path: geen GitHub, credential, Fabric-service,
Qwen/Claude, runner, systeemdienst of fysieke server.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from runner_mcp import fabric_update
from runner_mcp.fabric_update import (
    FabricUpdateError,
    _promote_inactive_bundle_noreplace,
)

COMMIT = "a" * 40
INCOMING = ".incoming-" + "b" * 32


def _fresh(tmp_path: Path):
    """Maak uitsluitend onder tmp_path een eigenaar-private inactieve werkboom."""
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    work = root / INCOMING
    work.mkdir(mode=0o700)
    source = work / "source"
    source.mkdir(mode=0o700)
    bundle = source / "bundle"
    bundle.mkdir(mode=0o700)
    (bundle / "COMMIT_SHA").write_text(COMMIT + "\n", encoding="ascii")
    return root, work, bundle


def test_private_exact_bundle_moves_atomically_only_to_inactive_custody(tmp_path):
    root, work, bundle = _fresh(tmp_path)
    source_inode = bundle.stat().st_ino
    _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    promoted = root / COMMIT
    assert promoted.is_dir()
    assert promoted.stat().st_ino == source_inode
    assert (promoted / "COMMIT_SHA").read_text("ascii") == COMMIT + "\n"
    assert not bundle.exists()
    assert (work / "source").is_dir()
    assert not (tmp_path / "bundle").exists()
    assert not (tmp_path / "slots").exists()
    assert not (tmp_path / "transaction.json").exists()


def test_normal_read_only_git_checkout_directories_are_allowed(tmp_path):
    root, work, _bundle = _fresh(tmp_path)
    # Git schrijft source vaak met mode 0755. Privé-ouder 0700 en geen
    # groeps-/wereldschrijf zijn de werkelijke beveiligingsvoorwaarden.
    (work / "source").chmod(0o755)
    (work / "source" / "bundle").chmod(0o755)
    _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert (root / COMMIT / "COMMIT_SHA").read_text("ascii") == COMMIT + "\n"


def test_existing_empty_destination_cannot_be_replaced(tmp_path):
    root, _, bundle = _fresh(tmp_path)
    destination = root / COMMIT
    destination.mkdir(mode=0o700)
    old_inode = destination.stat().st_ino
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert destination.stat().st_ino == old_inode
    assert list(destination.iterdir()) == []
    assert bundle.exists()


def test_competing_worker_creates_destination_just_before_atomic_promotion(
    tmp_path, monkeypatch,
):
    root, _, bundle = _fresh(tmp_path)
    original = fabric_update._promote_noreplace

    def concurrent_stage(root_fd, stage_name, final_name):
        assert final_name == COMMIT
        os.mkdir(COMMIT, mode=0o700, dir_fd=root_fd)
        return original(root_fd, stage_name, final_name)

    monkeypatch.setattr(fabric_update, "_promote_noreplace", concurrent_stage)
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)

    assert (root / COMMIT).is_dir()
    assert list((root / COMMIT).iterdir()) == []
    assert bundle.exists()
    assert (bundle / "COMMIT_SHA").read_text("ascii") == COMMIT + "\n"


def test_second_stage_same_commit_fails_without_replacing_original(tmp_path):
    root, _, _ = _fresh(tmp_path)
    _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    target = root / COMMIT
    original_inode = target.stat().st_ino

    other = ".incoming-" + "c" * 32
    bundle = root / other / "source" / "bundle"
    bundle.mkdir(parents=True, mode=0o700)
    (root / other).chmod(0o700)
    (root / other / "source").chmod(0o700)
    (bundle / "COMMIT_SHA").write_text("other", encoding="ascii")
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, other, COMMIT)
    assert target.stat().st_ino == original_inode
    assert (target / "COMMIT_SHA").read_text("ascii") == COMMIT + "\n"
    assert (bundle / "COMMIT_SHA").read_text("ascii") == "other"


@pytest.mark.parametrize("part", ["incoming", "source", "bundle"])
def test_symlinked_intermediate_work_tree_denied(tmp_path, part):
    root, work, bundle = _fresh(tmp_path)
    other = tmp_path / "external"
    other.mkdir(mode=0o700)
    if part == "incoming":
        # Vervang alleen de lege werk-ouder niet; bewaar de originele boom.
        preserved = root / (INCOMING + "-preserved")
        work.rename(preserved)
        work.symlink_to(preserved, target_is_directory=True)
    elif part == "source":
        preserved = work / "source-preserved"
        (work / "source").rename(preserved)
        (work / "source").symlink_to(preserved, target_is_directory=True)
    else:
        preserved = work / "source" / "bundle-preserved"
        bundle.rename(preserved)
        bundle.symlink_to(preserved, target_is_directory=True)
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert not (root / COMMIT).exists()
    assert other.is_dir()


@pytest.mark.parametrize("part", ["root", "incoming", "source", "bundle"])
def test_non_private_directory_denied_without_promotion(tmp_path, part):
    root, work, bundle = _fresh(tmp_path)
    choice = {
        "root": root, "incoming": work, "source": work / "source", "bundle": bundle
    }[part]
    # source en bundle mogen 0755 hebben, maar nooit groepsschrijf.
    choice.chmod(0o750 if part in {"root", "incoming"} else 0o770)
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert not (root / COMMIT).exists()
    assert (bundle / "COMMIT_SHA").exists()


@pytest.mark.parametrize("invalid", [
    "", ".incoming-short", ".incoming-" + "B" * 32,
    "../other", ".incoming-" + "a" * 32 + "/other",
    "bundle", COMMIT,
])
def test_not_a_generated_incoming_name_denied(tmp_path, invalid):
    root, _, bundle = _fresh(tmp_path)
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, invalid, COMMIT)
    assert bundle.exists()
    assert not (root / COMMIT).exists()


def test_invalid_commit_refused_without_any_rename(tmp_path):
    root, _, bundle = _fresh(tmp_path)
    with pytest.raises(FabricUpdateError, match="fabric_update_commit_invalid"):
        _promote_inactive_bundle_noreplace(root, INCOMING, "main")
    assert bundle.exists()


def test_preexisting_destination_symlink_is_never_followed(tmp_path):
    root, _, bundle = _fresh(tmp_path)
    other = tmp_path / "outside"
    other.mkdir(mode=0o700)
    (root / COMMIT).symlink_to(other, target_is_directory=True)
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert (root / COMMIT).is_symlink()
    assert bundle.exists()
    assert list(other.iterdir()) == []


def test_failed_incomplete_work_tree_never_creates_destination(tmp_path):
    root, _, bundle = _fresh(tmp_path)
    (bundle / "COMMIT_SHA").unlink()
    bundle.rmdir()
    with pytest.raises(FabricUpdateError, match="fabric_bundle_storage_conflict"):
        _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert not (root / COMMIT).exists()


def test_private_incoming_does_not_authorize_host_update_or_change_active_state(tmp_path):
    root, _, _ = _fresh(tmp_path)
    (tmp_path / "bundle").mkdir(mode=0o700)
    (tmp_path / "bundle" / "active").write_text("prior")
    (tmp_path / "slots").mkdir(mode=0o700)
    (tmp_path / "slots" / "previous").write_text("protected")
    (tmp_path / "transaction.json").write_text("history")
    _promote_inactive_bundle_noreplace(root, INCOMING, COMMIT)
    assert (tmp_path / "bundle" / "active").read_text() == "prior"
    assert (tmp_path / "slots" / "previous").read_text() == "protected"
    assert (tmp_path / "transaction.json").read_text() == "history"
    assert stat.S_IMODE((root / COMMIT).stat().st_mode) == 0o700
