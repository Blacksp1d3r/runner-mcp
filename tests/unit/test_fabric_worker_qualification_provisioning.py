import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp.fabric_worker_qualification_provisioning import (
    FabricWorkerQualificationProvisioner,
    FabricWorkerQualificationProvisioningError,
    provisioning_config_environment_key,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def managed_home(tmp_path: Path, revision: str = "a" * 40) -> Path:
    home = tmp_path / "home"
    slot = (
        home
        / ".local/state/runner-fabric/control-plane-update/slots"
        / revision
    )
    slot.mkdir(parents=True)
    binary = slot / "runner-fabric"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o700)
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(binary)
    return home


def binding(tmp_path: Path, *, generation: int = 3) -> Path:
    path = tmp_path / "qualification-binding.json"
    path.write_text(
        json.dumps(
            {
                "schemaVersion": (
                    "runner.mcp/worker-qualification-provisioning-config/v1"
                ),
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": generation,
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


def request(revision: str = "a" * 40, generation: int = 3) -> dict:
    return {
        "worker_id": "aifordable-lab",
        "capability_profile": "bewind-ocr-qualification-v1",
        "generation": generation,
        "plan_digest": "b" * 64,
        "policy_expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "fabric_revision": revision,
        "request_fingerprint": "c" * 64,
    }


def test_fixed_provisioning_writes_owner_only_state(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )

    result = provisioner.provision(**request())

    assert result == {
        "schemaVersion": (
            "runner.fabric/worker-qualification-provisioning-result/v1"
        ),
        "workerId": "aifordable-lab",
        "capabilityProfile": "bewind-ocr-qualification-v1",
        "state": "ready",
        "reasonCode": "qualification-state-ready",
        "observedGeneration": 3,
        "observedFabricRevision": "a" * 40,
        "requestFingerprint": "c" * 64,
        "managedLauncherReady": True,
        "qualificationStateReady": True,
        "normalActivationEnabled": False,
    }
    state = (
        home
        / ".local/state/runner-mcp/worker-qualification/aifordable-lab.json"
    )
    assert state.stat().st_mode & 0o777 == 0o600
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["normalActivationEnabled"] is False
    assert "path" not in payload
    assert "endpoint" not in payload


def test_identical_request_is_idempotent(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )
    args = request()

    first = provisioner.provision(**args)
    second = provisioner.provision(**args)

    assert first == second


def test_existing_mismatched_state_fails_closed(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )
    provisioner.provision(**request())

    changed = request()
    changed["request_fingerprint"] = "d" * 64
    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="state_mismatch",
    ):
        provisioner.provision(**changed)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("worker_id", "../host", "worker_identity_invalid"),
        ("capability_profile", "shell-v1", "capability_unavailable"),
        ("generation", 0, "generation_invalid"),
        ("plan_digest", "bad", "plan_digest_invalid"),
        ("fabric_revision", "bad", "revision_invalid"),
        ("request_fingerprint", "bad", "request_fingerprint_invalid"),
    ],
)
def test_invalid_public_contract_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
    match: str,
) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )
    args = request()
    args[field] = value

    with pytest.raises(FabricWorkerQualificationProvisioningError, match=match):
        provisioner.provision(**args)


def test_expired_request_fails_before_state_write(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )
    args = request()
    args["policy_expires_at"] = (
        datetime.now(UTC) - timedelta(seconds=1)
    ).isoformat()

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="policy_expired",
    ):
        provisioner.provision(**args)

    assert not (
        home
        / ".local/state/runner-mcp/worker-qualification/aifordable-lab.json"
    ).exists()


def test_revision_and_generation_are_fenced(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path, generation=3)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )

    bad_revision = request(revision="d" * 40)
    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="revision_mismatch",
    ):
        provisioner.provision(**bad_revision)

    bad_generation = request(generation=4)
    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="binding_mismatch",
    ):
        provisioner.provision(**bad_generation)


def test_private_binding_must_be_owner_only(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = binding(tmp_path)
    config.chmod(0o644)
    provisioner = FabricWorkerQualificationProvisioner(
        safety=safety(tmp_path),
        environment={provisioning_config_environment_key(): str(config)},
        home=home,
    )

    with pytest.raises(
        FabricWorkerQualificationProvisioningError,
        match="config_unmanaged",
    ):
        provisioner.provision(**request())
