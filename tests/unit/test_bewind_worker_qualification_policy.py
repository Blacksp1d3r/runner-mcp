from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.bewind_worker_qualification_policy import (
    BewindWorkerQualificationPolicyConfigurator,
    BewindWorkerQualificationPolicyError,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def _safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def _target() -> dict:
    return {
        "mode": "af14-disposable-v1",
        "qualification_id": "bewind-ocr-lab-v1",
        "target_allocation_id": "11111111-1111-4111-8111-111111111111",
        "host_binding_key": "lab-a",
        "project_binding_key": "bewind-qualification",
        "project_name": "rf-bewind-qualification",
        "instance_binding_key": "bewind-ocr-guest",
        "instance_name": "rf-bewind-ocr",
        "network_binding_key": "bewind-ocr-net",
        "network_name": "rf-bewind-ocr-net",
        "storage_binding_key": "default",
        "storage_pool_name": "default",
        "binding_created_at": "2026-10-06T18:00:00+00:00",
        "binding_expires_at": "2026-10-06T23:00:00+00:00",
        "incus_executable": "/usr/bin/incus",
        "image_remote": "local",
        "image_fingerprint": "a" * 64,
        "cpu_count": 8,
        "memory_mib": 16384,
        "root_disk_gib": 64,
    }


def _runtime(tmp_path: Path) -> tuple[Path, dict[str, str], str]:
    config_dir = tmp_path / "config"
    config_dir.mkdir(mode=0o700)
    config_dir.chmod(0o700)
    token = "s" * 48
    env_file = config_dir / "runner-mcp.env"
    env_file.write_text(
        "RUNNER_MCP_BEARER_TOKEN=" + token + "\n",
        encoding="utf-8",
    )
    env_file.chmod(0o600)
    target = config_dir / "existing-target.json"
    target.write_text(json.dumps(_target()) + "\n", encoding="utf-8")
    target.chmod(0o600)
    values = {
        "RUNNER_MCP_BEARER_TOKEN": token,
        "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(target),
    }
    return config_dir, values, token


def test_policy_configuration_fails_closed_on_wrong_host(tmp_path: Path) -> None:
    config_dir, values, _token = _runtime(tmp_path)
    before = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    manager = BewindWorkerQualificationPolicyConfigurator(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "github-runner",
        now=lambda: datetime(2026, 10, 7, 8, 0, tzinfo=UTC),
    )

    with pytest.raises(
        BewindWorkerQualificationPolicyError,
        match="host_mismatch",
    ):
        manager.configure()

    assert (config_dir / "runner-mcp.env").read_text(encoding="utf-8") == before


def test_policy_configuration_requires_existing_private_target(tmp_path: Path) -> None:
    config_dir, values, _token = _runtime(tmp_path)
    values.pop("RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG")
    manager = BewindWorkerQualificationPolicyConfigurator(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 8, 0, tzinfo=UTC),
    )

    with pytest.raises(
        BewindWorkerQualificationPolicyError,
        match="source_target_unavailable",
    ):
        manager.configure()


def test_policy_configuration_writes_complete_fixed_private_policy(
    tmp_path: Path,
) -> None:
    config_dir, values, token = _runtime(tmp_path)
    manager = BewindWorkerQualificationPolicyConfigurator(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 8, 0, tzinfo=UTC),
    )

    result = manager.configure()

    assert result == {
        "schemaVersion": "runner-mcp/bewind-worker-qualification-policy/v1",
        "state": "configured",
        "workerId": "aifordable-lab",
        "capabilityProfile": "bewind-ocr-qualification-v1",
        "generation": 1,
        "policyValid": True,
        "sourceTargetReady": True,
        "agentRestartRequired": True,
        "normalActivationEnabled": False,
    }
    assert token not in json.dumps(result)

    expected = {
        "RUNNER_FABRIC_WORKER_QUALIFICATION_WORKER_ID": "aifordable-lab",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_GENERATION": "1",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_NETWORK_PROFILE": "deny-private",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_CPU_UNITS": "8",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_MEMORY_MIB": "16384",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_DISK_MIB": "65536",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_CPU_UNITS": "2",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_MEMORY_MIB": "2048",
        "RUNNER_FABRIC_WORKER_QUALIFICATION_POLICY_EXPIRES_AT": (
            "2026-10-07T10:00:00+00:00"
        ),
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": "http://127.0.0.1:8000/mcp",
        "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": token,
    }
    for key, value in expected.items():
        assert values[key] == value

    template = json.loads(values["RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON"])
    assert template["worker_id"] == "aifordable-lab"
    assert template["generation"] == 1
    assert template["capability_profile"] == "bewind-ocr-qualification-v1"
    assert template["disposable_target"]["image_fingerprint"] == "a" * 64
    assert template["disposable_target"]["binding_created_at"] == (
        "2026-10-07T08:00:00+00:00"
    )
    assert template["disposable_target"]["binding_expires_at"] == (
        "2026-10-07T10:00:00+00:00"
    )

    env_text = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    for key in expected:
        assert f"{key}=" in env_text
    assert "RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON=" in env_text
