"""Q7 communication failures distinguish pre-run denial from unknown effects."""

import pytest

from runner_mcp.fabric_coding_availability import (
    FabricCodingAvailabilityQualificationError,
    bounded_qualification_failure,
)
from runner_mcp.operational_safety import (
    OperatorStopActive,
    SafetyConfigurationError,
)


@pytest.mark.parametrize(
    ("error", "state", "reason", "effect"),
    [
        (OperatorStopActive("private-stop-name"), "blocked",
         "operator_stop_active", "not_started"),
        (SafetyConfigurationError("/private/retention-status"), "blocked",
         "operator_safety_unqualified", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_case_invalid"),
         "blocked", "invalid_fixed_case", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_revision_invalid"),
         "blocked", "invalid_fixed_revision", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_launcher_unavailable"),
         "wait", "fabric_launcher_unqualified", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_launcher_unmanaged"),
         "wait", "fabric_launcher_unqualified", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_config_unavailable"),
         "wait", "q7_private_configuration_incomplete", "not_started"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_unavailable"),
         "unknown", "q7_execution_unverified", "unknown"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_failed"),
         "unknown", "q7_execution_unverified", "unknown"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_output_invalid"),
         "unknown", "q7_output_unverified", "unknown"),
        (FabricCodingAvailabilityQualificationError(
            "/private/workspace token=NEVER_EXPOSE"),
         "unknown", "q7_execution_unverified", "unknown"),
        (RuntimeError("provider secret /private/token"), "unknown",
         "q7_execution_unverified", "unknown"),
        (FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_failed",
            "/private/output"),
         "unknown", "q7_execution_unverified", "unknown"),
    ],
)
def test_qualification_failure_is_bounded_and_never_dispatches_or_retries(
    error, state, reason, effect,
):
    report = bounded_qualification_failure(error)
    assert report == {
        "schemaVersion": "runner-mcp/coding-availability-qualification-unavailable/v1",
        "state": state,
        "reason_code": reason,
        "result_verified": False,
        "qualification_effect": effect,
        "dispatch_authorized": False,
        "retry_authorized": False,
    }
    assert "/private" not in str(report)
    assert "NEVER_EXPOSE" not in str(report)
    assert "token" not in str(report)
    assert "provider" not in str(report)


def test_failure_report_never_mimics_successful_fabric_q7_schema():
    report = bounded_qualification_failure(
        FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_output_invalid"
        )
    )
    assert report["state"] == "unknown"
    assert report["qualification_effect"] == "unknown"
    assert "assignment_requests" not in report
    assert "workspace_clean" not in report
    assert "expected_revision" not in report
