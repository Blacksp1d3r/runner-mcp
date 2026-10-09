from __future__ import annotations

import json
from hashlib import sha256

import pytest

from runner_mcp.recovery_quarantine import (
    RecoveryFailureKind,
    RecoveryQuarantineError,
    RecoveryQuarantineLedger,
    RecoveryQuarantineState,
)


def _digest(data: bytes = b"synthetic-poison") -> str:
    return sha256(data).hexdigest()


def _ledger(tmp_path):
    return RecoveryQuarantineLedger(tmp_path / "quarantine.json")


def _fail(ledger, request_id="req-poison", fingerprint=None):
    return ledger.record_failure(
        request_id=request_id,
        fingerprint=fingerprint or _digest(),
        reason=RecoveryFailureKind.INVALID_REQUEST,
    )


def test_poison_quarantined_after_three_failures_and_persists_across_restart(tmp_path):
    ledger = _ledger(tmp_path)
    assert _fail(ledger).attempts == 1
    second = _fail(_ledger(tmp_path))
    assert second.attempts == 2
    assert second.state == RecoveryQuarantineState.RETRY
    third = _fail(_ledger(tmp_path))
    assert third.attempts == 3
    assert third.state == RecoveryQuarantineState.OPERATOR_REQUIRED

    restarted = _ledger(tmp_path)
    assert restarted.inspect("req-poison") == third
    assert _fail(restarted) == third
    assert restarted.inspect("req-poison").attempts == 3


def test_new_valid_request_state_is_independent_of_quarantined_poison(tmp_path):
    ledger = _ledger(tmp_path)
    for _ in range(3):
        _fail(ledger)
    independent = _fail(ledger, request_id="req-healthy", fingerprint=_digest(b"healthy"))
    assert independent.attempts == 1
    assert independent.state == RecoveryQuarantineState.RETRY
    assert ledger.inspect("req-poison").state == RecoveryQuarantineState.OPERATOR_REQUIRED


def test_changed_fingerprint_does_not_silently_replace_quarantined_evidence(tmp_path):
    ledger = _ledger(tmp_path)
    first = _fail(ledger)
    with pytest.raises(RecoveryQuarantineError, match="identity changed"):
        _fail(ledger, fingerprint=_digest(b"changed"))
    assert ledger.inspect("req-poison") == first


def test_changed_failure_category_requires_operator(tmp_path):
    ledger = _ledger(tmp_path)
    first = _fail(ledger)
    with pytest.raises(RecoveryQuarantineError, match="reason changed"):
        ledger.record_failure(
            request_id="req-poison",
            fingerprint=_digest(),
            reason=RecoveryFailureKind.RESULT_MISSING,
        )
    assert ledger.inspect("req-poison") == first


def test_rearm_requires_explicit_approval_exact_fingerprint_and_terminal_state(tmp_path):
    ledger = _ledger(tmp_path)
    _fail(ledger)
    with pytest.raises(RecoveryQuarantineError, match="terminal record"):
        ledger.rearm(
            request_id="req-poison",
            expected_fingerprint=_digest(),
            operator_approved=True,
        )
    _fail(ledger)
    _fail(ledger)
    for approval in (False, "true", None):
        with pytest.raises(RecoveryQuarantineError, match="approval"):
            ledger.rearm(
                request_id="req-poison",
                expected_fingerprint=_digest(),
                operator_approved=approval,
            )
    with pytest.raises(RecoveryQuarantineError, match="identity mismatch"):
        ledger.rearm(
            request_id="req-poison",
            expected_fingerprint=_digest(b"changed"),
            operator_approved=True,
        )
    restored = ledger.rearm(
        request_id="req-poison",
        expected_fingerprint=_digest(),
        operator_approved=True,
    )
    assert restored.attempts == 0
    assert restored.state == RecoveryQuarantineState.RETRY
    assert _fail(_ledger(tmp_path)).attempts == 1


def test_invalid_ids_and_fingerprints_rejected_without_unsafe_file_writes(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(RecoveryQuarantineError, match="identity is invalid"):
        _fail(ledger, request_id="../escape")
    with pytest.raises(RecoveryQuarantineError, match="fingerprint is invalid"):
        _fail(ledger, fingerprint="z" * 64)
    assert not (tmp_path / "quarantine.json").exists()


def test_corrupted_disk_record_fails_closed_and_remains_on_disk(tmp_path):
    ledger = _ledger(tmp_path)
    _fail(ledger)
    path = tmp_path / "quarantine.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["records"]["req-poison"]["attempts"] = "three"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(RecoveryQuarantineError, match="retry count"):
        ledger.inspect("req-poison")
    with pytest.raises(RecoveryQuarantineError, match="retry count"):
        _fail(ledger)
    assert '"three"' in path.read_text(encoding="utf-8")


def test_symlinked_ledger_target_is_never_followed(tmp_path):
    outside = tmp_path / "outside"
    outside.write_text("other application", encoding="utf-8")
    (tmp_path / "quarantine.json").symlink_to(outside)
    with pytest.raises(RecoveryQuarantineError, match="file is unsafe"):
        _fail(_ledger(tmp_path))
    assert outside.read_text(encoding="utf-8") == "other application"


def test_broad_file_or_parent_permissions_fail_closed(tmp_path):
    ledger = _ledger(tmp_path)
    _fail(ledger)
    target = tmp_path / "quarantine.json"
    target.chmod(0o644)
    with pytest.raises(RecoveryQuarantineError, match="permissions are unsafe"):
        ledger.inspect("req-poison")
    target.chmod(0o600)
    tmp_path.chmod(0o755)
    with pytest.raises(RecoveryQuarantineError, match="directory is unsafe"):
        ledger.inspect("req-poison")


def test_capacity_exhaustion_never_evicts_historical_evidence(tmp_path):
    ledger = RecoveryQuarantineLedger(tmp_path / "quarantine.json", max_records=1)
    first = _fail(ledger)
    with pytest.raises(RecoveryQuarantineError, match="capacity exhausted"):
        _fail(ledger, request_id="req-new", fingerprint=_digest(b"new"))
    assert ledger.inspect("req-poison") == first


@pytest.mark.parametrize("bad_budget", [True, 0, 17, -1])
def test_invalid_retry_budget_is_rejected(tmp_path, bad_budget):
    with pytest.raises(RecoveryQuarantineError, match="budget"):
        RecoveryQuarantineLedger(tmp_path / "quarantine.json", failure_budget=bad_budget)
