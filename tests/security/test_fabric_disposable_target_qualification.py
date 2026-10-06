from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.fabric_disposable_target_qualification import (
    FabricDisposableTargetQualificationError,
    qualify_fabric_disposable_target,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy

CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"


def managed_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    slots = (
        home
        / ".local"
        / "state"
        / "runner-fabric"
        / "control-plane-update"
        / "slots"
        / "slot-a"
    )
    slots.mkdir(parents=True)
    launcher = slots / "runner-fabric"
    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    launcher.chmod(0o700)
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "runner-fabric").symlink_to(launcher)
    return home


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def payload() -> dict[str, object]:
    return {
        "schemaVersion": "runner.fabric/disposable-target-qualification/v1",
        "qualificationId": "af14-lab-one",
        "targetAllocationId": "11111111-1111-4111-8111-111111111111",
        "runtimeProfile": "disposable-incus-vm-podman-v1",
        "createdReady": True,
        "resourceLimitsVerified": True,
        "guestRuntimeVerified": True,
        "managementAuthorityBlocked": True,
        "noDefaultRoute": True,
        "networkPolicyVerified": True,
        "destroyVerified": True,
        "recreateVerified": True,
        "recreateIsolationVerified": True,
        "finalDestroyVerified": True,
        "imageFingerprint": "a" * 64,
        "bootstrapSha256": "b" * 64,
        "qualificationPassed": True,
        "normalActivationEnabled": False,
        "finalState": "destroyed",
    }


def test_qualification_uses_only_managed_launcher_and_fixed_command(
    tmp_path: Path,
) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "private.json"
    config.write_text("{}", encoding="utf-8")
    config.chmod(0o600)
    calls: list[dict[str, object]] = []

    def fake_runner(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(payload()),
            stderr="",
        )

    result = qualify_fabric_disposable_target(
        safety=safety(tmp_path),
        private_values={CONFIG_ENV: str(config.resolve())},
        home=home,
        runner=fake_runner,
    )

    assert result == payload()
    assert len(calls) == 1
    call = calls[0]
    command = call["command"]
    assert isinstance(command, tuple)
    assert command[1:] == ("disposable-target-qualify",)
    assert str(home / ".local" / "bin" / "runner-fabric") == command[0]
    assert call["cwd"] == "/"
    assert call["shell"] is False
    assert call["timeout"] == 900
    assert call["env"] == {
        "HOME": str(home.resolve()),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        CONFIG_ENV: str(config.resolve()),
    }


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: {**p, "normalActivationEnabled": True},
        lambda p: {**p, "qualificationPassed": False},
        lambda p: {**p, "finalState": "ready"},
        lambda p: {**p, "privatePath": "/secret"},
        lambda p: {**p, "imageFingerprint": "not-a-digest"},
    ],
)
def test_invalid_or_private_payload_fails_closed(
    tmp_path: Path,
    mutator,
) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "private.json"
    config.write_text("{}", encoding="utf-8")
    config.chmod(0o600)

    def fake_runner(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(mutator(payload())),
            stderr="host=private.example path=/secret",
        )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="qualification_invalid",
    ):
        qualify_fabric_disposable_target(
            safety=safety(tmp_path),
            private_values={CONFIG_ENV: str(config.resolve())},
            home=home,
            runner=fake_runner,
        )


def test_nonzero_process_failure_is_sanitized(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "private.json"
    config.write_text("{}", encoding="utf-8")
    config.chmod(0o600)

    def fake_runner(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=2,
            stdout="",
            stderr="host=private.example path=/secret token=hidden",
        )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="qualification_failed",
    ) as exc:
        qualify_fabric_disposable_target(
            safety=safety(tmp_path),
            private_values={CONFIG_ENV: str(config.resolve())},
            home=home,
            runner=fake_runner,
        )

    rendered = str(exc.value)
    assert "private.example" not in rendered
    assert "/secret" not in rendered
    assert "hidden" not in rendered


def test_operator_stop_blocks_before_process_execution(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "private.json"
    config.write_text("{}", encoding="utf-8")
    config.chmod(0o600)
    guard = safety(tmp_path)
    assert guard.stop_file is not None
    guard.stop_file.write_text("stop\n", encoding="utf-8")
    calls = 0

    def fake_runner(command, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("must not execute")

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="qualification_blocked",
    ):
        qualify_fabric_disposable_target(
            safety=guard,
            private_values={CONFIG_ENV: str(config.resolve())},
            home=home,
            runner=fake_runner,
        )
    assert calls == 0
