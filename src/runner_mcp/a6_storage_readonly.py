"""Strictly non-authorizing A6 local journal observation over existing Fabric MCP.

A source-only read of an already-existing journal is NOT a separate physical
failure-domain attestation, a protected host update admission, or an ACK.
"""
from __future__ import annotations

_SCHEMA = "runner.fabric/a6-storage-readonly-preflight/v1"
_REASONS = frozenset({
    "private_roots_absent", "private_binding_incomplete",
    "private_binding_invalid", "journal_root_unsafe_or_missing",
    "evidence_root_unsafe_or_missing",
    "journal_and_evidence_roots_overlap",
    "physical_independence_not_attested",
    "local_journal_unavailable_or_invalid",
    "local_journal_hash_chain_verified_only",
    "fabric_read_unavailable", "fabric_read_invalid",
})
_LOCAL_REASONS = frozenset({
    "physical_independence_not_attested",
    "local_journal_unavailable_or_invalid",
    "local_journal_hash_chain_verified_only",
})


class A6StorageReadError(ValueError):
    """Sanitized untrusted Fabric A6 read-only payload."""


def a6_storage_wait(reason: str) -> dict[str, object]:
    if type(reason) is not str or reason not in _REASONS:
        raise A6StorageReadError("invalid fixed A6 read reason")
    return {
        "schemaVersion": _SCHEMA,
        "state": "wait",
        "reasonCode": reason,
        "journalRootObserved": False,
        "evidenceRootObserved": False,
        "journalIntegrityVerified": False,
        "physicalIndependenceVerified": False,
        "offTargetReadbackVerified": False,
        "a6Ready": False,
        "mutationEnabled": False,
        "dispatchAuthorized": False,
    }


def validate_a6_storage_readonly(value: object) -> dict[str, object]:
    """Reject cross-domain, forged or over-authorizing responses without retry."""
    base = a6_storage_wait("fabric_read_invalid")
    if type(value) is not dict or set(value) != set(base):
        raise A6StorageReadError("invalid A6 response shape")
    if (type(value["schemaVersion"]) is not str or value["schemaVersion"] != _SCHEMA
            or type(value["state"]) is not str or value["state"] != "wait"
            or type(value["reasonCode"]) is not str
            or value["reasonCode"] not in _REASONS):
        raise A6StorageReadError("invalid A6 response identity")
    for key in (
        "physicalIndependenceVerified", "offTargetReadbackVerified",
        "a6Ready", "mutationEnabled", "dispatchAuthorized",
    ):
        if value[key] is not False:
            raise A6StorageReadError("unqualified A6 authority")
    for key in ("journalRootObserved", "evidenceRootObserved"):
        if type(value[key]) is not bool:
            raise A6StorageReadError("invalid A6 root status")
    if value["journalRootObserved"] is not value["evidenceRootObserved"]:
        raise A6StorageReadError("contradictory A6 root status")
    reason = value["reasonCode"]
    if value["journalRootObserved"] is not (reason in _LOCAL_REASONS):
        raise A6StorageReadError("contradictory A6 local observation")
    if value["journalIntegrityVerified"] is not (
        reason == "local_journal_hash_chain_verified_only"
    ):
        raise A6StorageReadError("contradictory A6 local integrity")
    return dict(value)
