from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_SCHEMA = "runner.fabric/coding-agent-availability-qualification/v1"
_MAX_STDOUT_BYTES = 16_384
_MAX_STDERR_BYTES = 16_384
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
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
_Q7_ENV_KEYS = (
    "RUNNER_FABRIC_CODING_Q7_PROJECT_ID",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT",
    "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT",
    "RUNNER_FABRIC_CODING_Q7_WORKER_URL",
    "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN",
)


class FabricCodingAvailabilityQualificationError(RuntimeError):
    """Sanitized bounded coding availability qualification failure."""


class FabricCodingAvailabilityQualificationRunner:
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

    def run(self, case: str, expected_revision: str) -> dict[str, Any]:
        expected = _expected_case(case)
        _validate_revision(expected_revision)
        self.safety.assert_action_allowed(ActionClass.TEST)
        launcher = self._validated_launcher()
        env = self._private_environment()

        try:
            completed = self._runner(
                [
                    str(launcher),
                    "coding-agent-availability-qualify",
                    case,
                    expected_revision,
                ],
                cwd="/",
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_unavailable"
            ) from exc

        stdout = completed.stdout if isinstance(completed.stdout, str) else ""
        stderr = completed.stderr if isinstance(completed.stderr, str) else ""
        if (
            len(stdout.encode("utf-8", errors="replace")) > _MAX_STDOUT_BYTES
            or len(stderr.encode("utf-8", errors="replace")) > _MAX_STDERR_BYTES
        ):
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_output_invalid"
            )
        if completed.returncode != 0:
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_failed"
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_output_invalid"
            ) from exc

        return _validate_payload(
            payload,
            requested_case=case,
            requested_revision=expected_revision,
            expected=expected,
        )

    def _validated_launcher(self) -> Path:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        try:
            metadata = launcher.lstat()
        except OSError as exc:
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_launcher_unavailable"
            ) from exc
        if not stat.S_ISLNK(metadata.st_mode):
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_launcher_unmanaged"
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
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_launcher_unmanaged"
            ) from exc
        if not resolved.is_relative_to(slots) or not os.access(resolved, os.X_OK):
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_launcher_unmanaged"
            )
        return launcher

    def _private_environment(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for key in _Q7_ENV_KEYS:
            raw = self.environment.get(key)
            if (
                not isinstance(raw, str)
                or not raw.strip()
                or len(raw) > 4096
                or "\x00" in raw
            ):
                raise FabricCodingAvailabilityQualificationError(
                    "fabric_coding_availability_qualification_config_unavailable"
                )
            values[key] = raw

        return {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            **values,
        }


def _expected_case(case: object) -> tuple[str, str, str]:
    if not isinstance(case, str):
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_case_invalid"
        )
    try:
        return _CASES[case]
    except KeyError as exc:
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_case_invalid"
        ) from exc


def _validate_revision(expected_revision: object) -> None:
    if (
        not isinstance(expected_revision, str)
        or _REVISION_RE.fullmatch(expected_revision) is None
    ):
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_revision_invalid"
        )


def _validate_payload(
    value: object,
    *,
    requested_case: str,
    requested_revision: str,
    expected: tuple[str, str, str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_output_invalid"
        )
    expected_fields = {
        "schemaVersion",
        "case",
        "state",
        "reason_code",
        "work_unit_reason_code",
        "expected_revision",
        "assignment_requests",
        "workspace_clean",
    }
    if set(value) != expected_fields:
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_output_invalid"
        )

    expected_state, expected_reason, expected_work_unit_reason = expected
    if (
        value["schemaVersion"] != _SCHEMA
        or value["case"] != requested_case
        or value["state"] != expected_state
        or value["reason_code"] != expected_reason
        or value["work_unit_reason_code"] != expected_work_unit_reason
        or value["expected_revision"] != requested_revision
        or value["assignment_requests"] != 1
        or value["workspace_clean"] is not True
    ):
        raise FabricCodingAvailabilityQualificationError(
            "fabric_coding_availability_qualification_output_invalid"
        )
    return value
