from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_ENV_KEYS = (
    "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT",
    "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT",
    "RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE",
    "RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG",
)
_PREFLIGHT_SCHEMA = "runner.fabric/repository-mirror-preflight/v1"
_RECONCILE_SCHEMA = "runner.fabric/repository-mirror-runtime-report/v1"
_MAX_STDOUT_BYTES = 16_384
_MAX_STDERR_BYTES = 16_384


class FabricRepositoryMirrorError(RuntimeError):
    """Sanitized bounded repository-mirror control failure."""


class FabricRepositoryMirrorRunner:
    """Invoke only the fixed managed Runner Fabric F34 mirror operations."""

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

    def preflight(self) -> dict[str, Any]:
        return self._run(
            command="repository-mirrors-preflight",
            timeout_seconds=120,
            validator=_validate_preflight,
        )

    def readiness(self) -> dict[str, Any]:
        inventory_ready = _safe_private_dir(
            self.environment.get("RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT")
        )
        mirror_ready = _safe_private_dir(
            self.environment.get("RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT")
        )
        desired_ready = _safe_private_file(
            self.environment.get("RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE")
        )
        credential_ready = _safe_private_file(
            self.environment.get("RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG")
        )
        try:
            self._validated_launcher()
            runtime_ready = True
        except FabricRepositoryMirrorError:
            runtime_ready = False

        configured_count = sum(
            bool(self.environment.get(key))
            for key in _ENV_KEYS
        )
        if configured_count == 0:
            activation_state = "unconfigured"
        elif configured_count == len(_ENV_KEYS):
            activation_state = "configured"
        else:
            activation_state = "partial"

        storage_ready = inventory_ready and mirror_ready
        ready = (
            storage_ready
            and desired_ready
            and credential_ready
            and runtime_ready
        )
        if ready:
            reason = "ready"
        elif not runtime_ready:
            reason = "fabric-runtime-unavailable"
        elif not storage_ready:
            reason = "storage-binding-unavailable"
        elif not desired_ready:
            reason = "desired-state-binding-unavailable"
        else:
            reason = "credential-binding-unavailable"

        return {
            "schemaVersion": "runner-mcp/fabric-repository-mirror-activation-readiness/v1",
            "ready": ready,
            "storageReady": storage_ready,
            "desiredStateReady": desired_ready,
            "credentialBindingReady": credential_ready,
            "fabricRuntimeReady": runtime_ready,
            "activationState": activation_state,
            "reasonCode": reason,
            "mutationEnabled": False,
        }

    def reconcile(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.BACKUP)
        return self._run(
            command="repository-mirrors-reconcile",
            timeout_seconds=900,
            validator=_validate_reconcile,
        )

    def _run(
        self,
        *,
        command: str,
        timeout_seconds: int,
        validator,
    ) -> dict[str, Any]:
        launcher = self._validated_launcher()
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        for key in _ENV_KEYS:
            value = self.environment.get(key)
            if (
                not isinstance(value, str)
                or not value
                or len(value) > 4096
                or "\x00" in value
            ):
                raise FabricRepositoryMirrorError(
                    "fabric_repository_mirror_configuration_unavailable"
                )
            env[key] = value

        try:
            completed = self._runner(
                [str(launcher), command],
                cwd="/",
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_unavailable"
            ) from exc

        stdout = completed.stdout if isinstance(completed.stdout, str) else ""
        stderr = completed.stderr if isinstance(completed.stderr, str) else ""
        if (
            len(stdout.encode("utf-8", errors="replace")) > _MAX_STDOUT_BYTES
            or len(stderr.encode("utf-8", errors="replace")) > _MAX_STDERR_BYTES
        ):
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_output_invalid"
            )
        if completed.returncode != 0:
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_operation_failed"
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_output_invalid"
            ) from exc
        return validator(payload)

    def _validated_launcher(self) -> Path:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        try:
            metadata = launcher.lstat()
        except OSError as exc:
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_launcher_unavailable"
            ) from exc
        if not stat.S_ISLNK(metadata.st_mode):
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_launcher_unmanaged"
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
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_launcher_unmanaged"
            ) from exc
        if not resolved.is_relative_to(slots) or not os.access(resolved, os.X_OK):
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_launcher_unmanaged"
            )
        return launcher




def _safe_private_dir(value: object) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        return False
    try:
        metadata = path.stat()
    except OSError:
        return False
    return (
        stat.S_ISDIR(metadata.st_mode)
        and not (metadata.st_mode & 0o077)
        and os.access(path, os.W_OK | os.X_OK)
    )


def _safe_private_file(value: object) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        return False
    try:
        metadata = path.stat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and not (metadata.st_mode & 0o077)

def _validate_preflight(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schemaVersion",
        "ready",
        "managedRepositoryCount",
        "mutationEnabled",
        "networkChecked",
    }:
        raise FabricRepositoryMirrorError(
            "fabric_repository_mirror_output_invalid"
        )
    count = value["managedRepositoryCount"]
    if (
        value["schemaVersion"] != _PREFLIGHT_SCHEMA
        or value["ready"] is not True
        or value["mutationEnabled"] is not False
        or value["networkChecked"] is not False
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count < 1
        or count > 10_000
    ):
        raise FabricRepositoryMirrorError(
            "fabric_repository_mirror_output_invalid"
        )
    return value


def _validate_reconcile(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schemaVersion",
        "total",
        "succeeded",
        "failed",
        "inventoryRevision",
        "successful",
    }:
        raise FabricRepositoryMirrorError(
            "fabric_repository_mirror_output_invalid"
        )
    if value["schemaVersion"] != _RECONCILE_SCHEMA:
        raise FabricRepositoryMirrorError(
            "fabric_repository_mirror_output_invalid"
        )
    for field in ("total", "succeeded", "failed", "inventoryRevision"):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise FabricRepositoryMirrorError(
                "fabric_repository_mirror_output_invalid"
            )
    if (
        value["total"] < 1
        or value["total"] > 10_000
        or value["succeeded"] + value["failed"] != value["total"]
        or value["inventoryRevision"] < 1
        or not isinstance(value["successful"], bool)
        or value["successful"] is not (value["failed"] == 0)
    ):
        raise FabricRepositoryMirrorError(
            "fabric_repository_mirror_output_invalid"
        )
    return value
