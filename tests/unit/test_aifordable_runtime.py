from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.aifordable_results import AIfordableResultStore
from runner_mcp.aifordable_runtime import (
    AIfordableWatcherOutcome,
    AIfordableWatcherRuntime,
    AIfordableWatcherState,
)
from runner_mcp.aifordable_transport import (
    AIfordableClaim,
    AIfordableControlOperation,
    AIfordableEnvelope,
    AIfordableTransportError,
)
from runner_mcp.bridge_processor import BridgeExecutionAdapterError


class FakeExecutor:
    def __init__(self) -> None:
        self.status_calls = 0
        self.doctor_calls = 0
        self.fail = False

    def runtime_status(self):
        self.status_calls += 1
        if self.fail:
            raise BridgeExecutionAdapterError("private detail")
        return {"mode": "operational", "projects": 5}

    def runtime_doctor(self):
        self.doctor_calls += 1
        if self.fail:
            raise BridgeExecutionAdapterError("private detail")
        return {"failures": 0, "warnings": 0}


class FakeRelay:
    def __init__(self, claims: list[AIfordableClaim | None]) -> None:
        self.claims = list(claims)
        self.submissions: list[dict[str, object]] = []
        self.submit_errors: list[AIfordableTransportError] = []

    def claim_once(self, *, now: int) -> AIfordableClaim | None:
        del now
        if not self.claims:
            return None
        return self.claims.pop(0)

    def submit_terminal_result(self, **kwargs) -> None:
        self.submissions.append(dict(kwargs))
        if self.submit_errors:
            raise self.submit_errors.pop(0)


def claim(
    *,
    request_id: str = "cmd:test",
    operation: AIfordableControlOperation = AIfordableControlOperation.RUNTIME_STATUS,
    payload: dict[str, object] | None = None,
    version: int = 2,
    owner_generation: int = 1,
) -> AIfordableClaim:
    envelope = AIfordableEnvelope(
        request_id=request_id,
        target_subject="runner:primary",
        operation=operation,
        issued_at=1_000,
        expires_at=1_300,
        attempt=0,
        payload={} if payload is None else payload,
    )
    return AIfordableClaim(
        envelope=envelope,
        fingerprint=envelope.fingerprint,
        version=version,
        owner_generation=owner_generation,
    )


def result_store(tmp_path: Path) -> AIfordableResultStore:
    root = tmp_path / "results"
    root.mkdir()
    return AIfordableResultStore(root.resolve())


def runtime(
    tmp_path: Path,
    relay: FakeRelay,
    executor: FakeExecutor | None = None,
) -> tuple[AIfordableWatcherRuntime, FakeExecutor]:
    actual_executor = executor or FakeExecutor()
    return (
        AIfordableWatcherRuntime(
            relay=relay,  # type: ignore[arg-type]
            executor=actual_executor,
            results=result_store(tmp_path),
            subject="runner:primary",
        ),
        actual_executor,
    )


def test_runtime_status_completes_and_acks(tmp_path: Path) -> None:
    relay = FakeRelay([claim()])
    watcher, executor = runtime(tmp_path, relay)

    outcome = watcher.run_once(now=1_100)

    assert outcome == AIfordableWatcherOutcome(
        state=AIfordableWatcherState.COMPLETED,
        request_id="cmd:test",
        operation=AIfordableControlOperation.RUNTIME_STATUS,
    )
    assert executor.status_calls == 1
    assert relay.submissions[0]["action"] == "complete"
    assert relay.submissions[0]["result_code"] == "ok"
    assert relay.submissions[0]["result_payload"] == {
        "result": {"mode": "operational", "projects": 5}
    }
    assert watcher.results.pending() == ()


def test_runtime_doctor_completes(tmp_path: Path) -> None:
    relay = FakeRelay(
        [
            claim(
                operation=AIfordableControlOperation.RUNTIME_DOCTOR,
            )
        ]
    )
    watcher, executor = runtime(tmp_path, relay)

    outcome = watcher.run_once(now=1_100)

    assert outcome.state is AIfordableWatcherState.COMPLETED
    assert executor.doctor_calls == 1
    assert relay.submissions[0]["result_payload"] == {
        "result": {"failures": 0, "warnings": 0}
    }


