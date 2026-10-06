from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_REQUIRED_ENV_KEYS = (
    "RUNNER_FABRIC_CI_CONTINUITY_OBSERVATION_ROOT",
    "RUNNER_FABRIC_SOURCE_OUTAGE_STORE_ROOT",
    "RUNNER_FABRIC_EXTERNAL_CI_INTENT_ROOT",
    "RUNNER_FABRIC_CONTINUITY_PROJECT_ID",
)
_OPTIONAL_ENV_KEYS = ("RUNNER_FABRIC_CONTINUITY_FRESHNESS_SECONDS",)
_SCHEMA = "runner.fabric/continuity-status/v1"
_MAX_STDOUT_BYTES = 32_768
_MAX_STDERR_BYTES = 16_384
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")
_MODES = {
    "dual-healthy",
    "local-continuity",
    "external-continuity",
    "reconciling",
    "blocked",
}
_AUTHORITY_STATES = {
    "normal_external_primary",
    "external_unavailable_read_only",
    "local_primary_fenced",
    "reconciling",
    "external_primary_restored",
    "blocked_conflict",
}
_MIRROR_STATES = {"in-sync", "out-of-sync", "unavailable", "unknown"}


class FabricContinuityStatusError(RuntimeError):
    """Sanitized bounded continuity-status bridge failure."""


class FabricContinuityStatusRunner:
    """Invoke only the fixed managed Runner Fabric read-only continuity status."""

    def __init__(
        self,
        *,
        environment: Mapping[str, str],
        home: Path | None = None,
        runner=subprocess.run,
    ) -> None:
        self.environment = environment
        self.home = (home or Path.home()).expanduser().resolve()
        self._runner = runner

    def status(self) -> dict[str, Any]:
        launcher = self._validated_launcher()
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        for key in _REQUIRED_ENV_KEYS:
            value = self.environment.get(key)
            if not _bounded_env_value(value):
                raise FabricContinuityStatusError(
                    "fabric_continuity_status_configuration_unavailable"
                )
            env[key] = value

        for key in _OPTIONAL_ENV_KEYS:
            value = self.environment.get(key)
            if value is not None:
                if not _bounded_env_value(value):
                    raise FabricContinuityStatusError(
                        "fabric_continuity_status_configuration_unavailable"
                    )
                env[key] = value

        try:
            completed = self._runner(
                [str(launcher), "continuity-status"],
                cwd="/",
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricContinuityStatusError(
                "fabric_continuity_status_unavailable"
            ) from exc

        stdout = completed.stdout if isinstance(completed.stdout, str) else ""
        stderr = completed.stderr if isinstance(completed.stderr, str) else ""
        if (
            len(stdout.encode("utf-8", errors="replace")) > _MAX_STDOUT_BYTES
            or len(stderr.encode("utf-8", errors="replace")) > _MAX_STDERR_BYTES
        ):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_output_invalid"
            )
        if completed.returncode != 0:
            raise FabricContinuityStatusError(
                "fabric_continuity_status_operation_failed"
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise FabricContinuityStatusError(
                "fabric_continuity_status_output_invalid"
            ) from exc
        return _validate_status(payload)

    def _validated_launcher(self) -> Path:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        try:
            metadata = launcher.lstat()
        except OSError as exc:
            raise FabricContinuityStatusError(
                "fabric_continuity_status_launcher_unavailable"
            ) from exc
        if not stat.S_ISLNK(metadata.st_mode):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_launcher_unmanaged"
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
            raise FabricContinuityStatusError(
                "fabric_continuity_status_launcher_unmanaged"
            ) from exc
        if not resolved.is_relative_to(slots) or not os.access(resolved, os.X_OK):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_launcher_unmanaged"
            )
        return launcher


def _validate_status(value: object) -> dict[str, Any]:
    expected = {
        "schemaVersion",
        "projectId",
        "candidateRevision",
        "mode",
        "reasonCode",
        "localWorkAllowed",
        "externalSubmissionAllowed",
        "reconciliationRequired",
        "sourceAuthorityState",
        "mirrorState",
        "pendingExternalCount",
        "oldestPendingAgeSeconds",
        "localMirrorAgeSeconds",
        "providerOutageDrillAgeSeconds",
        "localOutageDrillAgeSeconds",
        "providerMutationEnabled",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise FabricContinuityStatusError(
            "fabric_continuity_status_output_invalid"
        )
    if (
        value["schemaVersion"] != _SCHEMA
        or not isinstance(value["projectId"], str)
        or _PROJECT_RE.fullmatch(value["projectId"]) is None
        or not isinstance(value["candidateRevision"], str)
        or _REVISION_RE.fullmatch(value["candidateRevision"]) is None
        or value["mode"] not in _MODES
        or not isinstance(value["reasonCode"], str)
        or _REASON_RE.fullmatch(value["reasonCode"]) is None
        or value["sourceAuthorityState"] not in _AUTHORITY_STATES
        or value["mirrorState"] not in _MIRROR_STATES
        or value["providerMutationEnabled"] is not False
    ):
        raise FabricContinuityStatusError(
            "fabric_continuity_status_output_invalid"
        )

    for field in (
        "localWorkAllowed",
        "externalSubmissionAllowed",
        "reconciliationRequired",
    ):
        if not isinstance(value[field], bool):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_output_invalid"
            )

    count = value["pendingExternalCount"]
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count < 0
        or count > 100_000
    ):
        raise FabricContinuityStatusError(
            "fabric_continuity_status_output_invalid"
        )

    for field in (
        "oldestPendingAgeSeconds",
        "localMirrorAgeSeconds",
        "providerOutageDrillAgeSeconds",
        "localOutageDrillAgeSeconds",
    ):
        if not _valid_age(value[field]):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_output_invalid"
            )

    return value


def _valid_age(value: object) -> bool:
    if value is None:
        return True
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and 0 <= value <= 31_536_000
    )


def _bounded_env_value(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= 4096
        and "\x00" not in value
    )
