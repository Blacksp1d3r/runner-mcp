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
