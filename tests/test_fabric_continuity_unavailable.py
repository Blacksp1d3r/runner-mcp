from __future__ import annotations

import pytest

from runner_mcp.fabric_continuity_status import bounded_continuity_unavailable


@pytest.mark.parametrize(
    "reason",
    [
        "fabric_continuity_status_configuration_unavailable",
        "fabric_continuity_status_launcher_unavailable",
        "fabric_continuity_status_launcher_unmanaged",
        "fabric_continuity_status_unavailable",
        "fabric_continuity_status_output_invalid",
        "fabric_continuity_status_operation_failed",
    ],
)
def test_allowlisted_safe_unavailability_has_no_execution_authority(reason: str):
    result = bounded_continuity_unavailable(reason)
    assert result == {
        "schemaVersion": "runner-mcp/fabric-continuity-unavailable/v1",
        "state": "unavailable",
        "reasonCode": reason,
        "localWorkAllowed": False,
        "externalSubmissionAllowed": False,
        "reconciliationRequired": True,
        "providerMutationEnabled": False,
    }


@pytest.mark.parametrize(
    "unsafe_reason",
    [None, 123, "", "/private/path bearer secret", "fabric_continuity_status_" + "x" * 999],
)
def test_never_reflect_sensitive_or_unknown_failure_text(unsafe_reason: object):
    result = bounded_continuity_unavailable(unsafe_reason)
    assert result["state"] == "unavailable"
    assert result["reasonCode"] == "fabric_continuity_status_unavailable"
    assert "secret" not in str(result)
    assert result["localWorkAllowed"] is False
    assert result["providerMutationEnabled"] is False
