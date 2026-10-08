from __future__ import annotations

import json
from pathlib import Path

from runner_mcp.bewind_ocr_qualification_authority import (
    BewindOcrQualificationExecutionAuthorityConfigurator,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def test_configure_persists_fixed_private_authority_and_updates_runtime(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env_file = config / "runner-mcp.env"
    env_file.write_text("EXISTING=value\n", encoding="utf-8")
    env_file.chmod(0o600)
    runtime = {"EXISTING": "value"}

    manager = BewindOcrQualificationExecutionAuthorityConfigurator(
        safety=safety(tmp_path),
        environment=runtime,
        config_dir=config,
    )

    first = manager.configure()
    second = manager.configure()

    assert first == second
    assert first["state"] == "configured"
    assert first["workerId"] == "aifordable-lab"
    assert first["capabilityProfile"] == "bewind-ocr-qualification-v1"
    assert first["generation"] == 1
    assert first["fabricRevision"] == (
        "ae345197a9bef3765408a21deaeb54fc8c03c4de"
    )
    assert first["bewindRevision"] == (
        "cf16b9e7481bdb56b8c308ff29c6f305cd1a0a48"
    )
    assert first["normalActivationEnabled"] is False

    raw = runtime["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON"]
    payload = json.loads(raw)
    assert payload == {
        "schemaVersion": "runner-mcp/bewind-ocr-qualification-execution/v1",
        "worker_id": "aifordable-lab",
        "capability_profile": "bewind-ocr-qualification-v1",
        "generation": 1,
        "fabric_revision": "ae345197a9bef3765408a21deaeb54fc8c03c4de",
        "bewind_revision": "cf16b9e7481bdb56b8c308ff29c6f305cd1a0a48",
    }

    rendered = env_file.read_text(encoding="utf-8")
    assert rendered.count(
        "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON="
    ) == 1
    assert "EXISTING=value" in rendered
    assert env_file.stat().st_mode & 0o777 == 0o600
