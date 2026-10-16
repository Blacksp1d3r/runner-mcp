from __future__ import annotations

import pytest

from runner_mcp.tunnel_readiness import (
    TunnelReadinessEvidence,
    bounded_doctor_tunnel_check,
)


def test_opt_in_only_missing_tunnel_does_not_warn_without_expectation():
    assert bounded_doctor_tunnel_check(expected=False) is None


def test_expected_tunnel_without_collector_is_warn_unavailable():
    assert bounded_doctor_tunnel_check(expected=True) == ("warn", "evidence_unavailable")


def test_configured_but_not_running_is_visible():
    assert bounded_doctor_tunnel_check(
        expected=True,
        evidence_provider=lambda: TunnelReadinessEvidence(
            configured=True, process_running=False
        ),
    ) == ("warn", "process_not_running")


def test_unconfigured_expected_tunnel_is_visible():
    assert bounded_doctor_tunnel_check(
        expected=True,
        evidence_provider=lambda: TunnelReadinessEvidence(configured=False),
    ) == ("warn", "not_configured")


def test_running_but_unauthenticated_is_visible():
    assert bounded_doctor_tunnel_check(
        expected=True,
        evidence_provider=lambda: TunnelReadinessEvidence(
            configured=True, process_running=True, local_mcp_ready=True,
        ),
    ) == ("warn", "control_plane_not_authenticated")


def test_strict_positive_evidence_only_case_that_passes():
    assert bounded_doctor_tunnel_check(
        expected=True,
        evidence_provider=lambda: TunnelReadinessEvidence(
            configured=True,
            process_running=True,
            local_mcp_ready=True,
            control_plane_authenticated=True,
            end_to_end_routable=True,
        ),
    ) == ("pass", "routable")


def test_inconsistent_evidence_fails_closed():
    assert bounded_doctor_tunnel_check(
        expected=True,
        evidence_provider=lambda: TunnelReadinessEvidence(
            configured=False,
            process_running=True,
        ),
    ) == ("warn", "inconsistent_evidence")


def test_private_exception_never_leaks_into_doctor():
    def sensitive_collector() -> TunnelReadinessEvidence:
        raise OSError("private-path: /not/to/be/printed token=123")

    result = bounded_doctor_tunnel_check(
        expected=True, evidence_provider=sensitive_collector
    )
    assert result == ("warn", "evidence_unavailable")
    assert "token" not in str(result)


@pytest.mark.parametrize("incorrect", ["false", 1, None])
def test_nonboolean_expected_marker_is_rejected(incorrect: object):
    with pytest.raises(TypeError):
        bounded_doctor_tunnel_check(expected=incorrect)


def test_malformed_collector_result_fails_closed():
    assert bounded_doctor_tunnel_check(
        expected=True, evidence_provider=lambda: {"configured": True}
    ) == ("warn", "evidence_unavailable")
