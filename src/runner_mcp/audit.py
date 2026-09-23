from __future__ import annotations

import fcntl
import json
import os
import stat
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock


@dataclass(frozen=True)
class AuditEvent:
    request_id: str
    tool: str
    project: str | None
    actor: str
    result: str
    timestamp: str


class AuditLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()

    def append(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        if nofollow == 0:
            raise OSError("audit append requires symlink-safe file opening")
        flags |= nofollow

        with self._lock:
            fd = os.open(self.path, flags, 0o600)
            try:
                opened = os.fstat(fd)
                if not stat.S_ISREG(opened.st_mode):
                    raise OSError("audit target must be a regular file")
                os.fchmod(fd, 0o600)
                fcntl.flock(fd, fcntl.LOCK_EX)
                try:
                    view = memoryview(payload)
                    while view:
                        written = os.write(fd, view)
                        if written <= 0:
                            raise OSError("audit append made no write progress")
                        view = view[written:]
                    os.fsync(fd)
                finally:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()
