from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.bewind_disposable_bootstrap import (
    BewindDisposableBootstrapError,
    BewindDisposableBootstrapRestorer,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def _safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def _runtime(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    config_dir = tmp_path / "config"
    config_dir.mkdir(mode=0o700)
    config_dir.chmod(0o700)
    env_file = config_dir / "runner-mcp.env"
    env_file.write_text("RUNNER_MCP_BEARER_TOKEN=" + "s" * 48 + "\n", encoding="utf-8")
    env_file.chmod(0o600)
    return config_dir, {"RUNNER_MCP_BEARER_TOKEN": "s" * 48}


def test_restore_is_host_bound(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "github-runner",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(BewindDisposableBootstrapError, match="host_mismatch"):
        restorer.restore()

    assert "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG" not in values


def test_restore_writes_fixed_private_bootstrap(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
    )

    result = restorer.restore()

    assert result["state"] == "restored"
    assert result["workerId"] == "aifordable-lab"
    assert result["capabilityProfile"] == "bewind-ocr-qualification-v1"
    assert result["generation"] == 1
    assert result["normalActivationEnabled"] is False

    raw = values["RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"]
    config_path = Path(raw)
    assert config_path == config_dir / "worker-qualification" / "disposable-target.json"
    assert config_path.stat().st_mode & 0o777 == 0o600

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload == {
        "mode": "af14-disposable-v1",
        "qualification_id": "bewind-ocr-lab-v1",
        "target_allocation_id": result["targetAllocationId"],
        "host_binding_key": "aifordable-lab",
        "project_binding_key": "bewind-qualification",
        "project_name": "rf-bewind-qualification",
        "instance_binding_key": "bewind-ocr-guest",
        "instance_name": "rf-bewind-ocr",
        "network_binding_key": "bewind-ocr-net",
        "network_name": "rf-bewind-ocr-net",
        "storage_binding_key": "default",
        "storage_pool_name": "default",
        "binding_created_at": "2026-10-07T15:00:00+00:00",
        "binding_expires_at": "2026-10-07T17:00:00+00:00",
        "incus_executable": "/usr/bin/incus",
        "image_remote": "local",
        "image_fingerprint": "879602ca696d63166965188337597d254083955bd154847284b030a4affd5fc9",
        "cpu_count": 4,
        "memory_mib": 8192,
        "root_disk_gib": 20,
    }

    env_text = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    assert "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG=" in env_text
    assert str(config_path) in env_text


def test_restore_is_deterministic_except_timestamps(tmp_path: Path) -> None:
    first_dir, first_values = _runtime(tmp_path / "one")
    second_dir, second_values = _runtime(tmp_path / "two")
    clock = lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC)

    first = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path / "s1"),
        environment=first_values,
        config_dir=first_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=clock,
    ).restore()
    second = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path / "s2"),
        environment=second_values,
        config_dir=second_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=clock,
    ).restore()

    assert first["targetAllocationId"] == second["targetAllocationId"]
