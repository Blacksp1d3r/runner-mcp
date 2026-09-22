"""Category-only diagnostics for long-running Runner MCP components."""

from __future__ import annotations

from enum import StrEnum


class SafeDiagnosticError(RuntimeError):
    """Raised when a diagnostic field is not part of the public safe contract."""


class DiagnosticComponent(StrEnum):
    GITHUB_WATCHER = "github_watcher"
    COMPLETION_WATCHER = "completion_watcher"
    CRON_SUPERVISOR = "cron_supervisor"


class DiagnosticEvent(StrEnum):
    LIFECYCLE_STARTED = "lifecycle_started"
    LIFECYCLE_STOPPED = "lifecycle_stopped"
    CYCLE_HEALTHY = "cycle_healthy"
    CYCLE_DEGRADED = "cycle_degraded"
    CYCLE_UNINITIALIZED = "cycle_uninitialized"
    RETRY_TIMEOUT = "retry_timeout"
    RETRY_RATE_LIMITED = "retry_rate_limited"
    RETRY_UNAVAILABLE = "retry_unavailable"
    RETRY_EXHAUSTED = "retry_exhausted"
    SUPERVISOR_RESTART_REQUESTED = "supervisor_restart_requested"
    SUPERVISOR_RESTART_HANDOFF = "supervisor_restart_handoff"
    SUPERVISOR_RESTART_FAILED = "supervisor_restart_failed"


class DiagnosticErrorCategory(StrEnum):
    BOOTSTRAP_REQUIRED = "bootstrap_required"
    RECOVERY_REQUIRED = "recovery_required"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    AUTHORIZATION = "authorization"
    INVALID_RESPONSE = "invalid_response"
    DELIVERY_FAILED = "delivery_failed"
    RESTART_FAILED = "restart_failed"
    SUPERVISOR_LOCKED = "supervisor_locked"


def render_safe_diagnostic(
    *,
    component: DiagnosticComponent,
    event: DiagnosticEvent,
    error: DiagnosticErrorCategory | None = None,
) -> str:
    """Render one bounded diagnostic line without accepting arbitrary text."""

    if not isinstance(component, DiagnosticComponent):
        raise SafeDiagnosticError("diagnostic component is not allow-listed")
    if not isinstance(event, DiagnosticEvent):
        raise SafeDiagnosticError("diagnostic event is not allow-listed")
    if error is not None and not isinstance(error, DiagnosticErrorCategory):
        raise SafeDiagnosticError("diagnostic error category is not allow-listed")

    fields = [
        f"component={component.value}",
        f"event={event.value}",
    ]
    if error is not None:
        fields.append(f"error={error.value}")
    return " ".join(fields)
