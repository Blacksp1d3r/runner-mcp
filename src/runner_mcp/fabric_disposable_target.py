from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

from .operational_safety import ActionClass, OperatorSafetyGuard

_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_SCHEMA = "runner.fabric/disposable-target-qualification/v1"
_RUNTIME_PROFILE = "disposable-incus-vm-podman-v1"
_MAX_STDOUT_BYTES = 16_384
_MAX_STDERR_BYTES = 16_384
_QUALIFICATION_ID_RE = re.compile(r"^[a-z][a-z0-9._-]{0,95}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_BOUNDED_FAILURE_PREFIX = "Runner Fabric disposable target qualification: INVALID:"
_BOUNDED_FAILURE_REASONS = frozenset(
    {
        "config-unavailable",
        "config-invalid",
        "time-invalid",
        "clean-start",
        "create",
        "guest-agent-not-ready",
        "guest-runtime-not-ready",
        "isolation",
        "destroy",
        "recreate",
        "recreate-isolation",
        "final-destroy",
        "recovery-cleanup",
        "runtime-unavailable",
    }
)



class FabricDisposableTargetQualificationError(RuntimeError):
    """Sanitized bounded qualification failure."""


class FabricDisposableTargetQualificationRunner:
    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: Mapping[str, str],
        home: Path | None = None,
        runner=subprocess.run,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.home = (home or Path.home()).expanduser().resolve()
        self._runner = runner

    def run(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        launcher = self._validated_launcher()
        config_path = self._private_config_path()

        env = {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            _CONFIG_ENV: str(config_path),
        }

        try:
            completed = self._runner(
                [str(launcher), "disposable-target-qualify"],
                cwd="/",
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_unavailable"
            ) from exc

        stdout = completed.stdout if isinstance(completed.stdout, str) else ""
        stderr = completed.stderr if isinstance(completed.stderr, str) else ""
        if (
            len(stdout.encode("utf-8", errors="replace")) > _MAX_STDOUT_BYTES
            or len(stderr.encode("utf-8", errors="replace")) > _MAX_STDERR_BYTES
        ):
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_output_invalid"
            )
        if completed.returncode != 0:
            reason = _bounded_failure_reason(stderr)
            suffix = f":{reason}" if reason is not None else ""
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_failed" + suffix
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_output_invalid"
            ) from exc

        return _validate_payload(payload)

    def _validated_launcher(self) -> Path:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        try:
            metadata = launcher.lstat()
        except OSError as exc:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_launcher_unavailable"
            ) from exc
        if not stat.S_ISLNK(metadata.st_mode):
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_launcher_unmanaged"
            )
        try:
            resolved = launcher.resolve(strict=True)
            slots = (
                self.home
                / ".local"
                / "state"
                / "runner-fabric"
                / "control-plane-update"
                / "slots"
            ).resolve(strict=True)
        except OSError as exc:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_launcher_unmanaged"
            ) from exc
        if not resolved.is_relative_to(slots) or not os.access(resolved, os.X_OK):
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_launcher_unmanaged"
            )
        return launcher

    def _private_config_path(self) -> Path:
        raw = self.environment.get(_CONFIG_ENV)
        if (
            not isinstance(raw, str)
            or not raw
            or len(raw) > 4096
            or "\x00" in raw
        ):
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_config_unavailable"
            )
        path = Path(raw)
        if not path.is_absolute():
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_config_unavailable"
            )
        return path


def _bounded_failure_reason(stderr: str) -> str | None:
    detail = stderr.strip()
    if not detail.startswith(_BOUNDED_FAILURE_PREFIX):
        return None
    reason = detail.removeprefix(_BOUNDED_FAILURE_PREFIX).strip()
    if reason not in _BOUNDED_FAILURE_REASONS:
        return None
    return reason


def _validate_payload(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
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
    if set(value) != expected:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        )
    if (
        value["schemaVersion"] != _SCHEMA
        or value["runtimeProfile"] != _RUNTIME_PROFILE
        or value["finalState"] != "destroyed"
        or value["qualificationPassed"] is not True
        or value["normalActivationEnabled"] is not False
    ):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        )

    qualification_id = value["qualificationId"]
    if (
        not isinstance(qualification_id, str)
        or _QUALIFICATION_ID_RE.fullmatch(qualification_id) is None
    ):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        )

    target_id = value["targetAllocationId"]
    if not isinstance(target_id, str):
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        )
    try:
        parsed = UUID(target_id)
    except ValueError as exc:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        ) from exc
    if str(parsed) != target_id:
        raise FabricDisposableTargetQualificationError(
            "fabric_disposable_target_qualification_output_invalid"
        )

    for field in (
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
    ):
        if value[field] is not True:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_output_invalid"
            )

    for field in ("imageFingerprint", "bootstrapSha256"):
        item = value[field]
        if not isinstance(item, str) or _SHA256_RE.fullmatch(item) is None:
            raise FabricDisposableTargetQualificationError(
                "fabric_disposable_target_qualification_output_invalid"
            )

    return value


def qualification_config_environment_key() -> str:
    return _CONFIG_ENV
