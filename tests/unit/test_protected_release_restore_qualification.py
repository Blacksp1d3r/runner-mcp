from __future__ import annotations

import pytest

from runner_mcp.protected_release_restore_qualification import (
    ProtectedReleaseRestoreQualification,
)

A = "a" * 40
B = "b" * 40


def _readiness():
    return {
        "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
        "configurationState": "configured",
        "ready": True,
        "primaryCustodyReady": True,
        "mountReady": True,
        "mirrorRootReady": True,
        "distinctDeviceReady": True,
        "mutationEnabled": False,
        "reasonCode": "ready",
    }


def _receipt(sha=A):
    return {
        "schemaVersion": "runner-mcp/offline-disposable-release-restore/v1",
        "commitSha": sha,
        "revisionVerified": True,
        "localCustodyReaderAccepted": True,
        "offlineNetworkDisabled": True,
        "bootstrapPreflightPassed": True,
        "bootstrapApplyPassed": True,
        "bootstrapRollbackPassed": True,
        "disposableCleanupVerified": True,
        "liveMutationTriggered": False,
    }


def _case(*, pins=(A, B), good=True, proof=None, transaction=None):
    calls = []
    def qualify(sha):
        calls.append(sha)
        return _receipt(sha) if proof is None else proof(sha)
    obj = ProtectedReleaseRestoreQualification(
        protected_pins=lambda: pins,
        mirror_admission=_readiness,
        mirror_verified=lambda sha: good,
        disposable_qualify=qualify,
        live_transaction_state=transaction or (lambda: "unchanged-existing-live-transaction"),
    )
    return obj, calls


def test_two_proofs_required_even_in_synthetic_fixture():
    obj, calls = _case()
    result = obj.run()
    assert result["state"] == "qualified"
    assert result["qualifiedRevisionCount"] == 2
    assert calls == [A, B]
    assert result["restoreTriggered"] is False
    assert result["liveUpdateTriggered"] is False
    assert result["liveRollbackTriggered"] is False
    assert result["archiveDeleteTriggered"] is False


@pytest.mark.parametrize("pins", [(), (A,), (A, A), ("bad", B)])
def test_bad_pins_do_not_start_qualification(pins):
    obj, calls = _case(pins=pins)
    assert obj.run()["reasonCode"] == "protected-set-unavailable"
    assert calls == []


@pytest.mark.parametrize("field", [
    "revisionVerified", "localCustodyReaderAccepted",
    "offlineNetworkDisabled", "bootstrapPreflightPassed",
    "bootstrapApplyPassed", "bootstrapRollbackPassed",
    "disposableCleanupVerified",
])
def test_each_missing_proof_blocks(field):
    obj, calls = _case(proof=lambda _sha: {**_receipt(), field: False})
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "disposable-proof-incomplete"
    assert result["qualifiedRevisionCount"] == 0
    assert calls == [A]


def test_mirror_corruption_blocks_before_offline_import():
    obj, calls = _case(good=False)
    assert obj.run()["reasonCode"] == "mirror-custody-invalid"
    assert calls == []


def test_one_failed_second_revision_is_not_success():
    def second(sha):
        return _receipt(sha) if sha == A else {**_receipt(sha), "bootstrapRollbackPassed": False}
    obj, calls = _case(proof=second)
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["qualifiedRevisionCount"] == 1
    assert calls == [A, B]


def test_transaction_change_cannot_be_accepted():
    states = iter(["original", "original", "changed"])
    obj, _ = _case(transaction=lambda: next(states))
    result = obj.run()
    assert result["reasonCode"] == "live-transaction-changed"
    assert result["state"] == "blocked"


def test_private_failure_detail_is_not_exposed():
    def fail(_sha):
        raise OSError("/private/path secret=never-log")
    obj, _ = _case(proof=fail)
    result = obj.run()
    assert result["state"] == "blocked"
    assert "private" not in str(result)
    assert "secret" not in str(result)


def test_wrong_revision_receipt_cannot_qualify_second_pin():
    obj, calls = _case(proof=lambda _sha: _receipt(A))
    result = obj.run()
    assert result["reasonCode"] == "disposable-proof-incomplete"
    assert result["qualifiedRevisionCount"] == 1
    assert calls == [A, B]
