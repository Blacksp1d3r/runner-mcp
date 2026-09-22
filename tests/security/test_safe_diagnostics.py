from __future__ import annotations

import re

import pytest

from runner_mcp.safe_diagnostics import (
    DiagnosticComponent,
    DiagnosticErrorCategory,
    DiagnosticEvent,
    SafeDiagnosticError,
    render_safe_diagnostic,
)


def test_safe_diagnostic_renders_only_allowlisted_categories() -> None:
    assert render_safe_diagnostic(
        component=DiagnosticComponent.GITHUB_WATCHER,
        event=DiagnosticEvent.RETRY_TIMEOUT,
        error=DiagnosticErrorCategory.TIMEOUT,
    ) == "component=github_watcher event=retry_timeout error=timeout"


def test_required_diagnostic_event_groups_are_present() -> None:
    values = {item.value for item in DiagnosticEvent}
    assert {
        "lifecycle_started",
        "lifecycle_stopped",
        "cycle_healthy",
        "cycle_degraded",
        "cycle_uninitialized",
        "retry_timeout",
        "retry_rate_limited",
        "retry_unavailable",
        "retry_exhausted",
        "supervisor_restart_requested",
        "supervisor_restart_handoff",
        "supervisor_restart_failed",
    } <= values


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("component", "/srv/private/project"),
        ("event", "https://example.invalid/?token=secret-value"),
        ("error", "secret-value"),
    ],
)
def test_dynamic_sensitive_literals_are_rejected_without_echo(
    field: str,
    value: str,
) -> None:
    kwargs = {
        "component": DiagnosticComponent.GITHUB_WATCHER,
        "event": DiagnosticEvent.CYCLE_DEGRADED,
        "error": DiagnosticErrorCategory.RECOVERY_REQUIRED,
    }
    kwargs[field] = value

    with pytest.raises(SafeDiagnosticError) as caught:
        render_safe_diagnostic(**kwargs)

    assert value not in str(caught.value)
    assert "secret-value" not in str(caught.value)


def test_contract_values_are_bounded_identifier_categories() -> None:
    pattern = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
    values = [
        *(item.value for item in DiagnosticComponent),
        *(item.value for item in DiagnosticEvent),
        *(item.value for item in DiagnosticErrorCategory),
    ]
    assert values
    assert all(pattern.fullmatch(value) for value in values)


def test_renderer_has_no_arbitrary_message_or_context_channel() -> None:
    with pytest.raises(TypeError):
        render_safe_diagnostic(
            component=DiagnosticComponent.COMPLETION_WATCHER,
            event=DiagnosticEvent.CYCLE_HEALTHY,
            message="token=secret-value",
        )
