import json

import pytest

from runner_mcp.bridge_replay import ReplayState
from runner_mcp.bridge_resilience import (
    MAX_HEARTBEAT_BYTES,
    MAX_PENDING_OBSERVATIONS,
    BridgeResilienceError,
    RecoveryDisposition,
    RecoveryObservation,
    TransportFailureKind,
    WatcherHeartbeat,
    WatcherState,
    assess_watcher_health,
    parse_watcher_heartbeat,
    recovery_disposition,
    serialize_watcher_heartbeat,
    transport_retry_delays,
)


@pytest.mark.parametrize(
    ("has_result", "replay_state", "expected"),
    [
        (True, None, RecoveryDisposition.RESULT_EXISTS),
        (True, ReplayState.CLAIMED, RecoveryDisposition.RESULT_EXISTS),
        (True, ReplayState.COMPLETED, RecoveryDisposition.RESULT_EXISTS),
        (False, None, RecoveryDisposition.PROCESS),
        (False, ReplayState.CLAIMED, RecoveryDisposition.AMBIGUOUS_CLAIM),
        (False, ReplayState.COMPLETED, RecoveryDisposition.RESULT_MISSING),
    ],
)
def test_recovery_disposition_fails_closed_around_execution(
    has_result: bool,
    replay_state: ReplayState | None,
    expected: RecoveryDisposition,
) -> None:
    assert recovery_disposition(
        has_result=has_result,
        replay_state=replay_state,
    ) == expected


def test_healthy_heartbeat_has_no_backlog() -> None:
    heartbeat = assess_watcher_health([], stale_after_seconds=300)

    assert heartbeat == WatcherHeartbeat(
        state=WatcherState.HEALTHY,
        pending_requests=0,
        stale_requests=0,
        recovery_attention=0,
        oldest_pending_seconds=None,
    )


def test_fresh_unclaimed_request_reports_backlog() -> None:
    heartbeat = assess_watcher_health(
        [
            RecoveryObservation(
                request_id="req-301",
                age_seconds=20,
                disposition=RecoveryDisposition.PROCESS,
            )
        ],
        stale_after_seconds=300,
    )

    assert heartbeat.state == WatcherState.BACKLOG
    assert heartbeat.pending_requests == 1
    assert heartbeat.stale_requests == 0
    assert heartbeat.recovery_attention == 0
    assert heartbeat.oldest_pending_seconds == 20


def test_stale_request_degrades_watcher() -> None:
    heartbeat = assess_watcher_health(
        [
            RecoveryObservation(
                request_id="req-302",
                age_seconds=300,
                disposition=RecoveryDisposition.PROCESS,
            )
        ],
        stale_after_seconds=300,
    )

    assert heartbeat.state == WatcherState.DEGRADED
    assert heartbeat.stale_requests == 1


@pytest.mark.parametrize(
    "disposition",
    [
        RecoveryDisposition.AMBIGUOUS_CLAIM,
        RecoveryDisposition.RESULT_MISSING,
    ],
)
def test_recovery_attention_degrades_even_before_stale_threshold(
    disposition: RecoveryDisposition,
) -> None:
    heartbeat = assess_watcher_health(
        [
            RecoveryObservation(
                request_id="req-303",
                age_seconds=10,
                disposition=disposition,
            )
        ],
        stale_after_seconds=300,
    )

    assert heartbeat.state == WatcherState.DEGRADED
    assert heartbeat.recovery_attention == 1
    assert heartbeat.stale_requests == 0


def test_existing_result_is_not_counted_as_pending() -> None:
    heartbeat = assess_watcher_health(
        [
            RecoveryObservation(
                request_id="req-304",
                age_seconds=600,
                disposition=RecoveryDisposition.RESULT_EXISTS,
            )
        ],
        stale_after_seconds=300,
    )

    assert heartbeat.state == WatcherState.HEALTHY
    assert heartbeat.pending_requests == 0
    assert heartbeat.oldest_pending_seconds is None


def test_transport_failure_degrades_without_exposing_details() -> None:
    heartbeat = assess_watcher_health(
        [],
        stale_after_seconds=300,
        transport_healthy=False,
    )
    payload = heartbeat.model_dump(mode="json")

    assert heartbeat.state == WatcherState.DEGRADED
    assert payload == {
        "protocol_version": 1,
        "state": "degraded",
        "pending_requests": 0,
        "stale_requests": 0,
        "recovery_attention": 0,
        "oldest_pending_seconds": None,
    }


