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
    # Malformed types / negative values fail at the existing shape guard;
    # nonpositive but well-typed state combinations fail at the claim guard.
    with pytest.raises(BlackControlEvidenceError):
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



@pytest.mark.parametrize("machine_subject", ["runner:control"])
def test_authenticated_machine_original_black_receipt_and_durable_ack(
    machine_subject,
):
    queued = sample()
    queued["request_id"] = "qual:black:runtime:v1"
    queued["requested_by_subject"] = machine_subject
    queued["requested_by_auth_strength"] = "machine"
    original = validate_black_record(queued)
    assert original["requested_by_auth_strength"] == "machine"
    assert original["requested_by_subject"] == machine_subject
    terminal = dict(
        queued,
        state="completed",
        version=3,
        owner_generation=1,
        result_code="ok",
        result_payload={"version": "0.1.30"},
        result_digest="b" * 64,
    )
    result = validate_black_record(
        terminal,
        request_id=original["request_id"],
        fingerprint=original["fingerprint"],
        requester_subject=machine_subject,
    )
    receipt = validate_black_ack(
        {
            "request_id": result["request_id"],
            "result_digest": result["result_digest"],
            "result_version": result["version"],
            "acknowledged_at": "2026-10-22T12:00:00Z",
            "state": "authenticated-requester-ack",
        },
        status=result,
    )
    after = dict(result, requester_acknowledged=True)
    confirm_black_ack_readback(status=result, ack=receipt, observed=after)


@pytest.mark.parametrize(("subject", "request_id"), [
    ("runner:black", "qual:black:runtime:v1"),
    ("runner:primary", "qual:black:runtime:v1"),
    ("runner:control-center", "qual:black:runtime:v1"),
    ("runner:aifordable-lab", "qual:black:runtime:v1"),
    ("runner:other", "qual:black:runtime:v1"),
    ("runner:control", "qual:black:other"),
    ("user:operator", "qual:black:runtime:v1"),
    ("runner:control\nspoof", "qual:black:runtime:v1"),
])
def test_machine_issuer_never_accepts_worker_foreign_request_or_subject(
    subject, request_id,
):
    raw = sample()
    raw["request_id"] = request_id
    raw["requested_by_subject"] = subject
    raw["requested_by_auth_strength"] = "machine"
    with pytest.raises(BlackControlEvidenceError):
        validate_black_record(raw)


def test_machine_proof_cannot_be_relabelled_as_human_or_lose_identity_after_ack():
    raw = sample("completed")
    raw.update(
        request_id="qual:black:runtime:v1",
        requested_by_subject="runner:control",
        requested_by_auth_strength="machine",
        version=3,
    )
    before = validate_black_record(raw)
    ack = validate_black_ack(
        {
            "request_id": before["request_id"],
            "result_digest": before["result_digest"],
            "result_version": before["version"],
            "acknowledged_at": "2026-10-22T12:00:00Z",
            "state": "authenticated-requester-ack",
        },
        status=before,
    )
    after = dict(before, requester_acknowledged=True)
    confirm_black_ack_readback(status=before, ack=ack, observed=after)
    for field, value in (
        ("requested_by_auth_strength", "mfa"),
        ("requested_by_subject", "runner:primary"),
        ("owner_generation", 2),
        ("fingerprint", "c" * 64),
        ("result_digest", "c" * 64),
    ):
        changed = dict(after, **{field: value})
        with pytest.raises(BlackControlEvidenceError):
            confirm_black_ack_readback(status=before, ack=ack, observed=changed)
