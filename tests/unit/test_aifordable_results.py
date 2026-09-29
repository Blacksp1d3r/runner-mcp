from __future__ import annotations

import hashlib
import math

import pytest

from runner_mcp.aifordable_results import (
    AIfordableDurableResult,
    AIfordableResultStore,
    AIfordableResultStoreError,
    AIfordableTerminalAction,
)

FINGERPRINT = "a" * 64


def store(tmp_path) -> AIfordableResultStore:
    root = tmp_path / "results"
    root.mkdir()
    return AIfordableResultStore(root.resolve())


def result(
    *,
    relay_version: int = 2,
    owner_generation: int = 1,
    payload: dict[str, object] | None = None,
) -> AIfordableDurableResult:
    return AIfordableDurableResult(
        request_id="cmd:test",
        fingerprint=FINGERPRINT,
        relay_version=relay_version,
        owner_generation=owner_generation,
        action=AIfordableTerminalAction.COMPLETE,
        result_code="ok",
        result_payload={"mode": "operational"} if payload is None else payload,
    )


def test_result_survives_restart_and_is_idempotent(tmp_path) -> None:
    first = store(tmp_path)
    stored = first.put(result())
    assert first.put(result()) == stored

    reopened = AIfordableResultStore((tmp_path / "results").resolve())
    assert reopened.get(stored.request_id) == stored
    assert reopened.pending() == (stored,)


def test_newer_remote_fencing_rebinds_same_result(tmp_path) -> None:
    outbox = store(tmp_path)
    outbox.put(result())

    rebound = outbox.put(result(relay_version=4, owner_generation=2))

    assert rebound.relay_version == 4
    assert rebound.owner_generation == 2
    assert rebound.result_payload == {"mode": "operational"}


def test_backwards_fencing_and_conflicting_result_fail_closed(tmp_path) -> None:
    outbox = store(tmp_path)
    outbox.put(result(relay_version=4, owner_generation=2))

    with pytest.raises(AIfordableResultStoreError, match="backwards"):
        outbox.put(result(relay_version=2, owner_generation=1))

    with pytest.raises(AIfordableResultStoreError, match="different result"):
        outbox.put(
            AIfordableDurableResult(
                request_id="cmd:test",
                fingerprint=FINGERPRINT,
                relay_version=5,
                owner_generation=3,
                action=AIfordableTerminalAction.FAIL,
                result_code="execution_failed",
                result_payload={"reason": "execution_failed"},
            )
        )


def test_acknowledge_requires_matching_fingerprint(tmp_path) -> None:
    outbox = store(tmp_path)
    stored = outbox.put(result())

    with pytest.raises(AIfordableResultStoreError, match="fingerprint"):
        outbox.acknowledge(stored.request_id, "b" * 64)

    outbox.acknowledge(stored.request_id, stored.fingerprint)
    assert outbox.get(stored.request_id) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"token": "forbidden"},
        {"nested": {"credential_value": "forbidden"}},
        {"authorization": "forbidden"},
        {"value": math.nan},
    ],
)
def test_payload_rejects_secrets_and_non_strict_json(
    payload: dict[str, object],
) -> None:
    with pytest.raises(AIfordableResultStoreError):
        result(payload=payload)


def test_corrupt_or_symlink_state_fails_closed(tmp_path) -> None:
    outbox = store(tmp_path)
    stored = outbox.put(result())
    digest = hashlib.sha256(stored.request_id.encode()).hexdigest()
    path = tmp_path / "results" / f"{digest}.json"

    path.write_text("{not-json")
    with pytest.raises(AIfordableResultStoreError, match="corrupt"):
        outbox.get(stored.request_id)

    target = tmp_path / "outside.json"
    target.write_text("{}")
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(AIfordableResultStoreError, match="unsafe"):
        outbox.get(stored.request_id)
