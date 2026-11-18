"""No-symlink fixed owner-only Q7 custody-root preparation regression tests."""
from __future__ import annotations

import os
import stat

import pytest

from runner_mcp.fabric_q7_fixed_root_prepare import (
    Q7FixedRootUnqualified,
    _prepare_fixed_q7_root_under,
)


def _base(tmp_path):
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    return root


def test_prepare_only_two_fixed_private_descendants_then_idempotent(tmp_path):
    root = _base(tmp_path)
    result = _prepare_fixed_q7_root_under(root)
    assert result == {
        "state": "fixed_root_prepared",
        "roots_private": True,
        "physical_independence_verified": False,
        "bundle_imported": False,
        "install_authorized": False,
    }
    level = root / "runner-fabric"
    dest = level / "control-plane-update"
    assert stat.S_IMODE(level.stat().st_mode) == 0o700
    assert stat.S_IMODE(dest.stat().st_mode) == 0o700
    assert _prepare_fixed_q7_root_under(root)["state"] == "already_private"
    assert list(level.iterdir()) == [dest]


def test_partial_owner_root_refused_without_repair(tmp_path):
    root = _base(tmp_path)
    first = root / "runner-fabric"
    first.mkdir(mode=0o700)
    with pytest.raises(Q7FixedRootUnqualified):
        _prepare_fixed_q7_root_under(root)
    assert list(first.iterdir()) == []


def test_symlinked_existing_first_root_refused(tmp_path):
    root = _base(tmp_path)
    target = tmp_path / "outside"
    target.mkdir(mode=0o700)
    (root / "runner-fabric").symlink_to(target, target_is_directory=True)
    with pytest.raises(Q7FixedRootUnqualified):
        _prepare_fixed_q7_root_under(root)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("bad", [0o755, 0o750, 0o775])
def test_non_private_parent_is_refused_without_mutation(tmp_path, bad):
    root = _base(tmp_path)
    root.chmod(bad)
    with pytest.raises(Q7FixedRootUnqualified):
        _prepare_fixed_q7_root_under(root)
    assert list(root.iterdir()) == []


def test_second_fixed_mkdir_failure_preserves_partial_forensic_root(
    tmp_path, monkeypatch
):
    root = _base(tmp_path)
    real_mkdir = os.mkdir

    def synthetic_fail(name, mode=0o777, *, dir_fd=None):
        if name == "control-plane-update":
            raise OSError("synthetic filesystem denial")
        return real_mkdir(name, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", synthetic_fail)
    with pytest.raises(Q7FixedRootUnqualified):
        _prepare_fixed_q7_root_under(root)
    assert (root / "runner-fabric").is_dir()
    assert not (root / "runner-fabric/control-plane-update").exists()
    with pytest.raises(Q7FixedRootUnqualified):
        _prepare_fixed_q7_root_under(root)


def test_existing_leaf_with_unexpected_data_not_deleted(tmp_path):
    root = _base(tmp_path)
    leaf = root / "runner-fabric"
    leaf.mkdir(mode=0o700)
    target = leaf / "control-plane-update"
    target.mkdir(mode=0o700)
    (target / "old-evidence.txt").write_text("keep")
    assert _prepare_fixed_q7_root_under(root)["state"] == "already_private"
    assert (target / "old-evidence.txt").read_text() == "keep"