def test_known_execution_failure_is_sanitized(tmp_path: Path) -> None:
    relay = FakeRelay([claim()])
    executor = FakeExecutor()
    executor.fail = True
    watcher, _ = runtime(tmp_path, relay, executor)

    outcome = watcher.run_once(now=1_100)

    assert outcome.state is AIfordableWatcherState.COMPLETED
    assert relay.submissions[0]["action"] == "fail"
    assert relay.submissions[0]["result_code"] == "execution_failed"
    assert relay.submissions[0]["result_payload"] == {
        "reason": "execution_failed"
    }


def test_fabric_mutation_stays_reserved(tmp_path: Path) -> None:
    relay = FakeRelay(
        [
            claim(
                operation=AIfordableControlOperation.FABRIC_RUN_WORK_UNIT,
                payload={
                    "work_unit_id": "wu:test",
                    "project_id": "project:test",
                    "work_item_id": "issue:test",
                    "expected_revision": "a" * 40,
                    "change_plan_id": "plan:test",
                },
            )
        ]
    )
    watcher, executor = runtime(tmp_path, relay)

    outcome = watcher.run_once(now=1_100)

    assert outcome.state is AIfordableWatcherState.COMPLETED
    assert executor.status_calls == 0
    assert executor.doctor_calls == 0
    assert relay.submissions[0]["action"] == "fail"
    assert relay.submissions[0]["result_code"] == "fabric_control_reserved"


def test_lost_result_ack_is_replayed_without_reexecution(tmp_path: Path) -> None:
    relay = FakeRelay([claim(), None])
    relay.submit_errors.append(
        AIfordableTransportError("relay unavailable")
    )
    watcher, executor = runtime(tmp_path, relay)

    first = watcher.run_once(now=1_100)

    assert first.state is AIfordableWatcherState.DEFERRED
    assert executor.status_calls == 1
    assert len(watcher.results.pending()) == 1

    second = watcher.run_once(now=1_101)

    assert second.state is AIfordableWatcherState.REPLAYED
    assert executor.status_calls == 1
    assert watcher.results.pending() == ()
    assert len(relay.submissions) == 2


def test_stale_result_rebinds_to_new_claim_without_reexecution(
    tmp_path: Path,
) -> None:
    initial = claim()
    reclaimed = claim(version=4, owner_generation=2)
    relay = FakeRelay([initial, reclaimed])
    relay.submit_errors.extend(
        [
            AIfordableTransportError("relay unavailable"),
            AIfordableTransportError(
                "relay state conflicted",
                status=409,
            ),
        ]
    )
    watcher, executor = runtime(tmp_path, relay)

    assert watcher.run_once(now=1_100).state is AIfordableWatcherState.DEFERRED
    second = watcher.run_once(now=1_200)

    assert second.state is AIfordableWatcherState.REPLAYED
    assert executor.status_calls == 1
    assert watcher.results.pending() == ()
    assert relay.submissions[-1]["expected_version"] == 4
    assert relay.submissions[-1]["owner_generation"] == 2


def test_mismatched_reclaim_fingerprint_requires_recovery(
    tmp_path: Path,
) -> None:
    first = claim()
    other = claim(
        request_id="cmd:other",
        operation=AIfordableControlOperation.RUNTIME_DOCTOR,
    )
    relay = FakeRelay([first, other])
    relay.submit_errors.extend(
        [
            AIfordableTransportError("relay unavailable"),
            AIfordableTransportError(
                "relay state conflicted",
                status=409,
            ),
        ]
    )
    watcher, executor = runtime(tmp_path, relay)

    assert watcher.run_once(now=1_100).state is AIfordableWatcherState.DEFERRED
    second = watcher.run_once(now=1_200)

    assert second.state is AIfordableWatcherState.RECOVERY_REQUIRED
    assert executor.status_calls == 1
    assert executor.doctor_calls == 0


def test_idle_does_not_execute(tmp_path: Path) -> None:
    relay = FakeRelay([None])
    watcher, executor = runtime(tmp_path, relay)

    outcome = watcher.run_once(now=1_100)

    assert outcome.state is AIfordableWatcherState.IDLE
    assert executor.status_calls == 0
    assert executor.doctor_calls == 0
