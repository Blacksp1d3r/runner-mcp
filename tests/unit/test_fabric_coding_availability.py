import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.fabric_coding_availability import (
    FabricCodingAvailabilityQualificationError,
    FabricCodingAvailabilityQualificationRunner,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)

_CASES = {
    "provider-temporarily-unavailable": (
        "wait",
        "provider_temporarily_unavailable",
        "coding_worker_wait",
    ),
    "subscription-auth-required": (
        "operator-required",
        "subscription_auth_required",
        "coding_worker_operator_required",
    ),
    "unsafe-billing-configuration": (
        "blocked",
        "unsafe_billing_configuration",
        "coding_worker_blocked",
    ),
}
_Q7_ENV = {
    "RUNNER_FABRIC_CODING_Q7_PROJECT_ID": "project:q7",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER": "github",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY": "Blacksp1d3r/AIfordable",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT": "/srv/q7/source",
    "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT": "/srv/q7/workspaces",
    "RUNNER_FABRIC_CODING_Q7_WORKER_URL": "http://127.0.0.1:9021/mcp",
    "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "k" * 48,
}


def _safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def _managed_home(tmp_path: Path) -> Path:
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


def _payload(case: str, revision: str) -> dict:
    state, reason, work_reason = _CASES[case]
    return {
        "schemaVersion": "runner.fabric/coding-agent-availability-qualification/v1",
        "case": case,
        "state": state,
        "reason_code": reason,
        "work_unit_reason_code": work_reason,
        "expected_revision": revision,
        "assignment_requests": 1,
        "workspace_clean": True,
    }


@pytest.mark.parametrize("case", tuple(_CASES))
def test_qualification_invokes_only_fixed_managed_command(
    tmp_path: Path,
    case: str,
) -> None:
    home = _managed_home(tmp_path)
    revision = "b" * 40
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(_payload(case, revision)),
            stderr="",
        )

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=_Q7_ENV,
        home=home,
        runner=fake_run,
    )

    result = runner.run(case, revision)

    assert result["case"] == case
    assert result["assignment_requests"] == 1
    assert result["workspace_clean"] is True
    command, kwargs = calls[0]
    assert command == [
        str(home / ".local/bin/runner-fabric"),
        "coding-agent-availability-qualify",
        case,
        revision,
    ]
    assert kwargs["shell"] is False
    assert kwargs["cwd"] == "/"
    assert kwargs["timeout"] == 300
    assert set(kwargs["env"]) == {
        "HOME",
        "PATH",
        "LANG",
        "LC_ALL",
        *_Q7_ENV,
    }
    assert "/srv/q7" not in repr(result)
    assert "k" * 48 not in repr(result)


@pytest.mark.parametrize(
    ("case", "revision"),
    [
        ("other", "b" * 40),
        ("provider-temporarily-unavailable", "B" * 40),
        ("provider-temporarily-unavailable", "short"),
    ],
)
def test_invalid_inputs_fail_before_process(
    tmp_path: Path,
    case: str,
    revision: str,
) -> None:
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("process must not run")

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=_Q7_ENV,
        home=_managed_home(tmp_path),
        runner=fake_run,
    )
    with pytest.raises(FabricCodingAvailabilityQualificationError):
        runner.run(case, revision)
    assert called is False


@pytest.mark.parametrize(
    "mutator",
    [
        lambda item: item.update({"privatePath": "/srv/private"}),
        lambda item: item.update({"assignment_requests": 2}),
        lambda item: item.update({"assignment_requests": True}),
        lambda item: item.update({"assignment_requests": 1.0}),
        lambda item: item.update({"assignment_requests": "1"}),
        lambda item: item.update({"assignment_requests": False}),
        lambda item: item.update({"workspace_clean": False}),
        lambda item: item.update({"state": "run"}),
        lambda item: item.update({"expected_revision": "c" * 40}),
    ],
)
def test_private_or_mismatched_output_fails_closed(
    tmp_path: Path,
    mutator,
) -> None:
    case = "provider-temporarily-unavailable"
    revision = "b" * 40
    value = _payload(case, revision)
    mutator(value)

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(value),
            stderr="private token=secret",
        )

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=_Q7_ENV,
        home=_managed_home(tmp_path),
        runner=fake_run,
    )
    with pytest.raises(
        FabricCodingAvailabilityQualificationError,
        match="output_invalid",
    ):
        runner.run(case, revision)


def test_nonzero_result_is_sanitized(tmp_path: Path) -> None:
    case = "subscription-auth-required"
    revision = "b" * 40

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr="/private/path token=secret",
        )

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=_Q7_ENV,
        home=_managed_home(tmp_path),
        runner=fake_run,
    )
    with pytest.raises(
        FabricCodingAvailabilityQualificationError,
        match="qualification_failed",
    ) as captured:
        runner.run(case, revision)
    assert "/private/path" not in str(captured.value)
    assert "secret" not in str(captured.value)


def test_missing_private_config_blocks_before_process(tmp_path: Path) -> None:
    values = dict(_Q7_ENV)
    values.pop("RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN")
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("process must not run")

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=values,
        home=_managed_home(tmp_path),
        runner=fake_run,
    )
    with pytest.raises(
        FabricCodingAvailabilityQualificationError,
        match="config_unavailable",
    ):
        runner.run("unsafe-billing-configuration", "b" * 40)
    assert called is False


def test_operator_stop_blocks_before_process(tmp_path: Path) -> None:
    stop = tmp_path / "operator.stop"
    stop.write_text("stop", encoding="utf-8")
    guard = OperatorSafetyGuard(
        stop_file=stop,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    runner = FabricCodingAvailabilityQualificationRunner(
        safety=guard,
        environment=_Q7_ENV,
        home=_managed_home(tmp_path),
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("process must not run")
        ),
    )
    with pytest.raises(OperatorStopActive):
        runner.run("unsafe-billing-configuration", "b" * 40)


def test_unmanaged_launcher_fails_closed(tmp_path: Path) -> None:
    home = tmp_path / "home"
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n", encoding="utf-8")
    launcher.chmod(0o700)

    runner = FabricCodingAvailabilityQualificationRunner(
        safety=_safety(tmp_path),
        environment=_Q7_ENV,
        home=home,
    )
    with pytest.raises(
        FabricCodingAvailabilityQualificationError,
        match="launcher_unmanaged",
    ):
        runner.run("unsafe-billing-configuration", "b" * 40)
