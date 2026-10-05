from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

from .fabric_agent_runtime import FabricAgentRestartError, _validated_launcher
from .operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    SafetyConfigurationError,
)

_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_SCHEMA = "runner.fabric/disposable-target-qualification/v1"
_MAX_OUTPUT = 32 * 1024


class FabricDisposableTargetQualificationError(RuntimeError):
    """Bounded failure for the fixed disposable-target qualification control."""


def qualify_fabric_disposable_target(
    *,
    safety: OperatorSafetyGuard,
    private_values: Mapping[str, str],
    home: Path | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    if not isinstance(safety, OperatorSafetyGuard):
        raise TypeError("safety must be OperatorSafetyGuard")
    if not isinstance(private_values, Mapping):
        raise TypeError("private_values must be a mapping")

    try:
        safety.assert_action_allowed(ActionClass.TEST)
    except (OperatorStopActive, SafetyConfigurationError) as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_blocked"
        ) from exc

    pointer = private_values.get(_CONFIG_ENV)
    if (
        not isinstance(pointer, str)
        or not pointer
        or "\x00" in pointer
        or not Path(pointer).is_absolute()
    ):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_unconfigured"
        )

    home_root = (home or Path.home()).expanduser().resolve()
    try:
        launcher = _validated_launcher(home_root)
    except FabricAgentRestartError as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_unavailable"
        ) from exc

    env = {
        "HOME": str(home_root),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        _CONFIG_ENV: pointer,
    }
    try:
        completed = runner(
            (str(launcher), "disposable-target-qualify"),
            cwd="/",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=900,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_failed"
        ) from exc

    if completed.returncode != 0:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_failed"
        )
    if not isinstance(completed.stdout, str):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    encoded = completed.stdout.encode("utf-8", errors="strict")
    if not encoded or len(encoded) > _MAX_OUTPUT:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        ) from exc
    return _validate_payload(payload)


def _validate_payload(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    expected = {
        "schemaVersion",
        "qualificationId",
        "targetAllocationId",
        "runtimeProfile",
        "createdReady",
        "resourceLimitsVerified",
        "guestRuntimeVerified",
        "managementAuthorityBlocked",
        "noDefaultRoute",
        "networkPolicyVerified",
        "destroyVerified",
        "recreateVerified",
        "recreateIsolationVerified",
        "finalDestroyVerified",
        "imageFingerprint",
        "bootstrapSha256",
        "qualificationPassed",
        "normalActivationEnabled",
        "finalState",
    }
    if set(value) != expected or value.get("schemaVersion") != _SCHEMA:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    qualification_id = value.get("qualificationId")
    if (
        not isinstance(qualification_id, str)
        or not 1 <= len(qualification_id) <= 96
        or any(
            not (char.islower() or char.isdigit() or char in "._-")
            for char in qualification_id
        )
        or not qualification_id[0].islower()
    ):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    target_id = value.get("targetAllocationId")
    if not isinstance(target_id, str):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    try:
        parsed = UUID(target_id)
    except ValueError as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        ) from exc
    if str(parsed) != target_id:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    if value.get("runtimeProfile") != "disposable-incus-vm-podman-v1":
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )

    required_true = (
        "createdReady",
        "resourceLimitsVerified",
        "guestRuntimeVerified",
        "managementAuthorityBlocked",
        "noDefaultRoute",
        "networkPolicyVerified",
        "destroyVerified",
        "recreateVerified",
        "recreateIsolationVerified",
        "finalDestroyVerified",
        "qualificationPassed",
    )
    if any(value.get(field) is not True for field in required_true):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    if value.get("normalActivationEnabled") is not False:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    if value.get("finalState") != "destroyed":
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    for field in ("imageFingerprint", "bootstrapSha256"):
        digest = value.get(field)
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_invalid"
            )

    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    forbidden = (
        "private",
        "credential",
        "token",
        "password",
        "authorization",
        "endpoint",
        "socket",
        "projectname",
        "instancename",
        "networkname",
        "storagepool",
        "/home/",
        "/srv/",
        "/var/",
    )
    lowered = raw.casefold()
    if any(fragment in lowered for fragment in forbidden):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_invalid"
        )
    return value
