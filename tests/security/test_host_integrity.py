from __future__ import annotations

import datetime

import runner_mcp.host_integrity as hi


NOW = datetime.datetime(2026, 9, 30, 8, 0, tzinfo=datetime.UTC)


class FakeDiagnostics:
    def __init__(self, evidence=()) -> None:
        self.evidence = evidence
        self.calls = []

    def recent_fatal_process_classes(self, *, since, until):
        self.calls.append((since, until))
        if isinstance(self.evidence, Exception):
            raise self.evidence
        return self.evidence


def gate(adapter: FakeDiagnostics) -> hi.HostRuntimeIntegrityGate:
    return hi.HostRuntimeIntegrityGate(diagnostics=adapter, now=lambda: NOW)


def test_clear_requires_passing_runtime_smoke_and_clean_window() -> None:
    adapter = FakeDiagnostics()

    assert gate(adapter).evaluate(runtime_smoke_passed=True) == hi.HostIntegrityState.CLEAR
    assert adapter.calls == [(NOW - hi.HOST_INTEGRITY_LOOKBACK, NOW)]


def test_runtime_smoke_failure_dominates_without_querying_diagnostics() -> None:
    adapter = FakeDiagnostics(
        (
            hi.FatalProcessEvidence(hi.FatalProcessClass.PYTHON_RUNTIME, NOW),
        )
    )

    assert (
        gate(adapter).evaluate(runtime_smoke_passed=False)
        == hi.HostIntegrityState.RUNTIME_SMOKE_FAILED
    )
    assert adapter.calls == []


def test_recent_python_crash_blocks_activation() -> None:
    adapter = FakeDiagnostics(
        (
            hi.FatalProcessEvidence(
                hi.FatalProcessClass.PYTHON_RUNTIME,
                NOW - datetime.timedelta(minutes=2),
            ),
        )
    )

    assert (
        gate(adapter).evaluate(runtime_smoke_passed=True)
        == hi.HostIntegrityState.RECENT_PROCESS_CRASH_EVIDENCE
    )


def test_recent_unrelated_system_crash_blocks_activation() -> None:
    adapter = FakeDiagnostics(
        (
            hi.FatalProcessEvidence(
                hi.FatalProcessClass.UNRELATED_SYSTEM_PROCESS,
                NOW - datetime.timedelta(minutes=29),
            ),
        )
    )

    assert (
        gate(adapter).evaluate(runtime_smoke_passed=True)
        == hi.HostIntegrityState.RECENT_PROCESS_CRASH_EVIDENCE
    )


def test_old_crash_does_not_block_after_clean_window() -> None:
    adapter = FakeDiagnostics(
        (
            hi.FatalProcessEvidence(
                hi.FatalProcessClass.PYTHON_RUNTIME,
                NOW - datetime.timedelta(minutes=31),
            ),
        )
    )

    assert gate(adapter).evaluate(runtime_smoke_passed=True) == hi.HostIntegrityState.CLEAR


def test_unavailable_diagnostics_fail_closed_without_leaking_exception() -> None:
    adapter = FakeDiagnostics(hi.HostDiagnosticError("private host path / secret detail"))

    result = gate(adapter).evaluate(runtime_smoke_passed=True)

    assert result == hi.HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
    assert "private" not in result.value
    assert "secret" not in result.value


def test_malformed_adapter_result_fails_closed() -> None:
    adapter = FakeDiagnostics(["raw journal line"])

    assert (
        gate(adapter).evaluate(runtime_smoke_passed=True)
        == hi.HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
    )


def test_naive_event_timestamp_fails_closed() -> None:
    adapter = FakeDiagnostics(
        (
            hi.FatalProcessEvidence(
                hi.FatalProcessClass.PYTHON_RUNTIME,
                datetime.datetime(2026, 9, 30, 7, 59).replace(tzinfo=None),  # noqa: DTZ001
            ),
        )
    )

    assert (
        gate(adapter).evaluate(runtime_smoke_passed=True)
        == hi.HostIntegrityState.DIAGNOSTICS_UNAVAILABLE
    )
