import os
import stat
from pathlib import Path

import pytest

from runner_mcp import secure_io as secure_io_module
from runner_mcp.secure_io import PrivateAtomicWriteError, atomic_replace_private


def test_atomic_replace_private_forces_0600_under_permissive_umask(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    previous_umask = os.umask(0)
    try:
        atomic_replace_private(target, b'{"state":"ok"}')
    finally:
        os.umask(previous_umask)

    assert target.read_bytes() == b'{"state":"ok"}'
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_atomic_replace_private_refuses_symlink_without_touching_referent(
    tmp_path: Path,
) -> None:
    referent = tmp_path / "outside.json"
    referent.write_bytes(b"outside")
    referent.chmod(0o640)
    referent_mode = stat.S_IMODE(referent.stat().st_mode)
    target = tmp_path / "state.json"
    target.symlink_to(referent)

    with pytest.raises(PrivateAtomicWriteError, match="unsafe"):
        atomic_replace_private(target, b"replacement")

    assert target.is_symlink()
    assert referent.read_bytes() == b"outside"
    assert stat.S_IMODE(referent.stat().st_mode) == referent_mode


def test_atomic_replace_private_fsyncs_before_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    events: list[str] = []
    real_fsync = secure_io_module.os.fsync
    real_replace = secure_io_module.os.replace

    def recording_fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    def recording_replace(source: str | Path, destination: str | Path) -> None:
        events.append("replace")
        real_replace(source, destination)

    monkeypatch.setattr(secure_io_module.os, "fsync", recording_fsync)
    monkeypatch.setattr(secure_io_module.os, "replace", recording_replace)

    atomic_replace_private(target, b"durable")

    assert events == ["fsync", "replace"]
    assert target.read_bytes() == b"durable"


def test_atomic_replace_private_fsync_failure_preserves_target_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")
    sensitive = str(tmp_path / "private-secret")

    def fail_fsync(_fd: int) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, "fsync", fail_fsync)

    with pytest.raises(PrivateAtomicWriteError) as captured:
        atomic_replace_private(target, b"new")

    assert str(captured.value) == "private file replacement failed"
    assert sensitive not in str(captured.value)
    assert target.read_bytes() == b"old"
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_atomic_replace_private_replace_failure_preserves_target_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")
    sensitive = str(tmp_path / "private-secret")

    def fail_replace(_source: str | Path, _destination: str | Path) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, "replace", fail_replace)

    with pytest.raises(PrivateAtomicWriteError) as captured:
        atomic_replace_private(target, b"new")

    assert str(captured.value) == "private file replacement failed"
    assert sensitive not in str(captured.value)
    assert target.read_bytes() == b"old"
    assert list(tmp_path.glob(".state.json.*.tmp")) == []
