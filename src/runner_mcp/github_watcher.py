from __future__ import annotations

import fcntl
import json
import os
import re
import stat
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .bridge_processor import (
    BridgeExecutor,
    BridgeProcessor,
    BridgeProcessState,
    BridgeResultSinkError,
)
from .bridge_protocol import (
    BridgeAction,
    BridgeProtocolError,
    BridgeResult,
    BridgeResultState,
    parse_bridge_request,
    serialize_bridge_result,
)
from .bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayDecision,
    ReplayRecord,
    ReplayState,
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
class GitHubRecoveryResolution:
    request_id: str
    action: BridgeAction
    prior_state: ReplayState


@dataclass(frozen=True, slots=True)
class GitHubAbandonResolution:
    request_id: str
    action: BridgeAction


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
        max_workers: int = 4,
        max_inflight: int = 32,
    ) -> None:
        if not 30 <= stale_after_seconds <= 86_400:
            raise ValueError("stale_after_seconds is outside the supported range")
        if not 1 <= max_workers <= 16:
            raise ValueError("max_workers must be between 1 and 16")
        if not max_workers <= max_inflight <= 256:
            raise ValueError("max_inflight must be between max_workers and 256")
        self._transport = transport
        self._ledger = ledger
        self._processor = BridgeProcessor(
            ledger=ledger,
            executor=executor,
            result_sink=transport,
        )
        self._cursor_store = cursor_store
        self._stale_after_seconds = stale_after_seconds
        self._max_workers = max_workers
        self._max_inflight = max_inflight

    def bootstrap_cursor_at_current_head(self) -> None:
        """Explicitly ignore historical requests and start after the current head."""
        head_sha = self._transport.request_head_sha()
        self._cursor_store.initialize(head_sha)

    def resolve_missing_result_fail_closed(
        self,
        request_id: str,
    ) -> GitHubRecoveryResolution:
        """Publish a terminal safe failure without replaying ambiguous work."""
        try:
            request_bytes = self._transport.fetch_request(request_id)
            request = parse_bridge_request(request_bytes)
            if request.request_id != request_id:
                raise BridgeProtocolError(
                    "request filename and payload ID do not match"
                )
            existing_result = self._transport.fetch_result(request_id)
            record = self._ledger.inspect(request)
        except (
            BridgeProtocolError,
            BridgeReplayError,
            GitHubMailboxTransportError,
            ValueError,
        ) as exc:
            raise GitHubWatcherError(
                "recovery request state could not be verified safely"
            ) from exc

        if existing_result is not None:
            raise GitHubWatcherError(
                "a durable result already exists; use normal watcher reconciliation"
            )
        if record is None:
            raise GitHubWatcherError(
                "request was never claimed; normal watcher processing is required"
            )
        if record.state not in {ReplayState.CLAIMED, ReplayState.COMPLETED}:
            raise GitHubWatcherError("request replay state is unsupported")

        failure = BridgeResult(
            request_id=request.request_id,
            action=request.action,
            state=BridgeResultState.FAILED,
            error_code="RECOVERY_REQUIRED",
            summary=(
                "The prior execution outcome is ambiguous. "
                "No action was replayed during recovery."
            ),
        )
        try:
            result_json = serialize_bridge_result(failure)
            self._transport.persist_result(request_id, result_json)
            if record.state == ReplayState.CLAIMED:
                self._ledger.complete(request)
        except (
            BridgeProtocolError,
            BridgeReplayError,
            BridgeResultSinkError,
            GitHubMailboxTransportError,
            ValueError,
        ) as exc:
            raise GitHubWatcherError(
                "fail-closed recovery result could not be persisted safely"
            ) from exc

        return GitHubRecoveryResolution(
            request_id=request.request_id,
            action=request.action,
            prior_state=record.state,
        )

    def abandon_unclaimed_request_fail_closed(
        self,
        request_id: str,
    ) -> GitHubAbandonResolution:
        """Persist an operator-aborted result without executing a fresh request."""
        try:
            request_bytes = self._transport.fetch_request(request_id)
            request = parse_bridge_request(request_bytes)
            if request.request_id != request_id:
                raise BridgeProtocolError(
                    "request filename and payload ID do not match"
                )
            existing_result = self._transport.fetch_result(request_id)
            record = self._ledger.inspect(request)
        except (
            BridgeProtocolError,
            BridgeReplayError,
            GitHubMailboxTransportError,
            ValueError,
        ) as exc:
            raise GitHubWatcherError(
                "abandon request state could not be verified safely"
            ) from exc

        if existing_result is not None:
            raise GitHubWatcherError(
                "a durable result already exists; use normal watcher reconciliation"
            )
        if record is not None:
            raise GitHubWatcherError(
                "request already has replay state; use missing-result recovery instead"
            )

        failure = BridgeResult(
            request_id=request.request_id,
            action=request.action,
            state=BridgeResultState.FAILED,
            error_code="OPERATOR_ABORTED",
            summary=(
                "A local operator abandoned this request. "
                "No action was executed."
            ),
        )
        try:
            claim = self._ledger.claim(request)
            if claim.decision != ReplayDecision.NEW:
                raise BridgeReplayError("request was claimed concurrently")
            result_json = serialize_bridge_result(failure)
            self._transport.persist_result(request_id, result_json)
        except (
            BridgeProtocolError,
            BridgeReplayError,
            BridgeResultSinkError,
            GitHubMailboxTransportError,
            ValueError,
        ) as exc:
            raise GitHubWatcherError(
                "abandonment result could not be persisted safely"
            ) from exc

        try:
            self._ledger.complete(request)
        except BridgeReplayError as exc:
            raise GitHubWatcherError(
                "abandonment result is durable; normal reconciliation is required"
            ) from exc

        return GitHubAbandonResolution(
            request_id=request.request_id,
            action=request.action,
        )

    def quarantine_malformed_request_fail_closed(
        self,
        request_id: str,
    ) -> GitHubWatcherCycleOutcome:
        """Advance only when one malformed request is the sole unresolved backlog."""
        try:
            cursor = self._cursor_store.read()
        except GitHubWatcherError:
            raise
        if cursor is None:
            raise GitHubWatcherError(
                "watcher cursor is uninitialized; bootstrap is required"
            )

        try:
            current_head = self._transport.request_head_sha()
            if current_head == cursor:
                raise GitHubWatcherError("watcher backlog is already empty")
            request_ids = self._transport.changed_request_ids(
                base_sha=cursor,
                head_sha=current_head,
            )
        except (GitHubMailboxTransportError, ValueError) as exc:
            raise GitHubWatcherError(
                "watcher backlog could not be verified safely"
            ) from exc

        if request_id not in request_ids:
            raise GitHubWatcherError(
                "malformed request is not present in the current watcher backlog"
            )

        try:
            malformed_bytes = self._transport.fetch_request_unvalidated(request_id)
            existing_result = self._transport.fetch_result(request_id)
        except GitHubMailboxTransportError as exc:
            raise GitHubWatcherError(
                "malformed request state could not be verified safely"
            ) from exc

        try:
            parse_bridge_request(malformed_bytes)
        except BridgeProtocolError:
            pass
        else:
            raise GitHubWatcherError(
                "request is protocol-valid; use normal processing, abandon or resolve"
            )

        if existing_result is not None:
            raise GitHubWatcherError(
                "malformed request already has a durable result; manual review is required"
            )

        reconciled = 0
        for other_request_id in request_ids:
            if other_request_id == request_id:
                continue
            try:
                request_bytes = self._transport.fetch_request(other_request_id)
                request = parse_bridge_request(request_bytes)
                if request.request_id != other_request_id:
                    raise BridgeProtocolError(
                        "request filename and payload ID do not match"
                    )
                result = self._transport.fetch_result(other_request_id)
                record = self._ledger.inspect(request)
            except (
                BridgeProtocolError,
                BridgeReplayError,
                GitHubMailboxTransportError,
                ValueError,
            ) as exc:
                raise GitHubWatcherError(
                    "another backlog request cannot be reconciled safely"
                ) from exc

            if result is None:
                raise GitHubWatcherError(
                    "another backlog request is unresolved; resolve or abandon it first"
                )
            if result.action != request.action:
                raise GitHubWatcherError(
                    "another backlog result does not match its request action"
                )

            try:
                self._ledger.claim(request)
                self._ledger.complete(request)
            except BridgeReplayError as exc:
                raise GitHubWatcherError(
                    "another backlog request cannot be reconciled safely"
                ) from exc
            reconciled += 1

        try:
            verified_head = self._transport.request_head_sha()
        except GitHubMailboxTransportError as exc:
            raise GitHubWatcherError(
                "watcher backlog could not be reverified safely"
            ) from exc
        if verified_head != current_head:
            raise GitHubWatcherError(
                "request head changed during malformed-request quarantine"
            )

        try:
            self._cursor_store.advance(
                expected_sha=cursor,
                new_sha=current_head,
            )
        except GitHubWatcherError:
            raise

        heartbeat = assess_watcher_health(
            [],
            stale_after_seconds=self._stale_after_seconds,
        )
        heartbeat_ok, published = self._heartbeat_delivery(
            heartbeat,
            publish_heartbeat=True,
        )
        return GitHubWatcherCycleOutcome(
            state=(
                GitHubWatcherCycleState.PROCESSED
                if heartbeat_ok
                else GitHubWatcherCycleState.DEGRADED
            ),
            discovered_requests=len(request_ids),
            processed_requests=0,
            reconciled_requests=reconciled,
            recovery_attention=0,
            heartbeat=heartbeat,
            heartbeat_published=published,
        )

    def _process_request(
        self,
        request_id: str,
    ) -> tuple[str, RecoveryObservation | None]:
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
            return (
                "attention",
                RecoveryObservation(
                    request_id=request_id,
                    age_seconds=0,
                    disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                ),
            )

        if result is not None:
            if result.action != request.action:
                return (
                    "attention",
                    RecoveryObservation(
                        request_id=request_id,
                        age_seconds=_record_age_seconds(record),
                        disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                    ),
                )

            try:
                self._ledger.claim(request)
                self._ledger.complete(request)
            except BridgeReplayError:
                return (
                    "attention",
                    RecoveryObservation(
                        request_id=request_id,
                        age_seconds=_record_age_seconds(record),
                        disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                    ),
                )
            return "reconciled", None

        disposition = recovery_disposition(
            has_result=False,
            replay_state=(record.state if record is not None else None),
        )
        if disposition == RecoveryDisposition.PROCESS:
            outcome = self._processor.process(request_bytes)
            if outcome.state == BridgeProcessState.COMPLETED:
                return "processed", None

            current_record = self._ledger.inspect(request)
            if outcome.state == BridgeProcessState.ALREADY_COMPLETED:
                disposition = RecoveryDisposition.RESULT_MISSING
            else:
                disposition = RecoveryDisposition.AMBIGUOUS_CLAIM
            return (
                "attention",
                RecoveryObservation(
                    request_id=request_id,
                    age_seconds=_record_age_seconds(current_record),
                    disposition=disposition,
                ),
            )

        return (
            "attention",
            RecoveryObservation(
                request_id=request_id,
                age_seconds=_record_age_seconds(record),
                disposition=disposition,
            ),
        )

    def _process_request_batch(
        self,
        request_ids: list[str],
    ) -> tuple[int, int, list[RecoveryObservation]]:
        processed = 0
        reconciled = 0
        observations: list[RecoveryObservation] = []

        for offset in range(0, len(request_ids), self._max_inflight):
            batch = request_ids[offset : offset + self._max_inflight]
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                futures = {
                    pool.submit(self._process_request, request_id): request_id
                    for request_id in batch
                }
                for future in as_completed(futures):
                    request_id = futures[future]
                    try:
                        outcome, observation = future.result()
                    except Exception:  # noqa: BLE001 - worker failures fail closed
                        outcome = "attention"
                        observation = RecoveryObservation(
                            request_id=request_id,
                            age_seconds=0,
                            disposition=RecoveryDisposition.AMBIGUOUS_CLAIM,
                        )
                    if outcome == "processed":
                        processed += 1
                    elif outcome == "reconciled":
                        reconciled += 1
                    if observation is not None:
                        observations.append(observation)

        return processed, reconciled, observations

    def run_cycle(
        self,
        *,
        publish_heartbeat: bool = True,
    ) -> GitHubWatcherCycleOutcome:
        try:
            cursor = self._cursor_store.read()
        except GitHubWatcherError:
            return self._degraded_outcome(publish_heartbeat=publish_heartbeat)

        if cursor is None:
            return self._uninitialized_outcome(publish_heartbeat=publish_heartbeat)

        try:
            current_head = self._transport.request_head_sha()
        except GitHubMailboxTransportError:
            return self._degraded_outcome(publish_heartbeat=publish_heartbeat)

        if current_head == cursor:
            heartbeat = assess_watcher_health(
                [],
                stale_after_seconds=self._stale_after_seconds,
            )
            heartbeat_ok, published = self._heartbeat_delivery(
                heartbeat,
                publish_heartbeat=publish_heartbeat,
            )
            return GitHubWatcherCycleOutcome(
                state=(
                    GitHubWatcherCycleState.IDLE
                    if heartbeat_ok
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
            return self._degraded_outcome(publish_heartbeat=publish_heartbeat)

        processed, reconciled, observations = self._process_request_batch(request_ids)

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
        heartbeat_ok, published = self._heartbeat_delivery(
            heartbeat,
            publish_heartbeat=publish_heartbeat,
        )

        if not heartbeat_ok:
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

    def _heartbeat_delivery(
        self,
        heartbeat: WatcherHeartbeat,
        *,
        publish_heartbeat: bool,
    ) -> tuple[bool, bool]:
        if not publish_heartbeat:
            return True, False
        try:
            self._transport.publish_heartbeat(
                serialize_watcher_heartbeat(heartbeat)
            )
        except (BridgeResilienceError, GitHubMailboxTransportError):
            return False, False
        return True, True

    def _uninitialized_outcome(
        self,
        *,
        publish_heartbeat: bool,
    ) -> GitHubWatcherCycleOutcome:
        heartbeat = assess_watcher_health(
            [],
            stale_after_seconds=self._stale_after_seconds,
            transport_healthy=False,
        )
        _heartbeat_ok, published = self._heartbeat_delivery(
            heartbeat,
            publish_heartbeat=publish_heartbeat,
        )
        return GitHubWatcherCycleOutcome(
            state=GitHubWatcherCycleState.UNINITIALIZED,
            discovered_requests=0,
            processed_requests=0,
            reconciled_requests=0,
            recovery_attention=0,
            heartbeat=heartbeat,
            heartbeat_published=published,
        )

    def _degraded_outcome(
        self,
        *,
        publish_heartbeat: bool,
    ) -> GitHubWatcherCycleOutcome:
        heartbeat = assess_watcher_health(
            [],
            stale_after_seconds=self._stale_after_seconds,
            transport_healthy=False,
        )
        _heartbeat_ok, published = self._heartbeat_delivery(
            heartbeat,
            publish_heartbeat=publish_heartbeat,
        )
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
