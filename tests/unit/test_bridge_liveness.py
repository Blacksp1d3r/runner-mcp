from datetime import UTC, datetime, timedelta

import pytest

from runner_mcp.bridge_liveness import (
    MailboxHealthState,
    PendingRequestObservation,
    RecoveryDisposition,
    TransportRetryPolicy,
    build_mailbox_heartbeat,
    recovery_disposition,
)
from runner_mcp.bridge_protocol import parse_bridge_request
from runner_mcp.bridge_replay import BridgeReplayLedger, ReplayDecision


def test_heartbeat_is_sanitized_and_reports_healthy_state() -> None:
    now = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    heartbeat = build_mailbox_heartbeat([], observed_at=now)

    assert heartbeat.state == MailboxHealthState.HEALTHY
    assert heartbeat.as_safe_dict() == {
        "state": "healthy",
        "observed_at": "2026-09-20T12:00:00+00:00",
        "pending_count": 0,
        "stale_count": 0,
        "oldest_pending_seconds": 0,
    }
    assert "host" not in heartbeat.as_safe_dict()
    assert "path" not in heartbeat.as_safe_dict()
    assert "service" not in heartbeat.as_safe_dict()


def test_heartbeat_distinguishes_backlog_from_stale_degraded() -> None:
    now = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    fresh = PendingRequestObservation("req-fresh", now - timedelta(seconds=30))
    stale = PendingRequestObservation("req-stale", now - timedelta(minutes=10))

    backlog = build_mailbox_heartbeat([fresh], observed_at=now, stale_after_seconds=300)
    degraded = build_mailbox_heartbeat(
        [fresh, stale], observed_at=now, stale_after_seconds=300
    )

    assert backlog.state == MailboxHealthState.BACKLOG
    assert backlog.stale_count == 0
    assert degraded.state == MailboxHealthState.DEGRADED
    assert degraded.pending_count == 2
    assert degraded.stale_count == 1
    assert degraded.oldest_pending_seconds == 600


def test_transport_error_marks_heartbeat_degraded_without_private_metadata() -> None:
    now = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    heartbeat = build_mailbox_heartbeat(
        [], observed_at=now, transport_degraded=True
    )

    assert heartbeat.state == MailboxHealthState.DEGRADED
    assert set(heartbeat.as_safe_dict()) == {
        "state",
        "observed_at",
        "pending_count",
        "stale_count",
        "oldest_pending_seconds",
    }


def test_transport_retry_policy_is_bounded() -> None:
    policy = TransportRetryPolicy(
        max_attempts=4, base_delay_seconds=2, max_delay_seconds=5
    )

    assert policy.delay_before_attempt(2) == 2
    assert policy.delay_before_attempt(3) == 4
    assert policy.delay_before_attempt(4) == 5
    assert policy.delay_before_attempt(5) is None


def test_completed_request_is_never_reexecuted(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-complete","action":"project_status","project":"demo"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    assert recovery_disposition(request, ledger.claim(request)) == RecoveryDisposition.PROCESS
    ledger.mark_completed(request)
    duplicate = ledger.claim(request)

    assert duplicate.decision == ReplayDecision.DUPLICATE
    assert duplicate.completed is True
    assert recovery_disposition(request, duplicate) == RecoveryDisposition.SKIP_COMPLETED


def test_unfinished_read_only_duplicate_can_resume_after_restart(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-read","action":"project_capabilities","project":"demo"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    ledger.claim(request)

    duplicate = BridgeReplayLedger(tmp_path / "replay.json").claim(request)
    assert duplicate.completed is False
    assert recovery_disposition(request, duplicate) == RecoveryDisposition.RETRY_IDEMPOTENT


def test_unfinished_run_tests_requires_reconciliation_not_blind_retry(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-test","action":"run_tests","project":"demo","profile":"unit"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    ledger.claim(request)

    duplicate = BridgeReplayLedger(tmp_path / "replay.json").claim(request)
    assert recovery_disposition(request, duplicate) == RecoveryDisposition.RECONCILE_REQUIRED


def test_invalid_liveness_inputs_fail_closed() -> None:
    naive = datetime(2026, 9, 20, 12, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        PendingRequestObservation("req-naive", naive)
    with pytest.raises(ValueError, match="positive"):
        build_mailbox_heartbeat([], stale_after_seconds=0)
