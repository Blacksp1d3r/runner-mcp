"""Strict source-only receipt gate for offline protected-release recovery.

No live restore, update, bootstrap or local filesystem authority is implemented here.
A separately qualified first-party adapter must perform the real disposable lifecycle.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from .protected_release_mirror import _admitted_readiness

_SHA = re.compile(r"^[0-9a-f]{40}$")
_SCHEMA = "runner-mcp/protected-release-restore-qualification/v1"
_PROOF = "runner-mcp/offline-disposable-release-restore/v1"


def _blocked(reason: str, qualified: int = 0) -> dict[str, Any]:
    return {
        "schemaVersion": _SCHEMA,
        "state": "blocked",
        "reasonCode": reason,
        "protectedRevisionCount": 2,
        "qualifiedRevisionCount": qualified,
        "restoreTriggered": False,
        "liveUpdateTriggered": False,
        "liveRollbackTriggered": False,
        "archiveDeleteTriggered": False,
    }


class ProtectedReleaseRestoreQualification:
    """Require exact two-release proof; no caller-selected revision or path."""

    def __init__(
        self, *,
        protected_pins: Callable[[], object],
        mirror_admission: Callable[[], Mapping[str, object]],
        mirror_verified: Callable[[str], bool],
        disposable_qualify: Callable[[str], Mapping[str, object]],
        live_transaction_state: Callable[[], object],
    ) -> None:
        self._pins = protected_pins
        self._admission = mirror_admission
        self._verified = mirror_verified
        self._qualify = disposable_qualify
        self._transaction = live_transaction_state

    def run(self) -> dict[str, Any]:
        try:
            pins = self._pins()
            if (
                not isinstance(pins, (tuple, list))
                or len(pins) != 2
                or any(not isinstance(v, str) or _SHA.fullmatch(v) is None for v in pins)
                or pins[0] == pins[1]
            ):
                return _blocked("protected-set-unavailable")
            if not _admitted_readiness(self._admission()):
                return _blocked("independent-volume-not-ready")
            before = self._transaction()
            if not isinstance(before, str) or not before:
                return _blocked("live-transaction-state-unavailable")
        except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
            return _blocked("preflight-unavailable")
        qualified = 0
        for revision in pins:
            try:
                if not _admitted_readiness(self._admission()):
                    return _blocked("independent-volume-not-ready", qualified)
                if self._verified(revision) is not True:
                    return _blocked("mirror-custody-invalid", qualified)
                evidence = self._qualify(revision)
                if (
                    not isinstance(evidence, Mapping)
                    or evidence.get("schemaVersion") != _PROOF
                    or evidence.get("commitSha") != revision
                    or evidence.get("revisionVerified") is not True
                    or evidence.get("localCustodyReaderAccepted") is not True
                    or evidence.get("offlineNetworkDisabled") is not True
                    or evidence.get("bootstrapPreflightPassed") is not True
                    or evidence.get("bootstrapApplyPassed") is not True
                    or evidence.get("bootstrapRollbackPassed") is not True
                    or evidence.get("disposableCleanupVerified") is not True
                    or evidence.get("liveMutationTriggered") is not False
                ):
                    return _blocked("disposable-proof-incomplete", qualified)
                if self._transaction() != before:
                    return _blocked("live-transaction-changed", qualified)
                qualified += 1
            except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
                return _blocked("disposable-qualification-blocked", qualified)
        try:
            if self._transaction() != before:
                return _blocked("live-transaction-changed", qualified)
        except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
            return _blocked("live-transaction-state-unavailable", qualified)
        result = _blocked("both-protected-restores-qualified", 2)
        result["state"] = "qualified"
        return result