def test_duplicate_observations_fail_closed() -> None:
    observations = [
        RecoveryObservation(
            request_id="req-305",
            age_seconds=1,
            disposition=RecoveryDisposition.PROCESS,
        ),
        RecoveryObservation(
            request_id="req-305",
            age_seconds=2,
            disposition=RecoveryDisposition.PROCESS,
        ),
    ]

    with pytest.raises(BridgeResilienceError, match="duplicate"):
        assess_watcher_health(observations, stale_after_seconds=300)


def test_observation_count_is_bounded() -> None:
    observations = [
        RecoveryObservation(
            request_id=f"req-{index:04d}",
            age_seconds=1,
            disposition=RecoveryDisposition.PROCESS,
        )
        for index in range(MAX_PENDING_OBSERVATIONS + 1)
    ]

    with pytest.raises(BridgeResilienceError, match="too many"):
        assess_watcher_health(observations, stale_after_seconds=300)


@pytest.mark.parametrize("threshold", [29, 86_401])
def test_stale_threshold_is_bounded(threshold: int) -> None:
    with pytest.raises(BridgeResilienceError, match="threshold"):
        assess_watcher_health([], stale_after_seconds=threshold)


def test_heartbeat_round_trips() -> None:
    heartbeat = assess_watcher_health(
        [
            RecoveryObservation(
                request_id="req-306",
                age_seconds=42,
                disposition=RecoveryDisposition.PROCESS,
            )
        ],
        stale_after_seconds=300,
    )

    encoded = serialize_watcher_heartbeat(heartbeat)
    parsed = parse_watcher_heartbeat(encoded)

    assert parsed == heartbeat


def test_heartbeat_unknown_fields_fail_closed() -> None:
    heartbeat = WatcherHeartbeat(
        state=WatcherState.HEALTHY,
        pending_requests=0,
        stale_requests=0,
        recovery_attention=0,
    )
    raw = heartbeat.model_dump(mode="json")
    raw["hostname"] = "private"

    with pytest.raises(BridgeResilienceError, match="strict validation"):
        parse_watcher_heartbeat(json.dumps(raw))


def test_heartbeat_duplicate_json_keys_fail_closed() -> None:
    payload = (
        '{"protocol_version":1,"state":"healthy","state":"degraded",'
        '"pending_requests":0,"stale_requests":0,'
        '"recovery_attention":0,"oldest_pending_seconds":null}'
    )

    with pytest.raises(BridgeResilienceError, match="duplicate JSON keys"):
        parse_watcher_heartbeat(payload)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_heartbeat_non_standard_numbers_fail_closed(constant: str) -> None:
    payload = (
        '{"protocol_version":1,"state":"healthy",'
        f'"pending_requests":{constant},"stale_requests":0,'
        '"recovery_attention":0,"oldest_pending_seconds":null}'
    )

    with pytest.raises(BridgeResilienceError, match="non-standard JSON constant"):
        parse_watcher_heartbeat(payload)


def test_heartbeat_size_is_bounded() -> None:
    payload = b"{" + b" " * MAX_HEARTBEAT_BYTES + b"}"

    with pytest.raises(BridgeResilienceError, match="size limit"):
        parse_watcher_heartbeat(payload)


def test_heartbeat_consistency_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="healthy heartbeat"):
        WatcherHeartbeat(
            state=WatcherState.HEALTHY,
            pending_requests=1,
            stale_requests=0,
            recovery_attention=0,
            oldest_pending_seconds=10,
        )

    with pytest.raises(ValueError, match="must be degraded"):
        WatcherHeartbeat(
            state=WatcherState.BACKLOG,
            pending_requests=1,
            stale_requests=1,
            recovery_attention=0,
            oldest_pending_seconds=400,
        )


@pytest.mark.parametrize(
    "failure",
    [
        TransportFailureKind.TIMEOUT,
        TransportFailureKind.RATE_LIMITED,
        TransportFailureKind.UNAVAILABLE,
    ],
)
def test_transient_transport_failures_have_bounded_retries(
    failure: TransportFailureKind,
) -> None:
    assert transport_retry_delays(failure) == (2, 5)


@pytest.mark.parametrize(
    "failure",
    [
        TransportFailureKind.AUTHORIZATION,
        TransportFailureKind.INVALID_RESPONSE,
    ],
)
def test_non_transient_transport_failures_are_not_retried(
    failure: TransportFailureKind,
) -> None:
    assert transport_retry_delays(failure) == ()


def test_retry_policy_rejects_untyped_failure_kind() -> None:
    with pytest.raises(BridgeResilienceError, match="unsupported"):
        transport_retry_delays("timeout")  # type: ignore[arg-type]
