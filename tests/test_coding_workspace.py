"""No generic mkdir: only local owner-bound fixed worker workspaces are writable."""

from __future__ import annotations

import fcntl
import os
import pwd
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from runner_mcp.coding_workspace import CodingWorkspaceProvisioner

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="rootless identity required")


def _configured(tmp_path: Path, worker: str = "qwen") -> tuple[CodingWorkspaceProvisioner, Path]:
    root = tmp_path / "work"
    root.mkdir(mode=0o755)
    for name in ("jobs", "patches"):
        (root / name).mkdir(mode=0o700)
    owner = pwd.getpwuid(os.geteuid()).pw_name
    values = {
        "RUNNER_MCP_CODING_WORKSPACE_WORKER": worker,
        "RUNNER_MCP_CODING_WORKSPACE_OWNER": owner,
        "RUNNER_MCP_CODING_WORKSPACE_ROOT": str(root),
    }
    return CodingWorkspaceProvisioner(values), root


def test_qwen_0755_root_and_private_subfolders_are_accepted(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    assert provisioner.preflight("qwen")["state"] == "ready"
    first = provisioner.prepare("qwen", "enercue-118")
    second = provisioner.prepare("qwen", "enercue-118")
    assert first["state"] == "prepared"
    assert second["state"] == "already_prepared"
    for parent in ("jobs", "patches"):
        item = root / parent / "enercue-118"
        assert stat.S_IMODE(item.stat().st_mode) == 0o700
    assert "tmp" not in repr(first)
    assert first["cross_host_execution_authorized"] is False
    assert first["filesystem_path_exposed"] is False


def test_claude_has_separate_fixed_worker_binding(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path, "claude")
    assert provisioner.prepare("qwen", "enercue-118")["reason_code"] == "worker_binding_mismatch"
    assert provisioner.prepare("claude", "enercue-89")["state"] == "prepared"
    assert not (root / "jobs" / "enercue-118").exists()


@pytest.mark.parametrize(
    "bad", ("../other", "/tmp/other", "", "a/b", "a\\b", ".", "..", "a b", "a" * 65),
)
def test_path_traversal_and_invalid_ids_do_not_write(tmp_path: Path, bad: str) -> None:
    provisioner, root = _configured(tmp_path)
    assert provisioner.prepare("qwen", bad)["reason_code"] == "work_unit_id_invalid"
    assert list((root / "jobs").iterdir()) == []
    assert list((root / "patches").iterdir()) == []


def test_unconfigured_and_partial_config_fail_without_mkdir(tmp_path: Path) -> None:
    empty = CodingWorkspaceProvisioner({})
    assert empty.preflight("claude")["reason_code"] == "private_binding_unavailable"
    assert empty.prepare("qwen", "job-1")["state"] == "unavailable"
    partial = CodingWorkspaceProvisioner({
        "RUNNER_MCP_CODING_WORKSPACE_ROOT": str(tmp_path / "never"),
    })
    assert partial.prepare("qwen", "job-1")["reason_code"] == "private_binding_incomplete"
    assert not (tmp_path / "never").exists()


def test_symlinked_workspace_and_subfolders_denied(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    (root / "jobs").rmdir()
    (root / "jobs").symlink_to(target, target_is_directory=True)
    assert provisioner.prepare("qwen", "job-1")["state"] == "unavailable"
    assert not (target / "job-1").exists()


def test_symlinked_task_denied_without_patch_creation(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    (root / "jobs" / "job-1").symlink_to(tmp_path, target_is_directory=True)
    result = provisioner.prepare("qwen", "job-1")
    assert result["reason_code"] == "workspace_entry_unsafe"
    assert not (root / "patches" / "job-1").exists()


def test_existing_partial_task_denied_without_modification(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    (root / "jobs" / "job-1").mkdir(mode=0o700)
    result = provisioner.prepare("qwen", "job-1")
    assert result["reason_code"] == "workspace_partial_existing"
    assert not (root / "patches" / "job-1").exists()


def test_world_writable_workspace_denied(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    (root / "jobs").chmod(0o777)
    result = provisioner.prepare("qwen", "job-1")
    assert result["state"] == "unavailable"
    assert not (root / "jobs" / "job-1").exists()


def test_owner_mismatch_never_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provisioner, root = _configured(tmp_path)
    real = os.geteuid()
    monkeypatch.setattr(os, "geteuid", lambda: real + 50000)
    result = provisioner.prepare("qwen", "job-1")
    assert result["reason_code"] == "local_owner_mismatch"
    assert not (root / "jobs" / "job-1").exists()


def test_unowned_root_and_symlink_parent_denied(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    root.chmod(0o777)
    assert provisioner.preflight("qwen")["reason_code"] == "workspace_directory_unsafe"
    root.chmod(0o755)
    symlink = tmp_path / "linked"
    symlink.symlink_to(root, target_is_directory=True)
    values = {
        "RUNNER_MCP_CODING_WORKSPACE_WORKER": "qwen",
        "RUNNER_MCP_CODING_WORKSPACE_OWNER": pwd.getpwuid(os.geteuid()).pw_name,
        "RUNNER_MCP_CODING_WORKSPACE_ROOT": str(symlink),
    }
    assert CodingWorkspaceProvisioner(values).prepare("qwen", "job-1")["state"] == "unavailable"


def test_capacity_limit_rejects_new_job_but_allows_repeat(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    assert provisioner.prepare("qwen", "first")["state"] == "prepared"
    for i in range(127):
        for parent in ("jobs", "patches"):
            (root / parent / f"existing-{i}").mkdir(mode=0o700)
    assert provisioner.prepare("qwen", "first")["state"] == "already_prepared"
    assert provisioner.prepare("qwen", "next")["reason_code"] == "workspace_capacity_reached"
    assert not (root / "jobs" / "next").exists()


def test_busy_workspace_blocks_without_write_then_replays(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    fd = os.open(root / "jobs", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = provisioner.prepare("qwen", "f18-replay")
        assert result["reason_code"] == "workspace_busy"
        assert not (root / "jobs" / "f18-replay").exists()
        assert not (root / "patches" / "f18-replay").exists()
    finally:
        os.close(fd)
    assert provisioner.prepare("qwen", "f18-replay")["state"] == "prepared"
    assert provisioner.prepare("qwen", "f18-replay")["state"] == "already_prepared"


def test_simultaneous_same_id_returns_one_completed_pair(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda _: provisioner.prepare("qwen", "same-f18-work-unit"), range(16),
        ))
    assert sum(reply["state"] == "prepared" for reply in results) == 1
    assert all(
        reply["state"] in {"prepared", "already_prepared"}
        or (reply["state"] == "unavailable" and reply["reason_code"] == "workspace_busy")
        for reply in results
    )
    assert provisioner.prepare("qwen", "same-f18-work-unit")["state"] == "already_prepared"
    for name in ("jobs", "patches"):
        entries = list((root / name).iterdir())
        assert len(entries) == 1
        assert stat.S_IMODE(entries[0].stat().st_mode) == 0o700


def test_inspect_reports_pair_without_mutation(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    before = (list((root / "jobs").iterdir()), list((root / "patches").iterdir()))
    absent = provisioner.inspect("qwen", "new-f18")
    assert absent["state"] == "absent"
    assert absent["reason_code"] == "workspace_not_prepared"
    assert absent["filesystem_path_exposed"] is False
    assert absent["cross_host_execution_authorized"] is False
    assert before == (list((root / "jobs").iterdir()), list((root / "patches").iterdir()))
    assert provisioner.prepare("qwen", "new-f18")["state"] == "prepared"
    receipt = provisioner.inspect("qwen", "new-f18")
    assert receipt["state"] == "prepared"
    assert receipt["reason_code"] == "already_prepared"


def test_inspect_denies_partial_unsafe_and_wrong_identity(tmp_path: Path) -> None:
    provisioner, root = _configured(tmp_path)
    (root / "jobs" / "partial").mkdir(mode=0o700)
    assert provisioner.inspect("qwen", "partial")["reason_code"] == "workspace_partial_existing"
    assert not (root / "patches" / "partial").exists()
    assert provisioner.inspect("qwen", "../escape")["reason_code"] == "work_unit_id_invalid"
    assert provisioner.inspect("claude", "partial")["reason_code"] == "worker_binding_mismatch"
    (root / "jobs" / "unsafe").symlink_to(tmp_path, target_is_directory=True)
    assert provisioner.inspect("qwen", "unsafe")["reason_code"] == "workspace_entry_unsafe"
    assert not (root / "patches" / "unsafe").exists()
