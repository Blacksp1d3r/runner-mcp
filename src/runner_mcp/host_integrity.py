from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


HOST_INTEGRITY_LOOKBACK = timedelta(minutes=30)


class HostIntegrityState(StrEnum):
    CLEAR = "host_integrity_clear"
    RUNTIME_SMOKE_FAILED = "runtime_smoke_failed"
    RECENT_PROCESS_CRASH_EVIDENCE = "recent_process_crash_evidence"
    DIAGNOSTICS_UNAVAILABLE = "diagnostics_unavailable"


class FatalProcessClass(StrEnum):
    PYTHON_RUNTIME = "python_runtime"
    UNRELATED_SYSTEM_PROCESS = "unrelated_system_process"


@dataclass(frozen=True)
class FatalProcessEvidence:
    process_class: FatalProcessClass
    observed_at: datetime


class HostDiagnosticError(RuntimeError):
    pass


class HostDiagnosticAdapter:
    def recent_fatal_process_classes(
        self,
        *,
        since: datetime,
        until: datetime,
    ) -> tuple[FatalProcessEvidence, ...]: ...


class HostRuntimeIntegrityGate:
    """Local-only bounded activation decision.

    The adapter is injected deliberately: this module does not read journals,
    execute commands, enable services, or expose a remote action.
    """

    def __init__(
        self,
        *,
        diagnostics: HostDiagnosticAdapter,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._diagnostics = diagnostics
        self._now = now or (lambda: datetime.now(UTC))

    def evaluate(self, *, runtime_smoke_passed: bool) -> HostIntegrityState:
        if runtime_smoke_passed is not True:
            return HostIntegrityState.RUNTIME_SMOKE_FAILED

        until = self._now()
        if until.tzinfo is None or until.utcoffset() is None:
            return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
        since = until - HOST_INTEGRITY_LOOKBACK

        try:
            evidence = self._diagnostics.recent_fatal_process_classes(
                since=since,
                until=until,
            )
        except (HostDiagnosticError, OSError, TimeoutError, ValueError):
            return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE

        if not isinstance(evidence, tuple):
            return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE

        for event in evidence:
            if not isinstance(event, FatalProcessEvidence):
                return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
            if event.observed_at.tzinfo is None or event.observed_at.utcoffset() is None:
                return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
            if not isinstance(event.process_class, FatalProcessClass):
                return HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
            if since <= event.observed_at <= until:
                return HostIntegrityState.RECENT_PROCESS_CRASH_EVIDENCE

        return HostIntegrityState.CLEAR
