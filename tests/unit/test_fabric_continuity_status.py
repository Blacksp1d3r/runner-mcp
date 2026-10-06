import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.fabric_continuity_status import (
    FabricContinuityStatusError,
    FabricContinuityStatusRunner,
)

REV = "a" * 40


def managed_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    slots = home / ".local/state/runner-fabric/control-plane-update/slots"
    slot = slots / ("b" * 40)
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
        "RUNNER_FABRIC_CI_CONTINUITY_OBSERVATION_ROOT": str(
            tmp_path / "observation"
        ),
        "RUNNER_FABRIC_SOURCE_OUTAGE_STORE_ROOT": str(tmp_path / "source"),
        "RUNNER_FABRIC_EXTERNAL_CI_INTENT_ROOT": str(tmp_path / "intent"),
        "RUNNER_FABRIC_CONTINUITY_PROJECT_ID": "project:runner-fabric",
        "RUNNER_FABRIC_CONTINUITY_FRESHNESS_SECONDS": "300",
    }


def payload(mode: str = "dual-healthy") -> dict[str, object]:
    return {
        "schemaVersion": "runner.fabric/continuity-status/v1",
        "projectId": "project:runner-fabric",
        "candidateRevision": REV,
        "mode": mode,
        "reasonCode": "both-paths-qualified",
        "localWorkAllowed": mode not in {"blocked", "external-continuity"},
        "externalSubmissionAllowed": mode in {
            "dual-healthy",
            "external-continuity",
        },
        "reconciliationRequired": mode == "reconciling",
        "sourceAuthorityState": "normal_external_primary",
        "mirrorState": "in-sync",
        "pendingExternalCount": 0,
        "oldestPendingAgeSeconds": None,
        "localMirrorAgeSeconds": 12,
        "providerOutageDrillAgeSeconds": None,
        "localOutageDrillAgeSeconds": None,
        "providerMutationEnabled": False,
    }


@pytest.mark.parametrize(
    "mode",
    [
        "dual-healthy",
        "local-continuity",
        "external-continuity",
        "reconciling",
        "blocked",
    ],
)
def test_runner_accepts_all_bounded_continuity_modes(
    tmp_path: Path,
    mode: str,
) -> None:
    home = managed_home(tmp_path)
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload(mode)),
            stderr="",
        )

    runner = FabricContinuityStatusRunner(
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    result = runner.status()

    assert result["mode"] == mode
    assert calls[0][0] == [
        str(home / ".local/bin/runner-fabric"),
        "continuity-status",
    ]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["cwd"] == "/"
    assert set(calls[0][1]["env"]) == {
        "HOME",
        "PATH",
        "LANG",
        "LC_ALL",
        "RUNNER_FABRIC_CI_CONTINUITY_OBSERVATION_ROOT",
        "RUNNER_FABRIC_SOURCE_OUTAGE_STORE_ROOT",
        "RUNNER_FABRIC_EXTERNAL_CI_INTENT_ROOT",
        "RUNNER_FABRIC_CONTINUITY_PROJECT_ID",
        "RUNNER_FABRIC_CONTINUITY_FRESHNESS_SECONDS",
    }


@pytest.mark.parametrize(
    "bad",
    [
        {**payload(), "privatePath": "/srv/private"},
        {**payload(), "schemaVersion": "runner.fabric/continuity-status/v9"},
        {**payload(), "projectId": "/private/project"},
        {**payload(), "candidateRevision": "not-a-revision"},
        {**payload(), "providerMutationEnabled": True},
        {**payload(), "pendingExternalCount": -1},
        {**payload(), "localMirrorAgeSeconds": -1},
        {**payload(), "mode": "healthy-ish"},
    ],
)
def test_invalid_or_private_output_fails_closed(
    tmp_path: Path,
    bad: dict[str, object],
) -> None:
    home = managed_home(tmp_path)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(bad),
            stderr="/private/path token=secret",
        )

    runner = FabricContinuityStatusRunner(
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricContinuityStatusError,
        match="output_invalid",
    ):
        runner.status()


def test_missing_private_binding_blocks_before_process(tmp_path: Path) -> None:
    home = managed_home(tmp_path)
    values = environment(tmp_path)
    values.pop("RUNNER_FABRIC_CONTINUITY_PROJECT_ID")
    called = False

    def fake_run(command, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("process must not be called")

    runner = FabricContinuityStatusRunner(
        environment=values,
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricContinuityStatusError,
        match="configuration_unavailable",
    ):
        runner.status()
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

    runner = FabricContinuityStatusRunner(
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricContinuityStatusError,
        match="operation_failed",
    ) as captured:
        runner.status()

    assert "/private" not in str(captured.value)
    assert "secret" not in str(captured.value)


def test_timeout_is_sanitized(tmp_path: Path) -> None:
    home = managed_home(tmp_path)

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 60)

    runner = FabricContinuityStatusRunner(
        environment=environment(tmp_path),
        home=home,
        runner=fake_run,
    )

    with pytest.raises(
        FabricContinuityStatusError,
        match="unavailable",
    ):
        runner.status()
