from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Iterable

from .bridge_protocol import REQUEST_ID_RE, BridgeAction, BridgeRequest
from .bridge_replay import ReplayClaim, ReplayDecision


class MailboxHealthState(StrEnum):
    HEALTHY = "healthy"
    BACKLOG = "backlog"
    DEGRADED = "degraded"


class RecoveryDisposition(StrEnum):
    PROCESS = "process"
    RETRY_IDEMPOTENT = "retry_idempotent"
    SKIP_COMPLETED = "skip_completed"
    RECONCILE_REQUIRED = "reconcile_required"


@dataclass(frozen=True)
class PendingRequestObservation:
    request_id: str
    first_seen_at: datetime

    def __post_init__(self) -> None:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id contains unsupported characters")
        if self.first_seen_at.tzinfo is None:
            raise ValueError("first_seen_at must be timezone-aware")


@dataclass(frozen=True)
class MailboxHeartbeat:
    state: MailboxHealthState
    observed_at: datetime
    pending_count: int
    stale_count: int
    oldest_pending_seconds: int

    def as_safe_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "observed_at": self.observed_at.astimezone(UTC).isoformat(),
            "pending_count": self.pending_count,
            "stale_count": self.stale_count,
            "oldest_pending_seconds": self.oldest_pending_seconds,
        }


@dataclass(frozen=True)
class TransportRetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: int = 2
    max_delay_seconds: int = 30

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.max_attempts > 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if self.base_delay_seconds < 1:
            raise ValueError("base_delay_seconds must be positive")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must not be smaller than base_delay_seconds")

    def delay_before_attempt(self, attempt: int) -> int | None:
        """Return bounded delay before a retry attempt, or None when retries are exhausted."""
        if attempt < 2:
            raise ValueError("attempt must be a retry attempt (2 or greater)")
        if attempt > self.max_attempts:
            return None
        exponent = attempt - 2
        return min(self.base_delay_seconds * (2**exponent), self.max_delay_seconds)


def build_mailbox_heartbeat(
    pending: Iterable[PendingRequestObservation],
    *,
    observed_at: datetime | None = None,
    stale_after_seconds: int = 300,
    transport_degraded: bool = False,
) -> MailboxHeartbeat:
    if stale_after_seconds < 1:
        raise ValueError("stale_after_seconds must be positive")

    now = observed_at or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    now = now.astimezone(UTC)

    ages: list[int] = []
    for item in pending:
        age = int(max(0, (now - item.first_seen_at.astimezone(UTC)).total_seconds()))
        ages.append(age)

    stale_count = sum(age >= stale_after_seconds for age in ages)
    if transport_degraded or stale_count:
        state = MailboxHealthState.DEGRADED
    elif ages:
        state = MailboxHealthState.BACKLOG
    else:
        state = MailboxHealthState.HEALTHY

    return MailboxHeartbeat(
        state=state,
        observed_at=now,
        pending_count=len(ages),
        stale_count=stale_count,
        oldest_pending_seconds=max(ages, default=0),
    )


def recovery_disposition(
    request: BridgeRequest,
    claim: ReplayClaim,
) -> RecoveryDisposition:
    """
    Decide what a restarted watcher may safely do.

    Completed requests are never executed again. Unfinished duplicate read-only/status
    requests may be repeated because they do not mutate project state. RUN_TESTS is
    deliberately different: a watcher restart may have happened after Runner MCP
    started the job but before the result was published, so the watcher must reconcile
    against Runner MCP job state instead of blindly launching the test again.
    """
    if claim.completed:
        return RecoveryDisposition.SKIP_COMPLETED

    if claim.decision == ReplayDecision.NEW:
        return RecoveryDisposition.PROCESS

    if request.action == BridgeAction.RUN_TESTS:
        return RecoveryDisposition.RECONCILE_REQUIRED

    return RecoveryDisposition.RETRY_IDEMPOTENT
