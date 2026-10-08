from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner_mcp.bewind_ocr_qualification_execution import (
    BewindOcrQualificationExecutionError,
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

    with pytest.raises(
        BewindOcrQualificationExecutionError,
        match="authority_invalid",
    ):
        runner._execution_config()


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

    with pytest.raises(
        BewindOcrQualificationExecutionError,
        match="readiness_blocked",
    ):
        runner._require_worker_readiness()



def test_output_validation_uses_whitespace_collapse_and_casefold(tmp_path: Path) -> None:
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
            "currentGeneration": 1,
        },
    )
    sidecar = tmp_path / "normalized-sidecar.txt"
    sidecar.write_text(
        "friedensGERICHT\n"
        "Bestellung   eines\nBetreuers\n"
        "SCHUTZREGELUNG DER   VERTRETUNG\f",
        encoding="utf-8",
    )

    page_hashes, output_hash = runner._validate_output(
        sidecar,
        expected_pages=1,
        expected_source_sha=digest,
    )

    assert len(page_hashes) == 1
    assert len(output_hash) == 64


def test_push_source_verifies_guest_sha_and_size(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    data = b"pdf"
    source.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    target_path, payload = target_config(tmp_path)
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, f"{digest}  /tmp/bewind-qualification.pdf\n", ""),
            subprocess.CompletedProcess([], 0, f"{len(data)}\n", ""),
        ]
    )
    calls = []

    def command_runner(*args, **kwargs):
        calls.append(args[0])
        return next(responses)

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
            "currentGeneration": 1,
        },
        command_runner=command_runner,
    )

    runner._push_source(
        payload,
        source,
        expected_sha=digest,
        expected_size=len(data),
    )

    assert any("sha256sum" in call for call in calls)
    assert any("stat" in call for call in calls)


def test_execute_ocr_returns_guest_cpu_seconds(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, payload = target_config(tmp_path)
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "120.50 9.50\n", ""),
        ]
    )

    def command_runner(*args, **kwargs):
        return next(responses)

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
            "currentGeneration": 1,
        },
        command_runner=command_runner,
    )

    assert runner._execute_ocr(payload) == 130.0


def test_target_cleanup_failure_still_attempts_single_use_staging_cleanup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    stager = FakeStager(source, digest)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": execution_config(),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(target_path),
        },
        config_dir=tmp_path,
        stager=stager,
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        monotonic=iter([10.0, 11.0]).__next__,
        loadavg=lambda: (0.1, 0.2, 0.3),
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _expected: None)
    monkeypatch.setattr(runner, "_require_clean_start", lambda _target: None)
    monkeypatch.setattr(runner, "_create_target", lambda _target: None)
    monkeypatch.setattr(runner, "_require_guest_runtime", lambda _target: None)
    monkeypatch.setattr(runner, "_push_source", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner, "_page_count", lambda _target: 1)
    monkeypatch.setattr(runner, "_execute_ocr", lambda _target: 1.0)

    sidecar = tmp_path / "bewind-ocr-qualification" / "result-sidecar.txt"

    def pull_sidecar(_target, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "Friedensgericht Bestellung eines Betreuers "
            "Schutzregelung der Vertretung",
            encoding="utf-8",
        )

    monkeypatch.setattr(runner, "_pull_sidecar", pull_sidecar)
    monkeypatch.setattr(
        runner,
        "_cleanup_target",
        lambda _target: (_ for _ in ()).throw(RuntimeError("inspection failed")),
    )

    result = runner.run()

    assert stager.cleaned is True
    assert result["state"] == "recovery-required"
    assert result["failureCategory"] == "cleanup-failed"
    assert result["cleanupReceipt"]["targetDestroyed"] is False
    assert result["cleanupReceipt"]["stagedInputRemoved"] is True
    assert not sidecar.exists()
