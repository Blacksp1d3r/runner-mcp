from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_CONFIG_ENV = "RUNNER_FABRIC_WORKER_QUALIFICATION_PROVISIONING_CONFIG"
_SCHEMA = "runner.mcp/worker-qualification-provisioning-config/v1"
_STATE_SCHEMA = "runner.mcp/worker-qualification-provisioning-state/v1"
_RESULT_SCHEMA = "runner.fabric/worker-qualification-provisioning-result/v1"
_ALLOWED_CAPABILITY = "bewind-ocr-qualification-v1"

_SYMBOLIC_RE = re.compile(r"^[a-z][a-z0-9._-]{0,95}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class FabricWorkerQualificationProvisioningError(RuntimeError):
    """Sanitized fail-closed provisioning failure."""


class FabricWorkerQualificationProvisioner:
    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: Mapping[str, str],
        home: Path | None = None,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.home = (home or Path.home()).expanduser().resolve()

    def provision(
        self,
        *,
        worker_id: str,
        capability_profile: str,
        generation: int,
        plan_digest: str,
        policy_expires_at: str,
        fabric_revision: str,
        request_fingerprint: str,
    ) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)

        worker_id = _symbolic(worker_id, "worker identity")
        if capability_profile != _ALLOWED_CAPABILITY:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_capability_unavailable"
            )
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_generation_invalid"
            )
        _digest(plan_digest, "enrollment plan digest")
        expires = _timestamp(policy_expires_at)
        if datetime.now(UTC) >= expires:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_policy_expired"
            )
        _commit(fabric_revision)
        _digest(request_fingerprint, "request fingerprint")

        trusted = self._trusted_binding()
        if (
            trusted["workerId"] != worker_id
            or trusted["capabilityProfile"] != capability_profile
            or trusted["generation"] != generation
        ):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_binding_mismatch"
            )

        observed_revision = self._managed_launcher_revision()
        if observed_revision != fabric_revision:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_revision_mismatch"
            )

        state = {
            "schemaVersion": _STATE_SCHEMA,
            "workerId": worker_id,
            "capabilityProfile": capability_profile,
            "generation": generation,
            "planDigest": plan_digest,
            "policyExpiresAt": expires.astimezone(UTC).isoformat(),
            "fabricRevision": fabric_revision,
            "requestFingerprint": request_fingerprint,
            "normalActivationEnabled": False,
        }
        self._write_or_verify_state(worker_id, state)

        return {
            "schemaVersion": _RESULT_SCHEMA,
            "workerId": worker_id,
            "capabilityProfile": capability_profile,
            "state": "ready",
            "reasonCode": "qualification-state-ready",
            "observedGeneration": generation,
            "observedFabricRevision": observed_revision,
            "requestFingerprint": request_fingerprint,
            "managedLauncherReady": True,
            "qualificationStateReady": True,
            "normalActivationEnabled": False,
        }

    def _trusted_binding(self) -> dict[str, Any]:
        path = self._private_config_path()
        try:
            metadata = path.stat()
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_unavailable"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_unmanaged"
            )
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_unmanaged"
            )
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_invalid"
            ) from exc

        expected = {
            "schemaVersion",
            "workerId",
            "capabilityProfile",
            "generation",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_invalid"
            )
        if value["schemaVersion"] != _SCHEMA:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_invalid"
            )
        _symbolic(value["workerId"], "worker identity")
        if value["capabilityProfile"] != _ALLOWED_CAPABILITY:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_invalid"
            )
        if (
            isinstance(value["generation"], bool)
            or not isinstance(value["generation"], int)
            or value["generation"] < 1
        ):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_invalid"
            )
        return value

    def _private_config_path(self) -> Path:
        raw = self.environment.get(_CONFIG_ENV)
        if (
            not isinstance(raw, str)
            or not raw
            or len(raw) > 4096
            or "\x00" in raw
        ):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_unavailable"
            )
        path = Path(raw)
        if not path.is_absolute():
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_config_unavailable"
            )
        return path

    def _managed_launcher_revision(self) -> str:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        try:
            metadata = launcher.lstat()
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_launcher_unavailable"
            ) from exc
        if not stat.S_ISLNK(metadata.st_mode):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_launcher_unmanaged"
            )

        slots = (
            self.home
            / ".local"
            / "state"
            / "runner-fabric"
            / "control-plane-update"
            / "slots"
        )
        try:
            resolved = launcher.resolve(strict=True)
            slots_resolved = slots.resolve(strict=True)
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_launcher_unmanaged"
            ) from exc
        if not resolved.is_relative_to(slots_resolved) or not os.access(resolved, os.X_OK):
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_launcher_unmanaged"
            )
        revision = resolved.parent.name
        _commit(revision)
        return revision

    def _write_or_verify_state(self, worker_id: str, state: dict[str, Any]) -> None:
        root = (
            self.home
            / ".local"
            / "state"
            / "runner-mcp"
            / "worker-qualification"
        )
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            root.chmod(0o700)
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_state_unavailable"
            ) from exc

        path = root / f"{worker_id}.json"
        encoded = json.dumps(
            state,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ) + "\n"

        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            try:
                metadata = path.stat()
                existing = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise FabricWorkerQualificationProvisioningError(
                    "fabric_worker_qualification_state_unavailable"
                ) from exc
            if (
                metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or existing != encoded
            ):
                raise FabricWorkerQualificationProvisioningError(
                    "fabric_worker_qualification_state_mismatch"
                )
            return
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "fabric_worker_qualification_state_unavailable"
            ) from exc

        try:
            os.write(fd, encoded.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)


def provisioning_config_environment_key() -> str:
    return _CONFIG_ENV


def _symbolic(value: object, label: str) -> str:
    if not isinstance(value, str) or _SYMBOLIC_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(
            f"fabric_worker_qualification_{label.replace(' ', '_')}_invalid"
        )
    return value


def _commit(value: object) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(
            "fabric_worker_qualification_revision_invalid"
        )
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(
            f"fabric_worker_qualification_{label.replace(' ', '_')}_invalid"
        )
    return value


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise FabricWorkerQualificationProvisioningError(
            "fabric_worker_qualification_expiry_invalid"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "fabric_worker_qualification_expiry_invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FabricWorkerQualificationProvisioningError(
            "fabric_worker_qualification_expiry_invalid"
        )
    return parsed.astimezone(UTC)
