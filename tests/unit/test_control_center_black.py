"""Pure fail-closed issuer correlation tests; no relay/network/credential."""
from __future__ import annotations

import pytest

from runner_mcp.control_center_black import (
    BlackControlEvidenceError,
    confirm_black_ack_readback,
    validate_black_ack,
    validate_black_record,
)


def sample(state="queued"):
    terminal = state in {"completed", "failed"}
    return {
        "request_id": "black-req-001",
        "target_subject": "runner:black",
        "operation": "runtime_status",
        "fingerprint": "a" * 64,
        "requested_by_subject": "operator-one",
        "requested_by_auth_strength": "mfa",
        "state": state,
        "version": 2,
        "owner_generation": 1 if terminal else 0,
        "result_code": "completed" if terminal else None,
        "result_payload": {"version": "0.1.30"} if terminal else None,
        "result_digest": "b" * 64 if terminal else None,
        "requester_acknowledged": False,
    }


def test_original_issuer_receipt_and_terminal_ack():
    original = validate_black_record(sample())
    result = validate_black_record(
        sample("completed"),
        request_id=original["request_id"],
        fingerprint=original["fingerprint"],
        requester_subject=original["requested_by_subject"],
    )
    receipt = validate_black_ack(
        {
            "request_id": result["request_id"],
            "result_digest": result["result_digest"],
            "result_version": result["version"],
            "acknowledged_at": "2026-10-22T10:00:00Z",
            "state": "authenticated-requester-ack",
        },
        status=result,
    )
    assert receipt["target_subject"] == "runner:black"
    assert receipt["result_digest"] == "b" * 64


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_subject", "runner:primary"),
        ("operation", "runtime_doctor"),
        ("requested_by_auth_strength", "password"),
        ("requested_by_subject", "foreign-operator"),
        ("fingerprint", "c" * 64),
        ("request_id", "another-request"),
        ("version", True),
        ("requester_acknowledged", True),
        ("result_digest", "c" * 64),
    ],
)
def test_wrong_identity_or_unproven_state_rejected(field, value):
    raw = sample()
    raw[field] = value
    with pytest.raises(BlackControlEvidenceError):
        validate_black_record(
            raw, request_id="black-req-001",
            fingerprint="a" * 64,
            requester_subject="operator-one",
        )


def test_secret_result_and_implicit_ack_rejected():
    raw = sample("completed")
    raw["result_payload"]["operator_token"] = "never"
    with pytest.raises(BlackControlEvidenceError):
        validate_black_record(raw)
    raw = sample("queued")
    raw["requester_acknowledged"] = True
    with pytest.raises(BlackControlEvidenceError):
        validate_black_record(raw)


@pytest.mark.parametrize("field,value", [
    ("request_id", "different"),
    ("result_digest", "c" * 64),
    ("result_version", 1),
    ("state", "complete"),
])
def test_wrong_ack_never_accepted(field, value):
    status = validate_black_record(sample("completed"))
    ack = {
        "request_id": "black-req-001",
        "result_digest": "b" * 64,
        "result_version": 2,
        "acknowledged_at": "2026-10-22T10:00:00Z",
        "state": "authenticated-requester-ack",
    }
    ack[field] = value
    with pytest.raises(BlackControlEvidenceError):
        validate_black_ack(ack, status=status)


@pytest.mark.parametrize(
    ("state", "generation"),
    [
        ("queued", 1),
        ("claimed", 0),
        ("completed", 0),
        ("failed", 0),
        ("claimed", -1),
        ("completed", True),
    ],
)
def test_worker_claim_generation_must_match_queue_state(state, generation):
    raw = sample(state)
    raw["owner_generation"] = generation
    with pytest.raises(BlackControlEvidenceError, match="generation"):
        validate_black_record(raw)


def test_real_claimed_and_terminal_records_remain_valid():
    for state in ("queued", "claimed", "completed", "failed"):
        raw = sample(state)
        if state == "claimed":
            raw["owner_generation"] = 1
        assert validate_black_record(raw)["state"] == state


def _terminal_ack_fixture():
    original = validate_black_record(sample("completed"))
    ack = validate_black_ack(
        {
            "request_id": original["request_id"],
            "result_digest": original["result_digest"],
            "result_version": original["version"],
            "acknowledged_at": "2026-10-22T10:00:00Z",
            "state": "authenticated-requester-ack",
        },
        status=original,
    )
    returned = dict(original, requester_acknowledged=True)
    return original, ack, returned


def test_post_ack_readback_same_original_generation_and_requester():
    before, ack, after = _terminal_ack_fixture()
    confirm_black_ack_readback(status=before, ack=ack, observed=after)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("owner_generation", 2),
        ("requested_by_subject", "other-requester"),
        ("fingerprint", "e" * 64),
        ("request_id", "other-request"),
        ("target_subject", "runner:primary"),
        ("operation", "runtime_doctor"),
        ("version", 3),
        ("result_digest", "f" * 64),
        ("result_code", "bridge_failed"),
        ("requester_acknowledged", False),
        ("state", "claimed"),
    ],
)
def test_post_ack_readback_changed_lineage_rejected(field, value):
    before, ack, after = _terminal_ack_fixture()
    after[field] = value
    with pytest.raises(BlackControlEvidenceError, match="durably correlated"):
        confirm_black_ack_readback(status=before, ack=ack, observed=after)


def test_post_ack_readback_foreign_ack_rejected():
    before, ack, after = _terminal_ack_fixture()
    ack["requested_by_subject"] = "foreign"
    with pytest.raises(BlackControlEvidenceError, match="durably correlated"):
        confirm_black_ack_readback(status=before, ack=ack, observed=after)
