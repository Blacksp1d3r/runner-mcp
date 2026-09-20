from __future__ import annotations

import fcntl
import json
import os
import re
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .bridge_processor import (
    BridgeExecutor,
    BridgeProcessor,
    BridgeProcessState,
)
from .bridge_protocol import (
    BridgeProtocolError,
    parse_bridge_request,
)
from .bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayRecord,
)
from .bridge_resilience import (
    MAX_PENDING_AGE_SECONDS,
    BridgeResilienceError,
    RecoveryDisposition,
    RecoveryObservation,
    WatcherHeartbeat,
    assess_watcher_health,
    recovery_disposition,
    serialize_watcher_heartbeat,
)
from .github_mailbox import (
    GitHubMailboxTransport,
    GitHubMailboxTransportError,
)

MAX_CURSOR_BYTES = 1_024
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GitHubWatcherError(BridgeResilienceError):
    """Safe watcher orchestration failure."""


class GitHubWatcherCycleState(StrEnum):
    UNINITIALIZED = "uninitialized"
    IDLE = "idle"
    PROCESSED = "processed"
    RECOVERY_REQUIRED = "recovery_required"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class GitHubWatcherCycleOutcome:
    state: GitHubWatcherCycleState
    discovered_requests: int
    processed_requests: int
    reconciled_requests: int
    recovery_attention: int
    heartbeat: WatcherHeartbeat
    heartbeat_published: bool


