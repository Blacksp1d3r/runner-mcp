from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .bridge_protocol import REQUEST_ID_RE, BridgeProtocolError
from .bridge_replay import ReplayState

MAX_PENDING_OBSERVATIONS = 1_000
MAX_PENDING_AGE_SECONDS = 31_536_000
MIN_STALE_AFTER_SECONDS = 30
MAX_STALE_AFTER_SECONDS = 86_400
MAX_HEARTBEAT_BYTES = 1_024
TRANSPORT_RETRY_DELAYS_SECONDS = (2, 5)


class BridgeResilienceError(BridgeProtocolError):
    """Raised when watcher-resilience state fails strict validation."""


class RecoveryDisposition(StrEnum):
    PROCESS = "process"
    RESULT_EXISTS = "result_exists"
    AMBIGUOUS_CLAIM = "ambiguous_claim"
    RESULT_MISSING = "result_missing"


class WatcherState(StrEnum):
    HEALTHY = "healthy"
    BACKLOG = "backlog"
    DEGRADED = "degraded"


class TransportFailureKind(StrEnum):
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    AUTHORIZATION = "authorization"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    request_id: str
    age_seconds: int
    disposition: RecoveryDisposition

    def __post_init__(self) -> None:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise BridgeResilienceError("recovery request_id has an unsafe shape")
        if not isinstance(self.age_seconds, int) or isinstance(self.age_seconds, bool):
            raise BridgeResilienceError("recovery age must be an integer")
        if not 0 <= self.age_seconds <= MAX_PENDING_AGE_SECONDS:
            raise BridgeResilienceError("recovery age is outside the supported range")


class WatcherHeartbeat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal[1] = 1
    state: WatcherState
    pending_requests: int = Field(ge=0, le=MAX_PENDING_OBSERVATIONS)
    stale_requests: int = Field(ge=0, le=MAX_PENDING_OBSERVATIONS)
    recovery_attention: int = Field(ge=0, le=MAX_PENDING_OBSERVATIONS)
    oldest_pending_seconds: int | None = Field(
        default=None,
        ge=0,
        le=MAX_PENDING_AGE_SECONDS,
    )

    @model_validator(mode="after")
    def validate_consistency(self) -> WatcherHeartbeat:
        if self.stale_requests > self.pending_requests:
            raise ValueError("stale_requests cannot exceed pending_requests")
        if self.recovery_attention > self.pending_requests:
            raise ValueError("recovery_attention cannot exceed pending_requests")

        if self.pending_requests == 0:
            if self.oldest_pending_seconds is not None:
                raise ValueError(
                    "oldest_pending_seconds requires at least one pending request"
                )
        elif self.oldest_pending_seconds is None:
            raise ValueError(
                "pending requests require oldest_pending_seconds"
            )

        if self.state == WatcherState.HEALTHY:
            if (
                self.pending_requests != 0
                or self.stale_requests != 0
                or self.recovery_attention != 0
            ):
                raise ValueError("healthy heartbeat cannot report backlog")
        elif self.state == WatcherState.BACKLOG:
            if self.pending_requests == 0:
                raise ValueError("backlog heartbeat requires pending requests")
            if self.stale_requests != 0 or self.recovery_attention != 0:
                raise ValueError(
                    "stale or recovery-attention work must be degraded"
                )
        return self


def recovery_disposition(
    *,
    has_result: bool,
    replay_state: ReplayState | None,
) -> RecoveryDisposition:
    if has_result:
        return RecoveryDisposition.RESULT_EXISTS
    if replay_state is None:
        return RecoveryDisposition.PROCESS
    if replay_state == ReplayState.CLAIMED:
        return RecoveryDisposition.AMBIGUOUS_CLAIM
    if replay_state == ReplayState.COMPLETED:
        return RecoveryDisposition.RESULT_MISSING
    raise BridgeResilienceError("unsupported replay state")


def assess_watcher_health(
    observations: list[RecoveryObservation],
    *,
    stale_after_seconds: int,
    transport_healthy: bool = True,
) -> WatcherHeartbeat:
    if not isinstance(stale_after_seconds, int) or isinstance(
        stale_after_seconds,
        bool,
    ):
        raise BridgeResilienceError("stale threshold must be an integer")
    if not MIN_STALE_AFTER_SECONDS <= stale_after_seconds <= MAX_STALE_AFTER_SECONDS:
        raise BridgeResilienceError("stale threshold is outside the supported range")
    if len(observations) > MAX_PENDING_OBSERVATIONS:
        raise BridgeResilienceError("too many pending observations")
    if any(not isinstance(item, RecoveryObservation) for item in observations):
        raise BridgeResilienceError("invalid pending observation")
    request_ids = [item.request_id for item in observations]
    if len(request_ids) != len(set(request_ids)):
        raise BridgeResilienceError("duplicate pending observation")

    pending = [
        item
        for item in observations
        if item.disposition != RecoveryDisposition.RESULT_EXISTS
    ]
    stale = [
        item
        for item in pending
        if item.age_seconds >= stale_after_seconds
    ]
    attention = [
        item
        for item in pending
        if item.disposition
        in {
            RecoveryDisposition.AMBIGUOUS_CLAIM,
            RecoveryDisposition.RESULT_MISSING,
        }
    ]

    if not transport_healthy or stale or attention:
        state = WatcherState.DEGRADED
    elif pending:
        state = WatcherState.BACKLOG
    else:
        state = WatcherState.HEALTHY

    oldest = max((item.age_seconds for item in pending), default=None)
    return WatcherHeartbeat(
        state=state,
        pending_requests=len(pending),
        stale_requests=len(stale),
        recovery_attention=len(attention),
        oldest_pending_seconds=oldest,
    )


def transport_retry_delays(
    failure: TransportFailureKind,
) -> tuple[int, ...]:
    if not isinstance(failure, TransportFailureKind):
        raise BridgeResilienceError("unsupported transport failure kind")
    if failure in {
        TransportFailureKind.TIMEOUT,
        TransportFailureKind.RATE_LIMITED,
        TransportFailureKind.UNAVAILABLE,
    }:
        return TRANSPORT_RETRY_DELAYS_SECONDS
    return ()


def serialize_watcher_heartbeat(heartbeat: WatcherHeartbeat) -> str:
    encoded = json.dumps(
        heartbeat.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > MAX_HEARTBEAT_BYTES:
        raise BridgeResilienceError("watcher heartbeat exceeds size limit")
    return encoded.decode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BridgeResilienceError("watcher heartbeat contains duplicate JSON keys")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise BridgeResilienceError(
        f"watcher heartbeat contains non-standard JSON constant: {value}"
    )


def parse_watcher_heartbeat(payload: str | bytes) -> WatcherHeartbeat:
    if isinstance(payload, bytes):
        if len(payload) > MAX_HEARTBEAT_BYTES:
            raise BridgeResilienceError("watcher heartbeat exceeds size limit")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BridgeResilienceError("watcher heartbeat must be UTF-8") from exc
    else:
        text = payload
        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise BridgeResilienceError("watcher heartbeat must be UTF-8") from exc
        if len(encoded) > MAX_HEARTBEAT_BYTES:
            raise BridgeResilienceError("watcher heartbeat exceeds size limit")

    try:
        raw = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except BridgeResilienceError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise BridgeResilienceError("watcher heartbeat is not valid JSON") from exc

    if not isinstance(raw, dict):
        raise BridgeResilienceError("watcher heartbeat must be a JSON object")

    try:
        return WatcherHeartbeat.model_validate(raw)
    except ValidationError as exc:
        raise BridgeResilienceError(
            "watcher heartbeat failed strict validation"
        ) from exc
