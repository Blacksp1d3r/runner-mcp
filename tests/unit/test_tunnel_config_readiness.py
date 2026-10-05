from pathlib import Path

import pytest

from runner_mcp.onboarding import TunnelRestartConfigState
from runner_mcp.tunnel_config_readiness import collect_tunnel_config_readiness


def test_absent_tunnel_config_is_not_configured(tmp_path: Path) -> None:
    result = collect_tunnel_config_readiness(tmp_path)

    assert result.restart_config is TunnelRestartConfigState.ABSENT
    assert result.public_dict() == {
        "restart_config": "absent",
        "state": "unconfigured",
        "reason": "not_configured",
    }


@pytest.mark.parametrize(
    "content, expected_config_state",
    [
        (
            "CONTROL_PLANE_TUNNEL_ID=\nCONTROL_PLANE_API_KEY=\n",
            "incomplete",
        ),
        (
            (
                "CONTROL_PLANE_TUNNEL_ID=tunnel-placeholder\n"
                "CONTROL_PLANE_API_KEY=duplicate-credentialduplicate-credential\n"
            ),
            "structurally_invalid",
        ),
    ],
)
def test_non_complete_config_never_claims_configured(
    tmp_path: Path,
    content: str,
    expected_config_state: str,
) -> None:
    tunnel_env = tmp_path / "tunnel.env"
    tunnel_env.write_text(content, encoding="utf-8")
    tunnel_env.chmod(0o600)

    result = collect_tunnel_config_readiness(tmp_path)

    assert result.public_dict() == {
        "restart_config": expected_config_state,
        "state": "unconfigured",
        "reason": "not_configured",
    }


def test_complete_config_requires_separate_process_evidence(tmp_path: Path) -> None:
    tunnel_env = tmp_path / "tunnel.env"
    tunnel_env.write_text(
        "CONTROL_PLANE_TUNNEL_ID=tunnel-placeholder\n"
        "CONTROL_PLANE_API_KEY=api-placeholder\n",
        encoding="utf-8",
    )
    tunnel_env.chmod(0o600)

    result = collect_tunnel_config_readiness(tmp_path)

    assert result.restart_config is TunnelRestartConfigState.COMPLETE
    assert result.public_dict() == {
        "restart_config": "complete",
        "state": "configured",
        "reason": "process_not_running",
    }


def test_public_payload_has_only_bounded_fields(tmp_path: Path) -> None:
    result = collect_tunnel_config_readiness(tmp_path)

    assert set(result.public_dict()) == {
        "restart_config",
        "state",
        "reason",
    }
