from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - Linux is the supported mutation platform
    _fcntl = None

_LOCK_FILENAME = ".runner-mcp-operation.lock"


class ReleaseOperationLockError(RuntimeError):
    """Bounded failure while preparing or holding a release-operation lock."""


class ReleaseOperationBusy(ReleaseOperationLockError):
    """Raised when another process already holds the release-operation lock."""


class ReleaseOperationLock:
    """One acquired non-blocking cross-process release-operation lock."""

    def __init__(self, fd: int) -> None:
        self._fd = fd

    def close(self) -> None:
        fd = self._fd
        if fd < 0:
            return
        self._fd = -1
        try:
            if _fcntl is not None:
                _fcntl.flock(fd, _fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(fd)
        except OSError:
            pass

    def __enter__(self) -> ReleaseOperationLock:
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()


def _validated_release_root(release_root: Path) -> Path:
    if not isinstance(release_root, Path) or not release_root.is_absolute():
        raise ReleaseOperationLockError("release operation lock root is unavailable")

    current = Path(release_root.anchor)
    try:
        for part in release_root.parts[1:]:
            current = current / part
            metadata = os.lstat(current)
            if stat.S_ISLNK(metadata.st_mode):
                raise ReleaseOperationLockError("release operation lock root is unsafe")
    except ReleaseOperationLockError:
        raise
    except OSError as exc:
        raise ReleaseOperationLockError("release operation lock root is unavailable") from exc

    try:
        metadata = os.stat(release_root, follow_symlinks=False)
    except OSError as exc:
        raise ReleaseOperationLockError("release operation lock root is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise ReleaseOperationLockError("release operation lock root is unavailable")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise ReleaseOperationLockError("release operation lock root is unsafe")
    if metadata.st_uid != os.getuid():
        raise ReleaseOperationLockError("release operation lock root is unsafe")
    return release_root


def _open_lock_file(release_root: Path) -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReleaseOperationLockError("release operation locking is unavailable")

    lock_path = release_root / _LOCK_FILENAME
    base_flags = os.O_RDWR | os.O_NOFOLLOW
    created = False
    try:
        try:
            fd = os.open(
                lock_path,
                base_flags | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            created = True
        except FileExistsError:
            fd = os.open(lock_path, base_flags)
    except OSError as exc:
        raise ReleaseOperationLockError("release operation lock object is unsafe") from exc

    try:
        os.set_inheritable(fd, False)
        if created:
            os.fchmod(fd, 0o600)
        metadata = os.fstat(fd)
        path_metadata = os.stat(lock_path, follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode):
            raise ReleaseOperationLockError("release operation lock object is unsafe")
        if not stat.S_ISREG(path_metadata.st_mode):
            raise ReleaseOperationLockError("release operation lock object is unsafe")
        if (metadata.st_dev, metadata.st_ino) != (
            path_metadata.st_dev,
            path_metadata.st_ino,
        ):
            raise ReleaseOperationLockError("release operation lock object is unsafe")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise ReleaseOperationLockError("release operation lock object is unsafe")
        if metadata.st_uid != os.getuid():
            raise ReleaseOperationLockError("release operation lock object is unsafe")
    except ReleaseOperationLockError:
        os.close(fd)
        raise
    except OSError as exc:
        os.close(fd)
        raise ReleaseOperationLockError("release operation lock object is unsafe") from exc
    return fd


def acquire_release_operation_lock(release_root: Path) -> ReleaseOperationLock:
    """Acquire the fixed private release-root lock without blocking or retrying."""
    if _fcntl is None:
        raise ReleaseOperationLockError("release operation locking is unavailable")

    validated_root = _validated_release_root(release_root)
    fd = _open_lock_file(validated_root)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
    except OSError as exc:
        try:
            os.close(fd)
        except OSError:
            pass
        if exc.errno in {errno.EACCES, errno.EAGAIN}:
            raise ReleaseOperationBusy("release_operation_busy") from None
        raise ReleaseOperationLockError("release operation locking failed") from None
    return ReleaseOperationLock(fd)
