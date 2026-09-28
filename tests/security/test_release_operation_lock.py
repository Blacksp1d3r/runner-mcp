import multiprocessing
import os
import stat
from pathlib import Path

import pytest

from runner_mcp import release_operation_lock as lock_module
from runner_mcp.release_operation_lock import (
    ReleaseOperationBusy,
    ReleaseOperationLockError,
    acquire_release_operation_lock,
)


def private_root(tmp_path: Path, name: str = "releases") -> Path:
    root = tmp_path / name
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return root


def hold_lock(path: str, ready, release) -> None:
    lock = acquire_release_operation_lock(Path(path))
    ready.set()
    release.wait(timeout=10)
    lock.close()


def test_separate_processes_cannot_hold_same_release_lock(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    context = multiprocessing.get_context("fork")
    ready = context.Event()
    release = context.Event()
    process = context.Process(target=hold_lock, args=(str(root), ready, release))
    process.start()
    try:
        assert ready.wait(timeout=5)
        with pytest.raises(ReleaseOperationBusy) as captured:
            acquire_release_operation_lock(root)
        assert str(captured.value) == "release_operation_busy"
        assert str(root) not in str(captured.value)
    finally:
        release.set()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
    assert process.exitcode == 0

    with acquire_release_operation_lock(root):
        pass


def test_process_exit_releases_kernel_lock_but_keeps_lock_file(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    context = multiprocessing.get_context("fork")
    ready = context.Event()
    release = context.Event()
    process = context.Process(target=hold_lock, args=(str(root), ready, release))
    process.start()
    assert ready.wait(timeout=5)

    process.terminate()
    process.join(timeout=5)
    assert process.exitcode is not None

    lock_path = root / ".runner-mcp-operation.lock"
    assert lock_path.is_file()
    assert not lock_path.is_symlink()
    assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600

    with acquire_release_operation_lock(root):
        pass


def test_normal_close_keeps_reusable_private_lock_file(tmp_path: Path) -> None:
    root = private_root(tmp_path)

    first = acquire_release_operation_lock(root)
    first.close()
    first.close()

    lock_path = root / ".runner-mcp-operation.lock"
    assert lock_path.read_bytes() == b""
    assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600

    with acquire_release_operation_lock(root):
        pass


def test_symlink_lock_object_is_rejected_without_touching_referent(
    tmp_path: Path,
) -> None:
    root = private_root(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"untouched")
    lock_path = root / ".runner-mcp-operation.lock"
    lock_path.symlink_to(outside)

    with pytest.raises(ReleaseOperationLockError) as captured:
        acquire_release_operation_lock(root)

    assert "unsafe" in str(captured.value)
    assert str(tmp_path) not in str(captured.value)
    assert outside.read_bytes() == b"untouched"


def test_non_regular_lock_object_is_rejected(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    (root / ".runner-mcp-operation.lock").mkdir(mode=0o700)

    with pytest.raises(ReleaseOperationLockError, match="unsafe"):
        acquire_release_operation_lock(root)


def test_broad_lock_permissions_are_rejected(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    lock_path = root / ".runner-mcp-operation.lock"
    lock_path.write_bytes(b"")
    lock_path.chmod(0o644)

    with pytest.raises(ReleaseOperationLockError, match="unsafe"):
        acquire_release_operation_lock(root)


def test_wrong_owner_lock_metadata_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = private_root(tmp_path)
    lock_path = root / ".runner-mcp-operation.lock"
    lock_path.write_bytes(b"")
    lock_path.chmod(0o600)
    real_fstat = lock_module.os.fstat

    def wrong_owner_fstat(fd: int):
        metadata = real_fstat(fd)
        values = list(metadata)
        values[4] = metadata.st_uid + 1
        return os.stat_result(values)

    monkeypatch.setattr(lock_module.os, "fstat", wrong_owner_fstat)

    with pytest.raises(ReleaseOperationLockError, match="unsafe"):
        acquire_release_operation_lock(root)


def test_unsafe_release_root_fails_closed(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    root.chmod(0o755)

    with pytest.raises(ReleaseOperationLockError, match="unsafe"):
        acquire_release_operation_lock(root)


def test_symlinked_release_root_fails_closed(tmp_path: Path) -> None:
    real_root = private_root(tmp_path, "real")
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(ReleaseOperationLockError, match="unsafe"):
        acquire_release_operation_lock(linked_root)


def test_different_release_roots_do_not_block_each_other(tmp_path: Path) -> None:
    first_root = private_root(tmp_path, "first")
    second_root = private_root(tmp_path, "second")

    first = acquire_release_operation_lock(first_root)
    try:
        second = acquire_release_operation_lock(second_root)
        second.close()
    finally:
        first.close()
