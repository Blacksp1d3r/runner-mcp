from __future__ import annotations

import pytest

from runner_mcp.fabric_bridge import bounded_host_inspection_unavailable


@pytest.mark.parametrize(
    "reason,category",
    [
        ("Runner Fabric host inspection failed", "fabric_inspection_unavailable"),
        ("Runner Fabric returned invalid host inspection", "invalid_inspection_payload"),
        ("Runner Fabric host inspection must be read-only", "invalid_inspection_payload"),
        ("Runner Fabric host inspection is too large", "invalid_inspection_payload"),
        ("Runner Fabric host inspection is invalid", "invalid_inspection_payload"),
        ("Runner Fabric host inspection contains private detail", "invalid_inspection_payload"),
        ("unexpected internal bridge exception", "fabric_inspection_unavailable"),
        ({"token": "fake"}, "fabric_inspection_unavailable"),
        (None, "fabric_inspection_unavailable"),
    ],
)
def test_host_inspection_failure_reports_only_safe_fixed_category(
    reason: object, category: str
):
    result = bounded_host_inspection_unavailable(reason)
    assert result == {
        "schema_version": "runner-mcp/fabric-host-inspection-error/v1",
        "state": "unavailable",
        "error_category": category,
        "mutation_enabled": False,
    }
    assert "token" not in str(result)


def test_failure_projection_requires_no_bridge_client_or_followup_probe():
    result = bounded_host_inspection_unavailable("Runner Fabric host inspection failed")
    assert result["state"] == "unavailable"
    assert result["mutation_enabled"] is False
