"""Recover only the fixed Bewind disposable qualification target."""

from __future__ import annotations

import json
import stat
import subprocess
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_PROJECT_NAME = "rf-bewind-qualification"
_INSTANCE_NAME = "rf-bewind-ocr"
_NETWORK_NAME = "rf-bewind-net"
_INCUS = "/usr/bin/incus"
_MAX_CAPTURE = 64 * 1024
_RETRIES = 6


class BewindDisposableTargetRecoveryError(RuntimeError):
    """Sanitized fixed disposable-target recovery failure."""


class BewindDisposableTargetRecovery:
    """Idempotently remove only the fixed Bewind qualification target."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: Mapping[str, str],
        runner=subprocess.run,
        sleep=time.sleep,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self._runner = runner
        self._sleep = sleep

    def recover(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        self._require_fixed_binding()

        initial_project, initial_instance, initial_network = self._state()

        for attempt in range(_RETRIES):
            project_present, instance_present, network_present = self._state()

            if instance_present:
                self._incus(
                    (
                        "--project",
                        _PROJECT_NAME,
                        "delete",
                        _INSTANCE_NAME,
                        "--force",
                    ),
                    timeout=120,
                )

            if project_present and not self._instance_present():
                self._incus(
                    ("project", "delete", _PROJECT_NAME),
                    timeout=120,
                )

            if network_present and not self._project_present():
                self._incus(
                    (
                        "--project",
                        "default",
                        "network",
                        "delete",
                        _NETWORK_NAME,
                    ),
                    timeout=120,
                )

            project_present, instance_present, network_present = self._state()
            if not project_present and not instance_present and not network_present:
                return {
                    "schemaVersion": "runner-mcp/bewind-disposable-target-recovery/v1",
                    "state": "clean",
                    "workerId": _WORKER_ID,
                    "capabilityProfile": _CAPABILITY,
                    "instanceAbsent": True,
                    "projectAbsent": True,
                    "networkAbsent": True,
                    "staleInstancePresent": initial_instance,
                    "staleProjectPresent": initial_project,
                    "staleNetworkPresent": initial_network,
                    "normalActivationEnabled": False,
                }
            if attempt + 1 < _RETRIES:
                self._sleep(1)

        raise BewindDisposableTargetRecoveryError(
            "bewind_disposable_target_recovery_incomplete"
        )

    def _require_fixed_binding(self) -> None:
        raw = self.environment.get(_CONFIG_ENV)
        if not isinstance(raw, str) or not raw or "\x00" in raw:
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_unavailable"
            )
        path = Path(raw)
        if not path.is_absolute():
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_unavailable"
            )
        try:
            metadata = path.lstat()
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_unavailable"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or metadata.st_mode & 0o077
            or not isinstance(payload, dict)
        ):
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_unsafe"
            )
        if (
            payload.get("host_binding_key") != _WORKER_ID
            or payload.get("project_name") != _PROJECT_NAME
            or payload.get("instance_name") != _INSTANCE_NAME
            or payload.get("network_name") != _NETWORK_NAME
            or payload.get("incus_executable") != _INCUS
        ):
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_mismatch"
            )
        try:
            expires = datetime.fromisoformat(payload["binding_expires_at"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_invalid"
            ) from exc
        if expires.tzinfo is None or datetime.now(UTC) >= expires.astimezone(UTC):
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_binding_expired"
            )

    def _state(self) -> tuple[bool, bool, bool]:
        project_present = self._project_present()
        instance_present = self._instance_present() if project_present else False
        network_present = self._network_present()
        return project_present, instance_present, network_present

    def _project_present(self) -> bool:
        return _PROJECT_NAME in self._names(
            ("project", "list", "--format=json"),
            category="project-inspection-failed",
        )

    def _instance_present(self) -> bool:
        if not self._project_present():
            return False
        return _INSTANCE_NAME in self._names(
            ("--project", _PROJECT_NAME, "list", "--format=json"),
            category="instance-inspection-failed",
        )

    def _network_present(self) -> bool:
        return _NETWORK_NAME in self._names(
            (
                "--project",
                "default",
                "network",
                "list",
                "--format=json",
            ),
            category="network-inspection-failed",
        )

    def _names(self, args: tuple[str, ...], *, category: str) -> set[str]:
        result = self._incus(args)
        if result.returncode != 0:
            raise BewindDisposableTargetRecoveryError(
                f"bewind_disposable_target_recovery_{category}"
            )
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise BewindDisposableTargetRecoveryError(
                f"bewind_disposable_target_recovery_{category}"
            ) from exc
        if not isinstance(payload, list):
            raise BewindDisposableTargetRecoveryError(
                f"bewind_disposable_target_recovery_{category}"
            )
        return {
            str(item.get("name"))
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    def _incus(
        self,
        args: tuple[str, ...],
        *,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self._runner(
                (_INCUS, *args),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                cwd="/",
                env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_incus_unavailable"
            ) from exc
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        if (
            len(stdout.encode(errors="replace")) > _MAX_CAPTURE
            or len(stderr.encode(errors="replace")) > _MAX_CAPTURE
        ):
            raise BewindDisposableTargetRecoveryError(
                "bewind_disposable_target_recovery_output_exceeded"
            )
        return result
