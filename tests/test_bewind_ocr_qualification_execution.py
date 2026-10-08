from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from runner_mcp.bewind_ocr_qualification_execution import (
    BewindOcrQualificationRunner,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


class FakeStager:
    def __init__(self, path: Path, digest: str) -> None:
        self.path = path
        self.digest = digest
        self.cleaned = False

    def require_staged(self):
        return SimpleNamespace(
            staged_path=self.path,
            source_sha256=self.digest,
            size_bytes=self.path.stat().st_size,
        )

    def cleanup(self):
        self.cleaned = True
        return {"state": "clean"}


class FakeQualifier:
    def run(self):
        return {
            "qualificationPassed": True,
            "finalState": "destroyed",
            "normalActivationEnabled": False,
        }


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def target_config(tmp_path: Path) -> tuple[Path, dict]:
    payload = {
        "project_name": "rf-bewind-qualification",
        "instance_name": "rf-bewind-ocr",
        "network_name": "rf-bewind-net",
        "storage_pool_name": "default",
        "image_remote": "local",
        "image_fingerprint": "a" * 64,
        "cpu_count": 4,
        "memory_mib": 8192,
        "root_disk_gib": 20,
        "binding_expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "incus_executable": "/usr/bin/incus",
    }
    path = tmp_path / "target.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path, payload


def execution_config() -> str:
    return json.dumps(
        {
            "schemaVersion": "runner-mcp/bewind-ocr-qualification-execution/v1",
            "worker_id": "aifordable-lab",
            "capability_profile": "bewind-ocr-qualification-v1",
            "generation": 1,
            "fabric_revision": "b" * 40,
            "bewind_revision": "c" * 40,
        }
    )


def test_fixed_contract_constants_are_project_canonical() -> None:
    import runner_mcp.bewind_ocr_qualification_execution as module

    assert module._WORKER_ID == "aifordable-lab"
    assert module._CAPABILITY == "bewind-ocr-qualification-v1"
    assert module._GENERATION == 1
    assert module._LANGUAGES == "nld+fra+deu"
    assert module._PIPELINE == "pre1997-ocrmypdf-sidecar-0.2.0"
    assert module._SOURCE_ID == "2026/02/03_1.pdf"
    assert "Friedensgericht" in module._REQUIRED_TERMS


def test_output_validation_hashes_pages_and_requires_german_terms(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    environment = {
        "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": execution_config(),
        "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(target_path),
    }
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment=environment,
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
    )
    sidecar = tmp_path / "sidecar.txt"
    sidecar.write_text(
        "Friedensgericht\n"
        "Bestellung eines Betreuers\n"
        "Schutzregelung der Vertretung\f"
        "second page\f",
        encoding="utf-8",
    )

    page_hashes, output_hash = runner._validate_output(
        sidecar,
        expected_pages=2,
        expected_source_sha=digest,
    )

    assert len(page_hashes) == 2
    assert len(output_hash) == 64


def test_execution_authority_rejects_wrong_worker(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    cfg = json.loads(execution_config())
    cfg["worker_id"] = "other"
    environment = {
        "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": json.dumps(cfg),
        "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(target_path),
    }
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment=environment,
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
    )

    try:
        runner._execution_config()
    except Exception as exc:
        assert "authority_invalid" in str(exc)
    else:
        raise AssertionError("wrong worker authority accepted")


def test_readiness_requires_exact_generation(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": execution_config(),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(target_path),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 2,
        },
    )

    try:
        runner._require_worker_readiness()
    except Exception as exc:
        assert "readiness_blocked" in str(exc)
    else:
        raise AssertionError("wrong generation accepted")
