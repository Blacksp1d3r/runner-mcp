"""Atomic create-once writer for UNTRUSTED offline receipt candidates.

This module has no deployment authority. Data passed by a caller is not a
trusted builder manifest, and successful writing never attests running code.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from uuid import uuid4

_MAX_RECEIPT_BYTES = 64 * 1024


def write_offline_receipt_candidate(destination: Path, receipt: dict[str, object]) -> bool:
    """Create an owner-only receipt without replacing an existing receipt.

    The caller remains responsible for authenticating the builder, validating
    contents, and binding an immutable environment to active runtime evidence.
    """
    if not isinstance(destination, Path) or not isinstance(receipt, dict):
        return False
    parent = destination.parent
    temporary: Path | None = None
    try:
        # Never follow a redirected receipt directory or a cross-user writable parent.
        if parent.is_symlink() or not parent.is_dir():
            return False
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            return False
        if info.st_mode & 0o022:
            return False
        if destination.exists() or destination.is_symlink():
            return False
        payload = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        if len(payload) > _MAX_RECEIPT_BYTES:
            return False
        temporary = parent / f".{destination.name}.{uuid4().hex}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(fd, "wb", closefd=True) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            # A hard link makes publishing atomic and fail-if-existing.
            os.link(temporary, destination, follow_symlinks=False)
            directory_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return True
        finally:
            temporary.unlink(missing_ok=True)
    except (OSError, TypeError, ValueError, UnicodeError):
        return False
