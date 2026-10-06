import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.fabric_repository_mirrors import (
    FabricRepositoryMirrorError,
    FabricRepositoryMirrorRunner,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    RetentionPolicy,
)


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


def environment(tmp_path: Path) -> dict[str, str]:
    return {
        "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT": str(
            tmp_path / "inventory"
        ),
        "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT": str(tmp_path / "mirrors"),
        "RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE": str(
            tmp_path / "managed.json"
        ),
        "RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG": str(
            tmp_path / "gitconfig"
        ),
    }


def preflight_payload() -> dict:
    return {
        "schemaVersion": "runner.fabric/repository-mirror-preflight/v1",
        "ready": True,
        "managedRepositoryCount": 8,
        "mutationEnabled": False,
        "networkChecked": False,
    }


def reconcile_payload() -> dict:
    return {
        "schemaVersion": "runner.fabric/repository-mirror-runtime-report/v1",
        "total": 8,
        "succeeded": 8,
        "failed": 0,
        "inventoryRevision": 12,
        "successful": True,
    }


def test_runner_invokes_only_fixed_mirror_commands(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    calls = []
    responses = [preflight_payload(), reconcile_payload()]

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(responses.pop(0)),
            stderr="",
        )

    runner = FabricRepositoryMirrorRunner(
        safety=safety(tmp_path),
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    assert runner.preflight()["ready"] is True
    assert runner.reconcile()["successful"] is True

    launcher = str(home / ".local/bin/runner-fabric")
    assert [item[0] for item in calls] == [
        [launcher, "repository-mirrors-preflight"],
        [launcher, "repository-mirrors-reconcile"],
    ]
    for _, kwargs in calls:
        assert kwargs["shell"] is False
        assert kwargs["cwd"] == "/"
        assert set(kwargs["env"]) == {
            "HOME",
            "PATH",
            "LANG",
            "LC_ALL",
            "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT",
            "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT",
            "RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE",
            "RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG",
        }


@pytest.mark.parametrize(
    "payload",
    [
        {**preflight_payload(), "privatePath": "/srv/private"},
        {**preflight_payload(), "mutationEnabled": True},
        {**preflight_payload(), "managedRepositoryCount": 0},
        {**reconcile_payload(), "token": "secret"},
        {**reconcile_payload(), "failed": 1},
        {**reconcile_payload(), "successful": False},
    ],
)
def test_invalid_or_private_output_fails_closed(
    tmp_path: Path,
    payload: dict,
) -> None:
    home = managed_home(tmp_path)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload),
            stderr="/private/path token=secret",
        )

    runner = FabricRepositoryMirrorRunner(
        safety=safety(tmp_path),
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    method = (
        runner.preflight
        if "managedRepositoryCount" in payload
        else runner.reconcile
    )
    with pytest.raises(
        FabricRepositoryMirrorError,
        match="output_invalid",
    ):
        method()


def test_missing_private_binding_blocks_before_process(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    called = False
    values = environment(tmp_path)
    values.pop("RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE")

    def fake_run(command, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("process must not be called")

    runner = FabricRepositoryMirrorRunner(
        safety=safety(tmp_path),
        environment=values,
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricRepositoryMirrorError,
        match="configuration_unavailable",
    ):
        runner.preflight()
    assert called is False


def test_nonzero_result_is_sanitized(tmp_path: Path) -> None:
    home = managed_home(tmp_path)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr="/private/path token=secret",
        )

    runner = FabricRepositoryMirrorRunner(
        safety=safety(tmp_path),
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricRepositoryMirrorError,
        match="operation_failed",
    ) as captured:
        runner.preflight()

    assert "/private" not in str(captured.value)
    assert "secret" not in str(captured.value)
