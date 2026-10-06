from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp.fabric_worker_qualification_provisioning import (
    FabricWorkerQualificationProvisioner,
    FabricWorkerQualificationProvisioningError,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def managed_home(tmp_path: Path, revision: str) -> Path:
    home = tmp_path / "home"
    slot = (
        home
        / ".local/state/runner-fabric/control-plane-update/slots"
        / revision
    )
    cli = slot / "venv/bin/runner-fabric"
    cli.parent.mkdir(parents=True)
    cli.write_text("#!/bin/sh\n", encoding="utf-8")
    cli.chmod(0o700)
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(cli)
    return home


def disposable_target() -> dict:
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
        "cpu_count": 4,
        "memory_mib": 8192,
        "root_disk_gib": 20,
    }


def private_template(generation: int = 7) -> str:
    return json.dumps(
        {
            "schemaVersion": "runner-mcp/worker-qualification-private/v1",
            "worker_id": "worker-lab-a",
            "capability_profile": "bewind-ocr-qualification-v1",
            "generation": generation,
            "disposable_target": disposable_target(),
        },
        sort_keys=True,
    )


def fingerprint(
    *,
    worker_id: str,
    capability_profile: str,
    generation: int,
    plan_digest: str,
    expires: datetime,
    revision: str,
) -> str:
    payload = {
        "capability_profile": capability_profile,
        "fabric_revision": revision,
        "generation": generation,
        "plan_digest": plan_digest,
        "policy_expires_at": expires.astimezone(UTC).isoformat(),
        "worker_id": worker_id,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def setup_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir(mode=0o700)
    config_dir.chmod(0o700)
    env_file = config_dir / "runner-mcp.env"
    env_file.write_text("RUNNER_MCP_RETENTION_CONFIRMED=true\n", encoding="utf-8")
    env_file.chmod(0o600)
    return config_dir


def provisioner(
    tmp_path: Path,
    *,
    revision: str,
    generation: int = 7,
):
    config_dir = setup_config(tmp_path)
    environment = {
        "RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON": private_template(
            generation
        )
    }
    return (
        FabricWorkerQualificationProvisioner(
            safety=safety(tmp_path),
            environment=environment,
            config_dir=config_dir,
            home=managed_home(tmp_path, revision),
        ),
        environment,
        config_dir,
    )


def test_provision_writes_fixed_private_state_and_runtime_binding(tmp_path: Path) -> None:
    revision = "a" * 40
    expires = datetime.now(UTC) + timedelta(hours=2)
    plan_digest = "b" * 64
    expected_fingerprint = fingerprint(
        worker_id="worker-lab-a",
        capability_profile="bewind-ocr-qualification-v1",
        generation=7,
        plan_digest=plan_digest,
        expires=expires,
        revision=revision,
    )
    manager, environment, config_dir = provisioner(
        tmp_path,
        revision=revision,
    )

    result = manager.provision(
        worker_id="worker-lab-a",
        capability_profile="bewind-ocr-qualification-v1",
        generation=7,
        plan_digest=plan_digest,
        policy_expires_at=expires.isoformat(),
        fabric_revision=revision,
        request_fingerprint=expected_fingerprint,
    )

    assert result == {
        "schemaVersion": (
            "runner.fabric/worker-qualification-provisioning-result/v1"
        ),
        "workerId": "worker-lab-a",
        "capabilityProfile": "bewind-ocr-qualification-v1",
        "state": "ready",
        "reasonCode": "qualification-state-ready",
        "observedGeneration": 7,
        "observedFabricRevision": revision,
        "requestFingerprint": expected_fingerprint,
        "managedLauncherReady": True,
        "qualificationStateReady": True,
        "normalActivationEnabled": False,
    }

    config = config_dir / "worker-qualification/disposable-target.json"
    assert config.stat().st_mode & 0o777 == 0o600
    payload = json.loads(config.read_text(encoding="utf-8"))
    assert set(payload) == set(disposable_target())
    assert payload["binding_expires_at"] == expires.astimezone(UTC).isoformat()
    assert environment[
        "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
    ] == str(config)
    env_text = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    assert str(config) in env_text


def test_provision_is_idempotent_for_same_request(tmp_path: Path) -> None:
    revision = "a" * 40
    expires = datetime.now(UTC) + timedelta(hours=2)
    plan_digest = "b" * 64
    expected_fingerprint = fingerprint(
        worker_id="worker-lab-a",
        capability_profile="bewind-ocr-qualification-v1",
        generation=7,
        plan_digest=plan_digest,
        expires=expires,
        revision=revision,
    )
    manager, _environment, _config_dir = provisioner(
        tmp_path,
        revision=revision,
    )
    args = dict(
        worker_id="worker-lab-a",
        capability_profile="bewind-ocr-qualification-v1",
        generation=7,
        plan_digest=plan_digest,
        policy_expires_at=expires.isoformat(),
        fabric_revision=revision,
        request_fingerprint=expected_fingerprint,
    )

    assert manager.provision(**args) == manager.provision(**args)


def test_wrong_generation_fails_before_private_state_write(tmp_path: Path) -> None:
    revision = "a" * 40
    expires = datetime.now(UTC) + timedelta(hours=2)
    manager, _environment, config_dir = provisioner(
        tmp_path,
        revision=revision,
        generation=8,
    )

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="generation does not match",
    ):
        manager.provision(
            worker_id="worker-lab-a",
            capability_profile="bewind-ocr-qualification-v1",
            generation=7,
            plan_digest="b" * 64,
            policy_expires_at=expires.isoformat(),
            fabric_revision=revision,
            request_fingerprint=fingerprint(
                worker_id="worker-lab-a",
                capability_profile="bewind-ocr-qualification-v1",
                generation=7,
                plan_digest="b" * 64,
                expires=expires,
                revision=revision,
            ),
        )

    assert not (config_dir / "worker-qualification").exists()


