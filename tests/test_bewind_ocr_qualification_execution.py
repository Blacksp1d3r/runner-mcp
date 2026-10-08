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
from runner_mcp.bewind_ocr_qualification_staging import (
    BewindOcrQualificationStagingError,
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
        "FRIEDENSGERICHT\n"
        "Bestellung   eines\n Betreuers\n"
        "schutzregelung der vertretung\f"
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



def test_run_exposes_bounded_internal_disposable_reason(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class InvalidQualifier:
        def run(self):
            return {
                "schemaVersion": (
                    "runner-mcp/disposable-target-qualification-status/v1"
                ),
                "state": "invalid",
                "reasonCode": "clean-start",
                "qualificationPassed": False,
                "normalActivationEnabled": False,
            }

    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=InvalidQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _revision: None)
    monkeypatch.setattr(runner, "_require_worker_readiness", lambda: None)

    result = runner.run()

    assert result == {
        "schemaVersion": "runner-mcp/bewind-ocr-qualification-preflight/v1",
        "state": "blocked",
        "reasonCode": "disposable-preflight-failed",
        "disposableReasonCode": "clean-start",
        "normalActivationEnabled": False,
    }


def test_run_returns_bounded_target_preflight_reason(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, _ = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _revision: None)
    monkeypatch.setattr(runner, "_require_worker_readiness", lambda: None)

    def expired_target():
        raise BewindOcrQualificationExecutionError(
            "bewind_ocr_qualification_target_expired"
        )

    monkeypatch.setattr(runner, "_target_config", expired_target)

    result = runner.run()

    assert result == {
        "schemaVersion": "runner-mcp/bewind-ocr-qualification-preflight/v1",
        "state": "blocked",
        "reasonCode": "target-expired",
        "normalActivationEnabled": False,
    }


def test_run_returns_bounded_staging_preflight_reason(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FailingStager:
        def require_staged(self):
            raise BewindOcrQualificationStagingError(
                "qualification staging state is unavailable"
            )

    target_path, _ = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FailingStager(),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _revision: None)
    monkeypatch.setattr(runner, "_require_worker_readiness", lambda: None)

    result = runner.run()

    assert result == {
        "schemaVersion": "runner-mcp/bewind-ocr-qualification-preflight/v1",
        "state": "blocked",
        "reasonCode": "staging-state-unavailable",
        "normalActivationEnabled": False,
    }


def test_guest_source_is_verified_after_push(tmp_path: Path) -> None:
    data = b"%PDF exact source"
    source = tmp_path / "source.pdf"
    source.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    target_path, target = target_config(tmp_path)
    calls: list[tuple[str, ...]] = []

    def fake_run(command, **_kwargs):
        calls.append(tuple(command))
        if "sha256sum" in command:
            stdout = f"{digest}  /tmp/bewind-qualification.pdf\n"
        elif "stat" in command and "%s" in command:
            stdout = f"{len(data)}\n"
        else:
            stdout = ""
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=stdout,
            stderr="",
        )

    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        command_runner=fake_run,
    )

    runner._push_source(
        target,
        source,
        expected_sha=digest,
        expected_size=len(data),
    )

    assert any("sha256sum" in command for command in calls)
    assert any("stat" in command and "%s" in command for command in calls)


def test_guest_source_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    data = b"%PDF exact source"
    source = tmp_path / "source.pdf"
    source.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    target_path, target = target_config(tmp_path)

    def fake_run(command, **_kwargs):
        stdout = ""
        if "sha256sum" in command:
            stdout = f"{'0' * 64}  /tmp/bewind-qualification.pdf\n"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=stdout,
            stderr="",
        )

    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        command_runner=fake_run,
    )

    with pytest.raises(RuntimeError, match="source-transfer-verification-failed"):
        runner._push_source(
            target,
            source,
            expected_sha=digest,
            expected_size=len(data),
        )


def test_guest_cpu_measurement_uses_busy_ticks(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    target_path, target = target_config(tmp_path)

    def fake_run(command, **_kwargs):
        if "getconf" in command:
            stdout = "100\n"
        elif "/proc/stat" in command:
            stdout = "cpu 100 10 20 1000 50 5 5 0 0 0\n"
        else:
            stdout = ""
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=stdout,
            stderr="",
        )

    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=FakeStager(source, digest),
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        command_runner=fake_run,
    )

    assert runner._guest_cpu_seconds(target) == pytest.approx(1.4)


