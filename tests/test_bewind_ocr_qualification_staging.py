from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.bewind_ocr_qualification_staging import (
    BewindOcrQualificationStager,
    BewindOcrQualificationStagingError,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def config_dir(tmp_path: Path) -> Path:
    value = tmp_path / "config"
    value.mkdir(mode=0o700)
    value.chmod(0o700)
    return value


def private_config(source: Path, data: bytes) -> str:
    return json.dumps(
        {
            "schemaVersion": "runner-mcp/bewind-ocr-qualification-source/v1",
            "worker_id": "aifordable-lab",
            "capability_profile": "bewind-ocr-qualification-v1",
            "source_id": "2026/02/03_1.pdf",
            "source_path": str(source),
            "expected_sha256": hashlib.sha256(data).hexdigest(),
            "expected_size_bytes": len(data),
        },
        sort_keys=True,
    )


def stager(tmp_path: Path, data: bytes = b"%PDF synthetic sentinel") -> tuple[
    BewindOcrQualificationStager,
    Path,
    dict[str, str],
]:
    source = tmp_path / "sentinel.pdf"
    source.write_bytes(data)
    source.chmod(0o600)
    environment = {
        "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON": private_config(
            source,
            data,
        )
    }
    return (
        BewindOcrQualificationStager(
            safety=safety(tmp_path),
            environment=environment,
            config_dir=config_dir(tmp_path),
        ),
        source,
        environment,
    )


def test_stage_is_zero_argument_content_addressed_and_restart_safe(
    tmp_path: Path,
) -> None:
    data = b"%PDF synthetic sentinel"
    manager, _source, environment = stager(tmp_path, data)
    digest = hashlib.sha256(data).hexdigest()

    result = manager.stage()

    assert result == {
        "schemaVersion": "runner-mcp/bewind-ocr-qualification-stage-result/v1",
        "state": "ready",
        "reasonCode": "qualification-source-staged",
        "workerId": "aifordable-lab",
        "capabilityProfile": "bewind-ocr-qualification-v1",
        "sourceId": "2026/02/03_1.pdf",
        "sourceSha256": digest,
        "sizeBytes": len(data),
        "singleUse": True,
        "normalActivationEnabled": False,
    }
    staged = manager.require_staged()
    assert staged.source_sha256 == digest
    assert staged.size_bytes == len(data)
    assert staged.staged_path.name == f"{digest}.pdf"
    assert staged.staged_path.read_bytes() == data
    assert staged.staged_path.stat().st_mode & 0o777 == 0o600

    restarted = BewindOcrQualificationStager(
        safety=safety(tmp_path),
        environment=environment,
        config_dir=manager.config_dir,
    )
    assert restarted.require_staged().source_sha256 == digest


def test_stage_is_idempotent_for_same_exact_source(tmp_path: Path) -> None:
    manager, _source, _environment = stager(tmp_path)

    first = manager.stage()
    second = manager.stage()

    assert first == second


def test_wrong_digest_fails_before_staging(tmp_path: Path) -> None:
    data = b"%PDF synthetic sentinel"
    manager, _source, environment = stager(tmp_path, data)
    payload = json.loads(
        environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"]
    )
    payload["expected_sha256"] = "0" * 64
    environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"] = json.dumps(
        payload
    )

    with pytest.raises(
        BewindOcrQualificationStagingError,
        match="digest does not match",
    ):
        manager.stage()

    assert not (
        manager.config_dir / "bewind-ocr-qualification/stage-receipt.json"
    ).exists()


def test_wrong_size_fails_before_staging(tmp_path: Path) -> None:
    data = b"%PDF synthetic sentinel"
    manager, _source, environment = stager(tmp_path, data)
    payload = json.loads(
        environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"]
    )
    payload["expected_size_bytes"] += 1
    environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"] = json.dumps(
        payload
    )

    with pytest.raises(
        BewindOcrQualificationStagingError,
        match="size does not match",
    ):
        manager.stage()


