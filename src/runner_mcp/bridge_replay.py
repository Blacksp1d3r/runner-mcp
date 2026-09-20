from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import fcntl

from .bridge_protocol import BridgeProtocolError, BridgeRequest

MAX_REPLAY_LEDGER_BYTES = 1_048_576
DEFAULT_MAX_REPLAY_ENTRIES = 5_000


class BridgeReplayError(BridgeProtocolError):
    """Raised when mailbox replay protection fails closed."""


class ReplayDecision(StrEnum):
    NEW = "new"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class ReplayClaim:
    decision: ReplayDecision
    fingerprint: str


def bridge_request_fingerprint(request: BridgeRequest) -> str:
    payload = json.dumps(
        request.model_dump(mode="json", exclude_none=True),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class BridgeReplayLedger:
    """Small local ledger that prevents request-id replay or mutation."""

    def __init__(
        self,
        path: Path,
        *,
        max_entries: int = DEFAULT_MAX_REPLAY_ENTRIES,
    ) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self._path = path
        self._max_entries = max_entries

    def claim(self, request: BridgeRequest) -> ReplayClaim:
        fingerprint = bridge_request_fingerprint(request)
        fd = self._open_ledger()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                entries = self._load(handle)
                existing = entries.get(request.request_id)

                if existing is not None:
                    if existing.get("fingerprint") != fingerprint:
                        raise BridgeReplayError(
                            "request_id was already used for a different request"
                        )
                    return ReplayClaim(
                        decision=ReplayDecision.DUPLICATE,
                        fingerprint=fingerprint,
                    )

                if len(entries) >= self._max_entries:
                    raise BridgeReplayError("replay ledger capacity reached")

                entries[request.request_id] = {
                    "fingerprint": fingerprint,
                    "action": request.action.value,
                    "seen_at": datetime.now(UTC).isoformat(),
                }
                self._store(handle, entries)
                return ReplayClaim(
                    decision=ReplayDecision.NEW,
                    fingerprint=fingerprint,
                )
        except OSError as exc:
            raise BridgeReplayError("replay ledger operation failed") from exc

    def _open_ledger(self) -> int:
        parent = self._path.parent
        if not parent.exists() or not parent.is_dir():
            raise BridgeReplayError("replay ledger parent directory is unavailable")

        try:
            fd = os.open(
                self._path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
            os.fchmod(fd, 0o600)
            return fd
        except OSError as exc:
            raise BridgeReplayError("replay ledger could not be opened") from exc

    def _load(self, handle: Any) -> dict[str, dict[str, str]]:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size > MAX_REPLAY_LEDGER_BYTES:
            raise BridgeReplayError("replay ledger exceeds size limit")

        handle.seek(0)
        text = handle.read()
        if not text:
            return {}

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise BridgeReplayError("replay ledger is not valid JSON") from exc

        if not isinstance(raw, dict):
            raise BridgeReplayError("replay ledger has invalid structure")

        entries: dict[str, dict[str, str]] = {}
        for request_id, entry in raw.items():
            if not isinstance(request_id, str) or not isinstance(entry, dict):
                raise BridgeReplayError("replay ledger has invalid structure")

            fingerprint = entry.get("fingerprint")
            action = entry.get("action")
            seen_at = entry.get("seen_at")
            if (
                not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or not isinstance(action, str)
                or not isinstance(seen_at, str)
            ):
                raise BridgeReplayError("replay ledger has invalid entry")

            entries[request_id] = {
                "fingerprint": fingerprint,
                "action": action,
                "seen_at": seen_at,
            }

        return entries

    def _store(self, handle: Any, entries: dict[str, dict[str, str]]) -> None:
        encoded = json.dumps(
            entries,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if len(encoded) > MAX_REPLAY_LEDGER_BYTES:
            raise BridgeReplayError("replay ledger exceeds size limit")

        handle.seek(0)
        handle.truncate()
        handle.write(encoded.decode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
