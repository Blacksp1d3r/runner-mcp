from __future__ import annotations

import pytest

from runner_mcp.a6_storage_readonly import (
    A6StorageReadError,
    a6_storage_wait,
    validate_a6_storage_readonly,
)


def test_absent_or_unavailable_a6_cannot_authorize_installation():
    for reason in ("fabric_read_unavailable", "private_roots_absent"):
        result = validate_a6_storage_readonly(a6_storage_wait(reason))
        assert result["state"] == "wait"
        assert result["a6Ready"] is False
        assert result["physicalIndependenceVerified"] is False
        assert result["mutationEnabled"] is False
        assert result["dispatchAuthorized"] is False


def test_local_hash_integrity_is_only_local_not_physical():
    payload = a6_storage_wait("local_journal_hash_chain_verified_only")
    payload.update({
        "journalRootObserved": True, "evidenceRootObserved": True,
        "journalIntegrityVerified": True,
    })
    assert validate_a6_storage_readonly(payload) == payload
    assert payload["offTargetReadbackVerified"] is False
    assert payload["a6Ready"] is False


@pytest.mark.parametrize("field,bad", [
    ("state", "ready"),
    ("schemaVersion", "other"),
    ("reasonCode", "qualified"),
    ("journalRootObserved", True),
    ("evidenceRootObserved", 1),
    ("journalIntegrityVerified", True),
    ("physicalIndependenceVerified", True),
    ("offTargetReadbackVerified", True),
    ("a6Ready", True),
    ("mutationEnabled", True),
    ("dispatchAuthorized", True),
])
def test_untrusted_a6_response_cannot_forge_independent_storage(field, bad):
    payload = a6_storage_wait("private_roots_absent")
    payload[field] = bad
    with pytest.raises(A6StorageReadError):
        validate_a6_storage_readonly(payload)


def test_unexpected_private_path_and_token_never_returned():
    payload = a6_storage_wait("private_binding_incomplete")
    payload["path"] = "/home/private/evidence"
    with pytest.raises(A6StorageReadError):
        validate_a6_storage_readonly(payload)


def test_forged_string_subclass_equality_is_not_trusted():
    class EqualString(str):
        def __eq__(self, other):
            return True

    payload = a6_storage_wait("private_roots_absent")
    payload["reasonCode"] = EqualString("local_journal_hash_chain_verified_only")
    with pytest.raises(A6StorageReadError):
        validate_a6_storage_readonly(payload)


def test_false_positive_local_integrity_without_two_roots_denied():
    payload = a6_storage_wait("local_journal_hash_chain_verified_only")
    payload["journalIntegrityVerified"] = True
    with pytest.raises(A6StorageReadError):
        validate_a6_storage_readonly(payload)


def test_absent_peer_has_same_status_as_bounded_unknown_not_green():
    assert a6_storage_wait("fabric_read_unavailable")["journalIntegrityVerified"] is False
