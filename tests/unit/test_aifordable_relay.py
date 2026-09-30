from __future__ import annotations

import json
from pathlib import Path

import pytest

from runner_mcp.aifordable_relay import (
    AIfordableRelayConfig,
    AIfordableRelayError,
    AIfordableRelayProtocolError,
    AIfordableRelayWorker,
    PendingRelayResult,
    RelayClaim,
    RelayPendingResultStore,
    _parse_claim,
)
from runner_mcp.bridge_processor import BridgeProcessState
from runner_mcp.bridge_protocol import (
    BridgeAction,
    BridgeResult,
    BridgeResultState,
    serialize_bridge_result,
)
from runner_mcp.bridge_replay import BridgeReplayLedger

NOW = 1_000


def envelope_payload(
    *,
    request_id: str = "req-runtime-001",
    target_subject: str = "runner:one",
    operation: str = "runtime_status",
) -> dict[str, object]:
    return {
        "schema_version": "aifordable.control/v1",
        "request_id": request_id,
        "target_subject": target_subject,
        "operation": operation,
        "issued_at": NOW,
        "expires_at": NOW + 300,
        "attempt": 0,
        "payload": {},
    }


def claim_payload(**kwargs) -> bytes:
    envelope = envelope_payload(**kwargs)
    encoded = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    import hashlib

    return json.dumps(
        {
            "envelope": envelope,
            "fingerprint": hashlib.sha256(encoded).hexdigest(),
            "version": 2,
            "owner_generation": 1,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def test_relay_config_requires_https_except_loopback() -> None:
    config = AIfordableRelayConfig(
        base_url="https://control.aifordable.test",
        runner_subject="runner:one",
        credential="x" * 32,
    )
    assert config.runner_subject == "runner:one"

    AIfordableRelayConfig(
        base_url="http://127.0.0.1:8080",
        runner_subject="runner:one",
        credential="x" * 32,
    )

    with pytest.raises(ValueError, match="HTTPS"):
        AIfordableRelayConfig(
            base_url="http://control.aifordable.test",
            runner_subject="runner:one",
            credential="x" * 32,
        )


def test_claim_validates_target_fingerprint_and_expiry() -> None:
    claim = _parse_claim(
        claim_payload(),
        expected_subject="runner:one",
        now_epoch=NOW,
    )

    assert claim.request_id == "req-runtime-001"
    assert claim.operation == "runtime_status"
    assert claim.bridge_request().action is BridgeAction.RUNTIME_STATUS

    with pytest.raises(AIfordableRelayProtocolError, match="target"):
        _parse_claim(
            claim_payload(target_subject="runner:two"),
            expected_subject="runner:one",
            now_epoch=NOW,
        )

    payload = json.loads(claim_payload())
    payload["fingerprint"] = "0" * 64
    with pytest.raises(AIfordableRelayProtocolError, match="fingerprint"):
        _parse_claim(
            json.dumps(payload).encode(),
            expected_subject="runner:one",
            now_epoch=NOW,
        )

    with pytest.raises(AIfordableRelayProtocolError, match="expired"):
        _parse_claim(
            claim_payload(),
            expected_subject="runner:one",
            now_epoch=NOW + 301,
        )


def test_initial_transport_rejects_unapproved_operation() -> None:
    with pytest.raises(AIfordableRelayProtocolError, match="unsupported"):
        _parse_claim(
            claim_payload(operation="run_tests"),
            expected_subject="runner:one",
            now_epoch=NOW,
        )


def test_pending_result_store_survives_restart(tmp_path: Path) -> None:
    path = (tmp_path / "pending.json").resolve()
    first = RelayPendingResultStore(path)
    result = BridgeResult(
        request_id="req-runtime-001",
        action=BridgeAction.RUNTIME_STATUS,
        state=BridgeResultState.COMPLETED,
        data={"result": {"mode": "operational"}},
    )
    pending = PendingRelayResult(
        request_id="req-runtime-001",
        version=2,
        owner_generation=1,
        result_json=serialize_bridge_result(result),
    )

    first.save(pending)
    restarted = RelayPendingResultStore(path)

    assert restarted.load() == pending
    restarted.clear()
    assert restarted.load() is None


class RecordingExecutor:
    def __init__(self) -> None:
        self.status_calls = 0
        self.doctor_calls = 0

    def runtime_status(self):
        self.status_calls += 1
        return {"mode": "operational", "projects": 5}

    def runtime_doctor(self):
        self.doctor_calls += 1
        return {"failures": 0, "warnings": 0}


class FakeTransport:
    def __init__(
        self,
        claim: RelayClaim | None,
        *,
        fail_first_publish: bool = False,
    ) -> None:
        self.claim = claim
        self.fail_first_publish = fail_first_publish
        self.claim_calls = 0
        self.publish_calls = 0
        self.published: list[PendingRelayResult] = []

    def claim_next(self):
        self.claim_calls += 1
        claim = self.claim
        self.claim = None
        return claim

    def publish(self, pending: PendingRelayResult) -> None:
        self.publish_calls += 1
        if self.fail_first_publish and self.publish_calls == 1:
            raise AIfordableRelayError("relay unavailable")
        self.published.append(pending)


def relay_claim(operation: str = "runtime_status") -> RelayClaim:
    raw = claim_payload(operation=operation)
    return _parse_claim(
        raw,
        expected_subject="runner:one",
        now_epoch=NOW,
    )


def test_worker_executes_runtime_status_once_and_returns_safe_result(
    tmp_path: Path,
) -> None:
    transport = FakeTransport(relay_claim())
    executor = RecordingExecutor()
    worker = AIfordableRelayWorker(
        transport=transport,
        ledger=BridgeReplayLedger((tmp_path / "replay.json").resolve()),
        executor=executor,
        pending_store=RelayPendingResultStore(
            (tmp_path / "pending.json").resolve()
        ),
    )

    outcome = worker.once()

    assert outcome is not None
    assert outcome.state is BridgeProcessState.COMPLETED
    assert executor.status_calls == 1
    assert transport.publish_calls == 1
    assert len(transport.published) == 1
    published = transport.published[0]
    parsed = json.loads(published.result_json)
    assert parsed["state"] == "completed"
    assert parsed["data"]["result"]["mode"] == "operational"


def test_publish_failure_retries_durable_result_without_reexecution(
    tmp_path: Path,
) -> None:
    transport = FakeTransport(
        relay_claim(),
        fail_first_publish=True,
    )
    executor = RecordingExecutor()
    replay_path = (tmp_path / "replay.json").resolve()
    pending_path = (tmp_path / "pending.json").resolve()
    worker = AIfordableRelayWorker(
        transport=transport,
        ledger=BridgeReplayLedger(replay_path),
        executor=executor,
        pending_store=RelayPendingResultStore(pending_path),
    )

    first = worker.once()

    assert first is not None
    assert first.state is BridgeProcessState.PERSISTENCE_FAILED
    assert executor.status_calls == 1
    assert RelayPendingResultStore(pending_path).load() is not None

    restarted = AIfordableRelayWorker(
        transport=transport,
        ledger=BridgeReplayLedger(replay_path),
        executor=executor,
        pending_store=RelayPendingResultStore(pending_path),
    )
    assert restarted.once() is None

    assert executor.status_calls == 1
    assert transport.publish_calls == 2
    assert RelayPendingResultStore(pending_path).load() is None


def test_runtime_doctor_uses_only_bounded_executor_method(tmp_path: Path) -> None:
    transport = FakeTransport(relay_claim("runtime_doctor"))
    executor = RecordingExecutor()
    worker = AIfordableRelayWorker(
        transport=transport,
        ledger=BridgeReplayLedger((tmp_path / "replay.json").resolve()),
        executor=executor,
        pending_store=RelayPendingResultStore(
            (tmp_path / "pending.json").resolve()
        ),
    )

    outcome = worker.once()

    assert outcome is not None
    assert outcome.state is BridgeProcessState.COMPLETED
    assert executor.doctor_calls == 1
    assert executor.status_calls == 0