class GitHubWatcherCursorStore:
    """Private local fast-forward cursor with fail-closed file semantics."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> str | None:
        fd = self._open()
        try:
            with os.fdopen(fd, "r", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
                return self._load(handle)
        except OSError as exc:
            raise GitHubWatcherError("watcher cursor read failed") from exc

    def initialize(self, head_sha: str) -> None:
        _validate_commit_sha(head_sha)
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                current = self._load(handle)
                if current is not None:
                    raise GitHubWatcherError("watcher cursor is already initialized")
                self._store(handle, head_sha)
        except OSError as exc:
            raise GitHubWatcherError("watcher cursor initialization failed") from exc

    def advance(self, *, expected_sha: str, new_sha: str) -> None:
        _validate_commit_sha(expected_sha)
        _validate_commit_sha(new_sha)
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                current = self._load(handle)
                if current != expected_sha:
                    raise GitHubWatcherError(
                        "watcher cursor changed concurrently"
                    )
                self._store(handle, new_sha)
        except OSError as exc:
            raise GitHubWatcherError("watcher cursor update failed") from exc

    def _open(self) -> int:
        parent = self._path.parent
        if not parent.exists() or not parent.is_dir():
            raise GitHubWatcherError("watcher cursor parent is unavailable")

        try:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self._path, flags, 0o600)
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                os.close(fd)
                raise GitHubWatcherError(
                    "watcher cursor must be a regular file"
                )
            os.fchmod(fd, 0o600)
            return fd
        except OSError as exc:
            raise GitHubWatcherError("watcher cursor could not be opened") from exc

    def _load(self, handle: Any) -> str | None:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size > MAX_CURSOR_BYTES:
            raise GitHubWatcherError("watcher cursor exceeds size limit")

        handle.seek(0)
        text = handle.read()
        if not text:
            return None

        try:
            raw = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonstandard_json_constant,
            )
        except GitHubWatcherError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise GitHubWatcherError("watcher cursor is invalid JSON") from exc

        if not isinstance(raw, dict) or set(raw) != {
            "version",
            "request_head_sha",
        }:
            raise GitHubWatcherError("watcher cursor has invalid structure")
        if raw["version"] != 1:
            raise GitHubWatcherError("watcher cursor version is unsupported")

        head_sha = raw["request_head_sha"]
        if not isinstance(head_sha, str) or not _COMMIT_SHA_RE.fullmatch(head_sha):
            raise GitHubWatcherError("watcher cursor has invalid commit SHA")
        return head_sha

    def _store(self, handle: Any, head_sha: str) -> None:
        encoded = json.dumps(
            {
                "version": 1,
                "request_head_sha": head_sha,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_CURSOR_BYTES:
            raise GitHubWatcherError("watcher cursor exceeds size limit")

        handle.seek(0)
        handle.truncate()
        handle.write(encoded.decode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


class GitHubMailboxWatcher:
    """Incremental GitHub mailbox coordinator with no historical replay by default."""

    def __init__(
        self,
        *,
        transport: GitHubMailboxTransport,
        ledger: BridgeReplayLedger,
        executor: BridgeExecutor,
        cursor_store: GitHubWatcherCursorStore,
        stale_after_seconds: int = 300,
    ) -> None:
        if not 30 <= stale_after_seconds <= 86_400:
            raise ValueError("stale_after_seconds is outside the supported range")
        self._transport = transport
        self._ledger = ledger
        self._processor = BridgeProcessor(
            ledger=ledger,
            executor=executor,
            result_sink=transport,
        )
        self._cursor_store = cursor_store
        self._stale_after_seconds = stale_after_seconds

    def bootstrap_cursor_at_current_head(self) -> None:
        """Explicitly ignore historical requests and start after the current head."""
        head_sha = self._transport.request_head_sha()
        self._cursor_store.initialize(head_sha)

    def run_cycle(self) -> GitHubWatcherCycleOutcome:
        try:
            cursor = self._cursor_store.read()
        except GitHubWatcherError:
            return self._degraded_outcome()

        if cursor is None:
            return self._uninitialized_outcome()

        try:
            current_head = self._transport.request_head_sha()
        except GitHubMailboxTransportError:
            return self._degraded_outcome()

        if current_head == cursor:
            heartbeat = assess_watcher_health(
                [],
                stale_after_seconds=self._stale_after_seconds,
            )
            published = self._publish_heartbeat(heartbeat)
            return GitHubWatcherCycleOutcome(
                state=(
                    GitHubWatcherCycleState.IDLE
                    if published
                    else GitHubWatcherCycleState.DEGRADED
                ),
                discovered_requests=0,
                processed_requests=0,
                reconciled_requests=0,
                recovery_attention=0,
                heartbeat=heartbeat,
                heartbeat_published=published,
            )

        try:
            request_ids = self._transport.changed_request_ids(
                base_sha=cursor,
                head_sha=current_head,
            )
        except (GitHubMailboxTransportError, ValueError):
            return self._degraded_outcome()

        observations: list[RecoveryObservation] = []
        processed = 0
        reconciled = 0
        hard_failure_index: int | None = None

        for index, request_id in enumerate(request_ids):
            try:
                request_bytes = self._transport.fetch_request(request_id)
                request = parse_bridge_request(request_bytes)
                if request.request_id != request_id:
                    raise BridgeProtocolError(
                        "request filename and payload ID do not match"
                    )
                result = self._transport.fetch_result(request_id)
                record = self._ledger.inspect(request)
            except (
                BridgeProtocolError,
                BridgeReplayError,
                GitHubMailboxTransportError,
                ValueError,
            ):
                observations.append(
                    RecoveryObservation(
                        request_id=request_id,
                        age_seconds=0,
                        disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                    )
                )
                hard_failure_index = index
                break

            if result is not None:
                if result.action != request.action:
                    observations.append(
                        RecoveryObservation(
                            request_id=request_id,
                            age_seconds=_record_age_seconds(record),
                            disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                        )
                    )
                    hard_failure_index = index
                    break

                try:
                    self._ledger.claim(request)
                    self._ledger.complete(request)
                except BridgeReplayError:
                    observations.append(
                        RecoveryObservation(
                            request_id=request_id,
                            age_seconds=_record_age_seconds(record),
                            disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                        )
                    )
                    hard_failure_index = index
                    break

                reconciled += 1
                continue

            disposition = recovery_disposition(
                has_result=False,
                replay_state=(record.state if record is not None else None),
            )
            if disposition == RecoveryDisposition.PROCESS:
                outcome = self._processor.process(request_bytes)
                if outcome.state == BridgeProcessState.COMPLETED:
                    processed += 1
                    continue

                current_record = self._ledger.inspect(request)
                if outcome.state == BridgeProcessState.ALREADY_COMPLETED:
                    disposition = RecoveryDisposition.RESULT_MISSING
                else:
                    disposition = RecoveryDisposition.AMBIGUOUS_CLAIM
                observations.append(
                    RecoveryObservation(
                        request_id=request_id,
                        age_seconds=_record_age_seconds(current_record),
                        disposition=disposition,
                    )
                )
                hard_failure_index = index
                break

            observations.append(
                RecoveryObservation(
                    request_id=request_id,
                    age_seconds=_record_age_seconds(record),
                    disposition=disposition,
                )
            )
            hard_failure_index = index
            break

        if hard_failure_index is not None:
            for request_id in request_ids[hard_failure_index + 1 :]:
                observations.append(
                    RecoveryObservation(
                        request_id=request_id,
                        age_seconds=0,
                        disposition=RecoveryDisposition.PROCESS,
                    )
                )

        cursor_advanced = False
        if not observations:
            try:
                self._cursor_store.advance(
                    expected_sha=cursor,
                    new_sha=current_head,
                )
                cursor_advanced = True
            except GitHubWatcherError:
                observations.append(
                    RecoveryObservation(
                        request_id=request_ids[0] if request_ids else "cursor",
                        age_seconds=0,
                        disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                    )
                )

        heartbeat = assess_watcher_health(
            observations,
            stale_after_seconds=self._stale_after_seconds,
            transport_healthy=cursor_advanced or bool(observations),
        )
        published = self._publish_heartbeat(heartbeat)

        if not published:
            state = GitHubWatcherCycleState.DEGRADED
        elif observations:
            state = GitHubWatcherCycleState.RECOVERY_REQUIRED
        elif processed or reconciled:
            state = GitHubWatcherCycleState.PROCESSED
        else:
            state = GitHubWatcherCycleState.IDLE

        return GitHubWatcherCycleOutcome(
            state=state,
            discovered_requests=len(request_ids),
            processed_requests=processed,
            reconciled_requests=reconciled,
            recovery_attention=heartbeat.recovery_attention,
            heartbeat=heartbeat,
            heartbeat_published=published,
        )

    def _publish_heartbeat(self, heartbeat: WatcherHeartbeat) -> bool:
        try:
            self._transport.publish_heartbeat(
                serialize_watcher_heartbeat(heartbeat)
            )
        except (BridgeResilienceError, GitHubMailboxTransportError):
            return False
        return True

    def _uninitialized_outcome(self) -> GitHubWatcherCycleOutcome:
        heartbeat = assess_watcher_health(
            [],
            stale_after_seconds=self._stale_after_seconds,
            transport_healthy=False,
        )
        published = self._publish_heartbeat(heartbeat)
        return GitHubWatcherCycleOutcome(
            state=GitHubWatcherCycleState.UNINITIALIZED,
            discovered_requests=0,
            processed_requests=0,
            reconciled_requests=0,
            recovery_attention=0,
            heartbeat=heartbeat,
            heartbeat_published=published,
        )

    def _degraded_outcome(self) -> GitHubWatcherCycleOutcome:
        heartbeat = assess_watcher_health(
            [],
            stale_after_seconds=self._stale_after_seconds,
            transport_healthy=False,
        )
        published = self._publish_heartbeat(heartbeat)
        return GitHubWatcherCycleOutcome(
            state=GitHubWatcherCycleState.DEGRADED,
            discovered_requests=0,
            processed_requests=0,
            reconciled_requests=0,
            recovery_attention=0,
            heartbeat=heartbeat,
            heartbeat_published=published,
        )


def _record_age_seconds(record: ReplayRecord | None) -> int:
    if record is None:
        return 0
    seen_at = datetime.fromisoformat(record.seen_at)
    age = max(0, int((datetime.now(UTC) - seen_at).total_seconds()))
    return min(age, MAX_PENDING_AGE_SECONDS)


def _validate_commit_sha(value: str) -> None:
    if not _COMMIT_SHA_RE.fullmatch(value):
        raise ValueError("commit SHA must be exactly 40 lowercase hex characters")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GitHubWatcherError("watcher cursor contains duplicate JSON keys")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise GitHubWatcherError(
        f"watcher cursor contains non-standard JSON constant: {value}"
    )
