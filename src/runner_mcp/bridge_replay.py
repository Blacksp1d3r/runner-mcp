from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .bridge_protocol import (
    REQUEST_ID_RE,
    BridgeAction,
    BridgeProtocolError,
    BridgeRequest,
)

MAX_REPLAY_LEDGER_BYTES = 1_048_576
DEFAULT_MAX_REPLAY_ENTRIES = 5_000
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class BridgeReplayError(BridgeProtocolError):
    """Raised when mailbox replay protection fails closed."""


class ReplayDecision(StrEnum):
    NEW = "new"
    DUPLICATE = "duplicate"


class ReplayState(StrEnum):
    CLAIMED = "claimed"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ReplayClaim:
    decision: ReplayDecision
    fingerprint: str
    state: ReplayState


@dataclass(frozen=True)
class ReplayRecord:
    request_id: str
    fingerprint: str
    action: BridgeAction
    state: ReplayState
    seen_at: str
    completed_at: str | None = None


def bridge_request_fingerprint(request: BridgeRequest) -> str:
    payload = json.dumps(
        request.model_dump(mode="json", exclude_none=True),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class BridgeReplayLedger:
    """Local request lifecycle ledger used to prevent unsafe replay."""

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
                    self._validate_request_match(
                        request=request,
                        fingerprint=fingerprint,
                        entry=existing,
                    )
                    return ReplayClaim(
                        decision=ReplayDecision.DUPLICATE,
                        fingerprint=fingerprint,
                        state=ReplayState(existing["state"]),
                    )

                if len(entries) >= self._max_entries:
                    raise BridgeReplayError("replay ledger capacity reached")

                entries[request.request_id] = {
                    "fingerprint": fingerprint,
                    "action": request.action.value,
                    "state": ReplayState.CLAIMED.value,
                    "seen_at": datetime.now(UTC).isoformat(),
                }
                self._store(handle, entries)
                return ReplayClaim(
                    decision=ReplayDecision.NEW,
                    fingerprint=fingerprint,
                    state=ReplayState.CLAIMED,
                )
        except OSError as exc:
            raise BridgeReplayError("replay ledger operation failed") from exc

    def complete(self, request: BridgeRequest) -> ReplayRecord:
        """Mark a previously claimed request completed after its result is durable."""
        fingerprint = bridge_request_fingerprint(request)
        fd = self._open_ledger()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                entries = self._load(handle)
                existing = entries.get(request.request_id)
                if existing is None:
                    raise BridgeReplayError(
                        "request must be claimed before it can be completed"
                    )

                self._validate_request_match(
                    request=request,
                    fingerprint=fingerprint,
                    entry=existing,
                )

                if existing["state"] == ReplayState.CLAIMED.value:
                    existing["state"] = ReplayState.COMPLETED.value
                    existing["completed_at"] = datetime.now(UTC).isoformat()
                    self._store(handle, entries)

                return self._record(request.request_id, existing)
        except OSError as exc:
            raise BridgeReplayError("replay ledger operation failed") from exc

    def inspect(self, request: BridgeRequest) -> ReplayRecord | None:
        """Return safe lifecycle metadata without mutating the ledger."""
        fingerprint = bridge_request_fingerprint(request)
        fd = self._open_ledger()
        try:
            with os.fdopen(fd, "r", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
                entries = self._load(handle)
                existing = entries.get(request.request_id)
                if existing is None:
                    return None
                self._validate_request_match(
                    request=request,
                    fingerprint=fingerprint,
                    entry=existing,
                )
                return self._record(request.request_id, existing)
        except OSError as exc:
            raise BridgeReplayError("replay ledger operation failed") from exc

    def _validate_request_match(
        self,
        *,
        request: BridgeRequest,
        fingerprint: str,
        entry: dict[str, str],
    ) -> None:
        if (
            entry["fingerprint"] != fingerprint
            or entry["action"] != request.action.value
        ):
            raise BridgeReplayError(
                "request_id was already used for a different request"
            )

    def _record(self, request_id: str, entry: dict[str, str]) -> ReplayRecord:
        return ReplayRecord(
            request_id=request_id,
            fingerprint=entry["fingerprint"],
            action=BridgeAction(entry["action"]),
            state=ReplayState(entry["state"]),
            seen_at=entry["seen_at"],
            completed_at=entry.get("completed_at"),
        )

    def _open_ledger(self) -> int:
        parent = self._path.parent
        if not parent.exists() or not parent.is_dir():
            raise BridgeReplayError("replay ledger parent directory is unavailable")

        try:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self._path, flags, 0o600)
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                os.close(fd)
                raise BridgeReplayError("replay ledger must be a regular file")
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
        allowed_actions = {action.value for action in BridgeAction}
        allowed_states = {state.value for state in ReplayState}
        for request_id, entry in raw.items():
            if (
                not isinstance(request_id, str)
                or not REQUEST_ID_RE.fullmatch(request_id)
                or not isinstance(entry, dict)
            ):
                raise BridgeReplayError("replay ledger has invalid structure")

            fingerprint = entry.get("fingerprint")
            action = entry.get("action")
            seen_at = entry.get("seen_at")
            state = entry.get("state", ReplayState.CLAIMED.value)
            completed_at = entry.get("completed_at")
            if (
                not isinstance(fingerprint, str)
                or not _SHA256_RE.fullmatch(fingerprint)
                or not isinstance(action, str)
                or action not in allowed_actions
                or not isinstance(seen_at, str)
                or not isinstance(state, str)
                or state not in allowed_states
            ):
                raise BridgeReplayError("replay ledger has invalid entry")

            self._parse_timestamp(seen_at)

            normalized: dict[str, str] = {
                "fingerprint": fingerprint,
                "action": action,
                "state": state,
                "seen_at": seen_at,
            }

            if state == ReplayState.COMPLETED.value:
                if not isinstance(completed_at, str):
                    raise BridgeReplayError("completed replay entry lacks timestamp")
                self._parse_timestamp(completed_at)
                normalized["completed_at"] = completed_at
            elif completed_at is not None:
                raise BridgeReplayError(
                    "claimed replay entry must not have completed_at"
                )

            entries[request_id] = normalized

        return entries

    def _parse_timestamp(self, value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise BridgeReplayError("replay ledger has invalid timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise BridgeReplayError("replay ledger timestamp must include timezone")
        return parsed

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
