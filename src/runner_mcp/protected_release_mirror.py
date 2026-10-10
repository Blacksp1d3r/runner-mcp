"""Fail-closed orchestration for exactly the privately pinned Fabric release pair.

This component has no MCP arguments, filesystem paths, shell authority or installer.
The managed Fabric adapter remains a separate topology-qualified integration gate.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_SCHEMA = "runner-mcp/protected-release-archive-mirror/v1"
_SHA = re.compile(r"^[0-9a-f]{40}$")
_SCOPE = "protected-release-archive-mirror"


class ProtectedReleaseMirrorBlocked(RuntimeError):
    """A bounded refusal that must not expose private storage details."""


def _result(
    reason: str, *,
    state: str = "blocked",
    copied: int = 0,
    verified: int = 0,
    already: int = 0,
    device_ready: bool = False,
) -> dict[str, Any]:
    return {
        "schemaVersion": _SCHEMA,
        "state": state,
        "protectedRevisionCount": 2,
        "mirroredCount": copied,
        "verifiedCount": verified,
        "alreadyStoredCount": already,
        "separateDeviceReady": device_ready,
        "reasonCode": reason,
        "mutationScope": _SCOPE,
        "restoreTriggered": False,
        "updateTriggered": False,
        "deleteTriggered": False,
    }


class ProtectedReleaseMirror:
    """Call only a prebound, first-party per-revision custody operation."""

    def __init__(
        self, *,
        safety: OperatorSafetyGuard,
        readiness: Callable[[], Mapping[str, object]],
        protected_pins: Callable[[], object],
        verify_primary: Callable[[str], bool],
        mirror_exact: Callable[[str], Mapping[str, object]],
        verify_secondary: Callable[[str], bool],
    ) -> None:
        self._safety = safety
        self._readiness = readiness
        self._pins = protected_pins
        self._verify_primary = verify_primary
        self._mirror_exact = mirror_exact
        self._verify_secondary = verify_secondary

    def run(self) -> dict[str, Any]:
        try:
            self._safety.assert_action_allowed(ActionClass.BACKUP)
        except (OSError, RuntimeError, ValueError):
            return _result("operator-safety-blocked")

        try:
            pins = self._pins()
            if (
                not isinstance(pins, (tuple, list))
                or len(pins) != 2
                or any(not isinstance(v, str) or _SHA.fullmatch(v) is None for v in pins)
                or pins[0] == pins[1]
            ):
                return _result("protected-set-unavailable")
            if self._readiness().get("ready") is not True:
                return _result("independent-volume-not-ready")
            for revision in pins:
                if self._verify_primary(revision) is not True:
                    return _result("primary-custody-invalid", device_ready=True)
        except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
            return _result("preflight-unavailable")

        copied = already = verified = 0
        for revision in pins:
            try:
                self._safety.assert_action_allowed(ActionClass.BACKUP)
                if self._readiness().get("ready") is not True:
                    return _result(
                        "independent-volume-not-ready", copied=copied,
                        already=already, verified=verified,
                    )
                evidence = self._mirror_exact(revision)
                if (
                    evidence.get("separateDevice") is not True
                    or not isinstance(evidence.get("alreadyStored"), bool)
                ):
                    return _result(
                        "mirror-evidence-invalid", copied=copied,
                        already=already, verified=verified, device_ready=True,
                    )
                if self._verify_secondary(revision) is not True:
                    return _result(
                        "secondary-custody-invalid", copied=copied,
                        already=already, verified=verified, device_ready=True,
                    )
                verified += 1
                if evidence["alreadyStored"]:
                    already += 1
                else:
                    copied += 1
            except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
                return _result(
                    "mirror-operation-blocked", copied=copied,
                    already=already, verified=verified,
                )
        return _result(
            "protected-set-verified", state="verified",
            copied=copied, already=already, verified=verified, device_ready=True,
        )
