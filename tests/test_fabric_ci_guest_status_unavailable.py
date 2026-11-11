from __future__ import annotations

import pytest

from runner_mcp.fabric_bridge import bounded_ci_guest_status_unavailable


@pytest.mark.parametrize(
    ("reason", "code"),
    [
        ("Runner Fabric CI guest request failed", "ci_guest_status_unavailable"),
        ("Runner Fabric returned invalid CI guest result", "ci_guest_status_invalid_payload"),
        ("Runner Fabric CI guest result contains private detail", "ci_guest_status_invalid_payload"),
        ("Runner Fabric CI guest result is too large", "ci_guest_status_invalid_payload"),
        ("/private/host/token=secret", "ci_guest_status_unavailable"),
        ({"token": "secret"}, "ci_guest_status_unavailable"),
        (None, "ci_guest_status_unavailable"),
    ],
)
def test_optional_guest_status_fails_closed_without_host_claim(
    reason: object, code: str,
) -> None:
    result = bounded_ci_guest_status_unavailable(reason)
    assert result == {
        "schema_version": "runner-mcp/fabric-ci-guest-status-error/v1",
        "state": "unavailable",
        "reason_code": code,
        "guest_registered": None,
        "guest_running": None,
        "mutation_enabled": False,
        "execution_enabled": False,
    }
    assert "secret" not in repr(result)
    assert "/private" not in repr(result)


def test_absent_guest_status_never_implies_false_guest_inventory() -> None:
    result = bounded_ci_guest_status_unavailable("unsupported optional peer capability")
    assert result["guest_registered"] is None
    assert result["guest_running"] is None
    assert result["execution_enabled"] is False