def test_success_result_contains_measured_cpu_seconds_per_page(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    stager = FakeStager(source, digest)
    target_path, target = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=stager,
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        loadavg=lambda: (0.1, 0.2, 0.3),
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _revision: None)
    monkeypatch.setattr(runner, "_require_worker_readiness", lambda: None)
    monkeypatch.setattr(runner, "_target_config", lambda: target)
    monkeypatch.setattr(runner, "_require_clean_start", lambda _target: None)
    monkeypatch.setattr(runner, "_create_target", lambda _target: None)
    monkeypatch.setattr(runner, "_require_guest_runtime", lambda _target: None)
    monkeypatch.setattr(
        runner,
        "_push_source",
        lambda _target, _path, **_kwargs: None,
    )
    monkeypatch.setattr(runner, "_page_count", lambda _target: 2)
    cpu_samples = iter((10.0, 14.0))
    monkeypatch.setattr(
        runner,
        "_guest_cpu_seconds",
        lambda _target: next(cpu_samples),
    )
    monkeypatch.setattr(runner, "_execute_ocr", lambda _target: None)
    monkeypatch.setattr(
        runner,
        "_pull_sidecar",
        lambda _target, _path: None,
    )
    monkeypatch.setattr(
        runner,
        "_validate_output",
        lambda _path, **_kwargs: (("d" * 64, "e" * 64), "f" * 64),
    )
    monkeypatch.setattr(runner, "_cleanup_target", lambda _target: True)

    result = runner.run()

    assert result["state"] == "qualified"
    assert result["cpuSecondsPerPage"] == 2.0
    assert stager.cleaned is True


def test_target_cleanup_failure_still_attempts_staging_cleanup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import runner_mcp.bewind_ocr_qualification_execution as module

    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    digest = hashlib.sha256(b"pdf").hexdigest()
    stager = FakeStager(source, digest)
    target_path, target = target_config(tmp_path)
    runner = BewindOcrQualificationRunner(
        safety=safety(tmp_path),
        environment={
            "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON": (
                execution_config()
            ),
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(
                target_path
            ),
        },
        config_dir=tmp_path,
        stager=stager,
        disposable_qualifier=FakeQualifier(),
        readiness_provider=lambda: {
            "activationReady": True,
            "currentGeneration": 1,
        },
        loadavg=lambda: (0.1, 0.2, 0.3),
    )
    monkeypatch.setattr(runner, "_require_fabric_revision", lambda _revision: None)
    monkeypatch.setattr(runner, "_require_worker_readiness", lambda: None)
    monkeypatch.setattr(runner, "_target_config", lambda: target)
    monkeypatch.setattr(runner, "_require_clean_start", lambda _target: None)
    monkeypatch.setattr(runner, "_create_target", lambda _target: None)
    monkeypatch.setattr(runner, "_require_guest_runtime", lambda _target: None)
    monkeypatch.setattr(
        runner,
        "_push_source",
        lambda _target, _path, **_kwargs: None,
    )
    monkeypatch.setattr(runner, "_page_count", lambda _target: 1)
    cpu_samples = iter((1.0, 2.0))
    monkeypatch.setattr(
        runner,
        "_guest_cpu_seconds",
        lambda _target: next(cpu_samples),
    )
    monkeypatch.setattr(runner, "_execute_ocr", lambda _target: None)
    monkeypatch.setattr(
        runner,
        "_pull_sidecar",
        lambda _target, _path: None,
    )
    monkeypatch.setattr(
        runner,
        "_validate_output",
        lambda _path, **_kwargs: (("d" * 64,), "f" * 64),
    )

    def cleanup_failure(_target):
        raise module._QualificationFailure("cleanup-failed")

    monkeypatch.setattr(runner, "_cleanup_target", cleanup_failure)

    result = runner.run()

    assert stager.cleaned is True
    assert result["state"] == "recovery-required"
    assert result["failureCategory"] == "cleanup-failed"
    assert result["cleanupReceipt"] == {
        "targetDestroyed": False,
        "stagedInputRemoved": True,
    }
