"""Read-only Q7 preflight refuses false Claude-ready claims."""
from pathlib import Path

import pytest

from runner_mcp.fabric_coding_availability import (
    FabricCodingAvailabilityQualificationRunner,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy

_ENV = {
    "RUNNER_FABRIC_CODING_Q7_PROJECT_ID": "aifordable",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER": "github",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY": "Blacksp1d3r/AIfordable",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT": "/qualified/source",
    "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT": "/qualified/workspaces",
    "RUNNER_FABRIC_CODING_Q7_WORKER_URL": "http://127.0.0.1:8030/mcp",
    "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "s" * 48,
}


def make_home(tmp_path: Path, *, managed: bool) -> Path:
    home = tmp_path / "home"
    launcher = home / ".local/bin/runner-fabric"
    launcher.parent.mkdir(parents=True)
    if managed:
        target = (
            home / ".local/state/runner-fabric/control-plane-update"
            / "slots" / ("a" * 40) / "bin"
        )
        target.mkdir(parents=True)
        binary = target / "runner-fabric"
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o700)
        launcher.symlink_to(binary)
    else:
        launcher.write_text("#!/bin/sh\n")
    return home


def run_preflight(tmp_path: Path, *, env=None, managed=True,
                  stop=False, retention=True):
    home = make_home(tmp_path, managed=managed)
    safety_file = tmp_path / "stop"
    if stop:
        safety_file.write_text("stop")
    runner = FabricCodingAvailabilityQualificationRunner(
        safety=OperatorSafetyGuard(
            safety_file, RetentionPolicy(), retention_confirmed=retention,
        ),
        environment=dict(_ENV if env is None else env),
        home=home,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("preflight must never execute a subprocess")
        ),
    )
    return runner.preflight()


def test_valid_fixed_preflight_is_not_provider_or_dispatch_ready(tmp_path: Path):
    report = run_preflight(tmp_path)
    assert report == {
        "schemaVersion": "runner-mcp/coding-availability-preflight/v1",
        "state": "ready-for-qualification",
        "reason_code": "bounded_q7_preflight_passed",
        "qualification_executed": False,
        "provider_session_checked": False,
        "dispatch_authorized": False,
    }
    assert "s" * 48 not in repr(report)
    assert "/qualified/" not in repr(report)


@pytest.mark.parametrize(
    ("missing_key", "expected"),
    [
        ("RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN", "q7_private_configuration_incomplete"),
        ("RUNNER_FABRIC_CODING_Q7_WORKER_URL", "q7_private_configuration_incomplete"),
    ],
)
def test_missing_private_binding_is_actionable_but_secret_free(
    tmp_path: Path, missing_key: str, expected: str,
):
    values = dict(_ENV)
    values.pop(missing_key)
    report = run_preflight(tmp_path, env=values)
    assert report["state"] == "wait"
    assert report["reason_code"] == expected
    assert report["dispatch_authorized"] is False
    assert missing_key not in repr(report)


def test_unmanaged_launcher_is_wait_without_executing_it(tmp_path: Path):
    report = run_preflight(tmp_path, managed=False)
    assert report["state"] == "wait"
    assert report["reason_code"] == "fabric_launcher_unqualified"


def test_operator_stop_precedes_configuration_and_launcher_checks(tmp_path: Path):
    report = run_preflight(tmp_path, env={}, managed=False, stop=True)
    assert report["state"] == "blocked"
    assert report["reason_code"] == "operator_stop_active"


def test_unconfirmed_retention_blocks_without_process(tmp_path: Path):
    report = run_preflight(tmp_path, retention=False)
    assert report["state"] == "blocked"
    assert report["reason_code"] == "operator_safety_unqualified"


def test_no_report_claims_real_model_session_or_execution(tmp_path: Path):
    cases = [
        run_preflight(tmp_path / "one", env={}),
        run_preflight(tmp_path / "two", managed=False),
        run_preflight(tmp_path / "three"),
    ]
    assert all(c["qualification_executed"] is False for c in cases)
    assert all(c["provider_session_checked"] is False for c in cases)
    assert all(c["dispatch_authorized"] is False for c in cases)
