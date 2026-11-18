"""Fail-closed adapter for existing read-only MCP status/Doctor dependencies.

This is only an exception/shape boundary, not host attestation or update admission.
A private exception or malformed response must never be presented as healthy.
"""

from __future__ import annotations

from collections.abc import Callable


def bounded_status_object(reader: Callable[[], object]) -> dict[str, object] | None:
    """Return an ordinary dictionary or None, never expose private error text."""
    try:
        observed = reader()
    except (OSError, RuntimeError, ValueError, TypeError, AttributeError, KeyError):
        return None
    if type(observed) is not dict:
        return None
    return observed
