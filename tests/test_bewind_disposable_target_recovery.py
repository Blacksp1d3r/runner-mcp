from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp.bewind_disposable_target_recovery import (
    BewindDisposableTargetRecovery,
    BewindDisposableTargetRecoveryError,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def binding(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    path = tmp_path / "target.json"
    payload = {
        "host_binding_key": "aifordable-lab",
        "project_name": "rf-bewind-qualification",
        "instance_name": "rf-bewind-ocr",
        "network_name": "rf-bewind-net",
        "incus_executable": "/usr/bin/incus",
        "binding_expires_at": (
            datetime.now(UTC) + timedelta(hours=1)
        ).isoformat(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path, {
        "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": str(path)
    }


def completed(stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess([], returncode, stdout, "")


def test_recovery_is_idempotent_when_target_is_already_absent(
    tmp_path: Path,
) -> None:
    _path, env = binding(tmp_path)

    def runner(argv, **_kwargs):
        args = argv[1:]
        if args == ("project", "list", "--format=json"):
            return completed("[]")
        if args == (
            "--project",
            "default",
            "network",
            "list",
            "--format=json",
        ):
            return completed("[]")
        raise AssertionError(args)

    result = BewindDisposableTargetRecovery(
        safety=safety(tmp_path),
        environment=env,
        runner=runner,
    ).recover()

    assert result["state"] == "clean"
    assert result["instanceAbsent"] is True
    assert result["projectAbsent"] is True
    assert result["networkAbsent"] is True
    assert result["staleInstancePresent"] is False
    assert result["staleProjectPresent"] is False
    assert result["staleNetworkPresent"] is False
    assert result["normalActivationEnabled"] is False


def test_recovery_deletes_only_fixed_bound_target(tmp_path: Path) -> None:
    _path, env = binding(tmp_path)
    calls = []
    state = {"instance": True, "project": True, "network": True}

    def runner(argv, **_kwargs):
        args = argv[1:]
        calls.append(args)
        if args == ("project", "list", "--format=json"):
            return completed(
                json.dumps(
                    [{"name": "rf-bewind-qualification"}]
                    if state["project"]
                    else []
                )
            )
        if args == (
            "--project",
            "rf-bewind-qualification",
            "list",
            "--format=json",
        ):
            return completed(
                json.dumps(
                    [{"name": "rf-bewind-ocr"}]
                    if state["instance"]
                    else []
                )
            )
        if args == (
            "--project",
            "default",
            "network",
            "list",
            "--format=json",
        ):
            return completed(
                json.dumps(
                    [{"name": "rf-bewind-net"}]
                    if state["network"]
                    else []
                )
            )
        if args == (
            "--project",
            "rf-bewind-qualification",
            "delete",
            "rf-bewind-ocr",
            "--force",
        ):
            state["instance"] = False
            return completed()
        if args == ("project", "delete", "rf-bewind-qualification"):
            state["project"] = False
            return completed()
        if args == (
            "--project",
            "default",
            "network",
            "delete",
            "rf-bewind-net",
        ):
            state["network"] = False
            return completed()
        raise AssertionError(args)

    result = BewindDisposableTargetRecovery(
        safety=safety(tmp_path),
        environment=env,
        runner=runner,
        sleep=lambda _seconds: None,
    ).recover()

    assert result["state"] == "clean"
    assert result["staleInstancePresent"] is True
    assert result["staleProjectPresent"] is True
    assert result["staleNetworkPresent"] is True
    assert any("rf-bewind-ocr" in args for args in calls)
    assert any("rf-bewind-qualification" in args for args in calls)
    assert any("rf-bewind-net" in args for args in calls)


def test_binding_mismatch_fails_before_incus(tmp_path: Path) -> None:
    path, env = binding(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["instance_name"] = "other"
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)

    def runner(*_args, **_kwargs):
        raise AssertionError("must not call Incus")

    with pytest.raises(
        BewindDisposableTargetRecoveryError,
        match="binding_mismatch",
    ):
        BewindDisposableTargetRecovery(
            safety=safety(tmp_path),
            environment=env,
            runner=runner,
        ).recover()


def test_expired_binding_fails_closed(tmp_path: Path) -> None:
    path, env = binding(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["binding_expires_at"] = (
        datetime.now(UTC) - timedelta(minutes=1)
    ).isoformat()
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)

    with pytest.raises(
        BewindDisposableTargetRecoveryError,
        match="binding_expired",
    ):
        BewindDisposableTargetRecovery(
            safety=safety(tmp_path),
            environment=env,
        ).recover()
