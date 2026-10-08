import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.fabric_disposable_target import (
    FabricDisposableTargetQualificationError,
    FabricDisposableTargetQualificationRunner,
    qualification_config_environment_key,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)


def payload() -> dict:
    return {
        "schemaVersion": "runner.fabric/disposable-target-qualification/v1",
        "qualificationId": "af14-lab-v1",
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


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def managed_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    slots = home / ".local/state/runner-fabric/control-plane-update/slots"
    slot = slots / ("a" * 40)
    slot.mkdir(parents=True)
    target = slot / "runner-fabric"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o700)
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(target)
    return home


def test_qualification_invokes_only_fixed_managed_command(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload()),
            stderr="",
        )

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=fake_run,
    )

    result = runner.run()

    assert result["qualificationPassed"] is True
    assert result["normalActivationEnabled"] is False
    assert result["finalState"] == "destroyed"
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == [
        str(home / ".local/bin/runner-fabric"),
        "disposable-target-qualify",
    ]
    assert kwargs["shell"] is False
    assert kwargs["cwd"] == "/"
    assert set(kwargs["env"]) == {
        "HOME",
        "PATH",
        "LANG",
        "LC_ALL",
        qualification_config_environment_key(),
    }
    assert "token" not in repr(calls).casefold()
    assert "secret" not in repr(calls).casefold()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda item: item.update({"privatePath": "/srv/private"}),
        lambda item: item.update({"normalActivationEnabled": True}),
        lambda item: item.update({"createdReady": False}),
        lambda item: item.update({"finalState": "ready"}),
        lambda item: item.update({"imageFingerprint": "not-a-digest"}),
    ],
)
def test_private_or_unqualified_output_fails_closed(
    tmp_path: Path,
    mutator,
) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")
    result = payload()
    mutator(result)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(result),
            stderr="private diagnostic must not escape",
        )

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="output_invalid",
    ):
        runner.run()


@pytest.mark.parametrize(
    "reason",
    [
        "guest-agent-not-ready",
        "destroy-instance-delete-nonzero",
        "final-destroy-network-persisted",
        "isolation-management-authority",
        "isolation-default-route",
        "isolation-network-policy",
        "recreate-isolation-management-authority",
        "recreate-isolation-default-route",
        "recreate-isolation-network-policy",
    ],
)
def test_known_nonzero_result_returns_only_bounded_reason(
    tmp_path: Path,
    reason: str,
) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr=(
                "Runner Fabric disposable target qualification: "
                f"INVALID:{reason}\n"
            ),
        )

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=fake_run,
    )

    result = runner.run()

    assert result == {
        "schemaVersion": "runner-mcp/disposable-target-qualification-status/v1",
        "state": "invalid",
        "reasonCode": reason,
        "qualificationPassed": False,
        "normalActivationEnabled": False,
    }


def test_unlisted_destroy_reason_is_rejected(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr=(
                "Runner Fabric disposable target qualification: "
                "INVALID:destroy-arbitrary-provider-detail\n"
            ),
        )

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="qualification_failed",
    ):
        runner.run()


def test_unknown_nonzero_result_is_sanitized(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr="/private/path token=secret",
        )

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="qualification_failed",
    ) as captured:
        runner.run()

    assert "/private/path" not in str(captured.value)
    assert "secret" not in str(captured.value)


def test_missing_private_config_blocks_before_process(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    called = False

    def fake_run(command, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("process must not be called")

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={},
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="config_unavailable",
    ):
        runner.run()

    assert called is False


def test_operator_stop_blocks_before_process(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")
    stop = tmp_path / "operator.stop"
    stop.write_text("stop", encoding="utf-8")
    guard = OperatorSafetyGuard(
        stop_file=stop,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )

    runner = FabricDisposableTargetQualificationRunner(
        safety=guard,
        environment={qualification_config_environment_key(): str(config)},
        home=home,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("process must not be called")
        ),
    )

    with pytest.raises(OperatorStopActive):
        runner.run()


def test_unmanaged_launcher_fails_closed(tmp_path: Path) -> None:
    home = tmp_path / "home"
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n", encoding="utf-8")
    launcher.chmod(0o700)
    config = tmp_path / "qualification.json"
    config.write_text("{}", encoding="utf-8")

    runner = FabricDisposableTargetQualificationRunner(
        safety=safety(tmp_path),
        environment={qualification_config_environment_key(): str(config)},
        home=home,
    )

    with pytest.raises(
        FabricDisposableTargetQualificationError,
        match="launcher_unmanaged",
    ):
        runner.run()
