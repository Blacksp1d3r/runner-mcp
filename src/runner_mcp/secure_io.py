from __future__ import annotations

import os
import tempfile
from pathlib import Path


class PrivateAtomicWriteError(RuntimeError):
    """Bounded failure from private atomic file replacement."""


def atomic_replace_private(path: Path, content: bytes) -> None:
    """Atomically replace one private file from a same-directory random temp file."""
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise PrivateAtomicWriteError("private file parent is unavailable")
    if path.is_symlink():
        raise PrivateAtomicWriteError("private file target is unsafe")

    fd = -1
    temporary: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
        )
        temporary = Path(temp_name)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise PrivateAtomicWriteError("private file replacement failed") from exc
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