def test_symlink_source_is_rejected(tmp_path: Path) -> None:
    data = b"%PDF synthetic sentinel"
    real = tmp_path / "real.pdf"
    real.write_bytes(data)
    source = tmp_path / "sentinel.pdf"
    source.symlink_to(real)
    cfg = config_dir(tmp_path)
    environment = {
        "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON": private_config(
            source,
            data,
        )
    }
    manager = BewindOcrQualificationStager(
        safety=safety(tmp_path),
        environment=environment,
        config_dir=cfg,
    )

    with pytest.raises(
        BewindOcrQualificationStagingError,
        match="source is unavailable",
    ):
        manager.stage()


def test_private_authority_is_fixed_to_worker_capability_and_source(
    tmp_path: Path,
) -> None:
    manager, _source, environment = stager(tmp_path)
    payload = json.loads(
        environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"]
    )

    for key, value in (
        ("worker_id", "other-worker"),
        ("capability_profile", "other"),
        ("source_id", "other.pdf"),
    ):
        changed = dict(payload)
        changed[key] = value
        environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"] = json.dumps(
            changed
        )
        with pytest.raises(
            BewindOcrQualificationStagingError,
            match="authority is invalid",
        ):
            manager.stage()

    environment["RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"] = json.dumps(
        payload
    )


def test_cleanup_removes_single_use_input_and_receipt(tmp_path: Path) -> None:
    manager, _source, _environment = stager(tmp_path)
    manager.stage()
    staged_path = manager.require_staged().staged_path

    result = manager.cleanup()

    assert result["state"] == "clean"
    assert result["stagedInputPresent"] is False
    assert result["receiptPresent"] is False
    assert not staged_path.exists()
    assert not (
        manager.config_dir / "bewind-ocr-qualification/stage-receipt.json"
    ).exists()
    with pytest.raises(BewindOcrQualificationStagingError):
        manager.require_staged()


def test_tampered_staged_input_fails_closed(tmp_path: Path) -> None:
    manager, _source, _environment = stager(tmp_path)
    manager.stage()
    staged = manager.require_staged()
    staged.staged_path.write_bytes(b"tampered")
    staged.staged_path.chmod(0o600)

    with pytest.raises(
        BewindOcrQualificationStagingError,
        match="size does not match",
    ):
        manager.require_staged()



def test_stage_accepts_private_file_backed_source_binding(tmp_path: Path) -> None:
    data = b"%PDF synthetic sentinel"
    source = tmp_path / "sentinel.pdf"
    source.write_bytes(data)
    source.chmod(0o600)
    cfg = config_dir(tmp_path)
    root = cfg / "bewind-ocr-qualification"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    binding = root / "source-binding.json"
    binding.write_text(private_config(source, data), encoding="utf-8")
    binding.chmod(0o600)

    manager = BewindOcrQualificationStager(
        safety=safety(tmp_path),
        environment={},
        config_dir=cfg,
    )

    result = manager.stage()

    assert result["state"] == "ready"
    assert result["sourceSha256"] == hashlib.sha256(data).hexdigest()


def test_file_backed_binding_must_remain_private(tmp_path: Path) -> None:
    data = b"%PDF synthetic sentinel"
    source = tmp_path / "sentinel.pdf"
    source.write_bytes(data)
    cfg = config_dir(tmp_path)
    root = cfg / "bewind-ocr-qualification"
    root.mkdir(mode=0o700)
    binding = root / "source-binding.json"
    binding.write_text(private_config(source, data), encoding="utf-8")
    binding.chmod(0o644)

    manager = BewindOcrQualificationStager(
        safety=safety(tmp_path),
        environment={},
        config_dir=cfg,
    )

    with pytest.raises(
        BewindOcrQualificationStagingError,
        match="state is unsafe",
    ):
        manager.stage()
