from __future__ import annotations

import json
import os
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
        line = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            os.chmod(self.path, 0o600)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()