def test_wrong_fabric_revision_fails_closed(tmp_path: Path) -> None:
    active_revision = "a" * 40
    requested_revision = "c" * 40
    expires = datetime.now(UTC) + timedelta(hours=2)
    manager, _environment, _config_dir = provisioner(
        tmp_path,
        revision=active_revision,
    )

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="revision",
    ):
        manager.provision(
            worker_id="worker-lab-a",
            capability_profile="bewind-ocr-qualification-v1",
            generation=7,
            plan_digest="b" * 64,
            policy_expires_at=expires.isoformat(),
            fabric_revision=requested_revision,
            request_fingerprint=fingerprint(
                worker_id="worker-lab-a",
                capability_profile="bewind-ocr-qualification-v1",
                generation=7,
                plan_digest="b" * 64,
                expires=expires,
                revision=requested_revision,
            ),
        )


def test_invalid_request_fingerprint_fails_closed(tmp_path: Path) -> None:
    revision = "a" * 40
    expires = datetime.now(UTC) + timedelta(hours=2)
    manager, _environment, _config_dir = provisioner(
        tmp_path,
        revision=revision,
    )

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="fingerprint is invalid",
    ):
        manager.provision(
            worker_id="worker-lab-a",
            capability_profile="bewind-ocr-qualification-v1",
            generation=7,
            plan_digest="b" * 64,
            policy_expires_at=expires.isoformat(),
            fabric_revision=revision,
            request_fingerprint="f" * 64,
        )


def test_expired_request_fails_closed(tmp_path: Path) -> None:
    revision = "a" * 40
    expires = datetime.now(UTC) - timedelta(seconds=1)
    manager, _environment, _config_dir = provisioner(
        tmp_path,
        revision=revision,
    )

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="expired",
    ):
        manager.provision(
            worker_id="worker-lab-a",
            capability_profile="bewind-ocr-qualification-v1",
            generation=7,
            plan_digest="b" * 64,
            policy_expires_at=expires.isoformat(),
            fabric_revision=revision,
            request_fingerprint=fingerprint(
                worker_id="worker-lab-a",
                capability_profile="bewind-ocr-qualification-v1",
                generation=7,
                plan_digest="b" * 64,
                expires=expires,
                revision=revision,
            ),
        )
