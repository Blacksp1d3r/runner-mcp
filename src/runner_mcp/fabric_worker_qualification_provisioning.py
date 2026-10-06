from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
from collections.abc import MutableMapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_TEMPLATE_ENV = "RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON"
_QUALIFICATION_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_SCHEMA = "runner-mcp/worker-qualification-private/v1"
_RESULT_SCHEMA = "runner.fabric/worker-qualification-provisioning-result/v1"
_CAPABILITY = "bewind-ocr-qualification-v1"
_ENV_FILE_NAME = "runner-mcp.env"
_PRIVATE_DIR_NAME = "worker-qualification"
_CONFIG_NAME = "disposable-target.json"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SYMBOLIC_RE = re.compile(r"^[a-z][a-z0-9._-]{0,95}$")
_MAX_TEMPLATE_BYTES = 64 * 1024

_DISPOSABLE_KEYS = frozenset(
    {
        "mode",
        "qualification_id",
        "target_allocation_id",
        "host_binding_key",
        "project_binding_key",
        "project_name",
        "instance_binding_key",
        "instance_name",
        "network_binding_key",
        "network_name",
        "storage_binding_key",
        "storage_pool_name",
        "binding_created_at",
        "binding_expires_at",
        "incus_executable",
        "image_remote",
        "image_fingerprint",
        "cpu_count",
        "memory_mib",
        "root_disk_gib",
    }
)


class FabricWorkerQualificationProvisioningError(RuntimeError):
    """Sanitized fixed worker-qualification provisioning failure."""


class FabricWorkerQualificationProvisioner:
    """Provision only the fixed local state used by Fabric qualification."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: MutableMapping[str, str],
        config_dir: Path,
        home: Path | None = None,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
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
        worker = _symbolic(worker_id, "worker identity")
        if capability_profile != _CAPABILITY:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification capability is unsupported"
            )
        current_generation = _positive_int(generation, "worker generation")
        plan = _digest(plan_digest, "enrollment plan digest")
        revision = _commit(fabric_revision)
        expires = _timestamp(policy_expires_at)
        if datetime.now(UTC) >= expires:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification policy is expired"
            )
        fingerprint = _digest(
            request_fingerprint,
            "provisioning request fingerprint",
        )
        expected = _fingerprint(
            worker_id=worker,
            capability_profile=capability_profile,
            generation=current_generation,
            plan_digest=plan,
            policy_expires_at=expires,
            fabric_revision=revision,
        )
        if fingerprint != expected:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification request fingerprint is invalid"
            )

        template = self._template()
        if template["worker_id"] != worker:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification identity does not match private authority"
            )
        if template["capability_profile"] != capability_profile:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification capability does not match private authority"
            )
        if template["generation"] != current_generation:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification generation does not match private authority"
            )

        self._require_managed_launcher(revision)
        private_dir = self.config_dir / _PRIVATE_DIR_NAME
        _ensure_private_dir(private_dir, self.config_dir)
        config_path = private_dir / _CONFIG_NAME
        payload = dict(template["disposable_target"])
        payload["binding_expires_at"] = expires.astimezone(UTC).isoformat()
        content = (
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        try:
            atomic_replace_private(config_path, content)
        except PrivateAtomicWriteError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private state could not be written"
            ) from exc
        _require_private_file(config_path)

        binding = {_QUALIFICATION_CONFIG_ENV: str(config_path)}
        _merge_private_env(self.config_dir / _ENV_FILE_NAME, binding)
        self.environment.update(binding)

        _require_private_file(config_path)
        if self.environment.get(_QUALIFICATION_CONFIG_ENV) != str(config_path):
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification runtime binding is unavailable"
            )
        self._require_managed_launcher(revision)

        return {
            "schemaVersion": _RESULT_SCHEMA,
            "workerId": worker,
            "capabilityProfile": capability_profile,
            "state": "ready",
            "reasonCode": "qualification-state-ready",
            "observedGeneration": current_generation,
            "observedFabricRevision": revision,
            "requestFingerprint": fingerprint,
            "managedLauncherReady": True,
            "qualificationStateReady": True,
            "normalActivationEnabled": False,
        }

    def _template(self) -> dict[str, Any]:
        raw = self.environment.get(_TEMPLATE_ENV)
        if (
            not isinstance(raw, str)
            or len(raw.encode("utf-8")) > _MAX_TEMPLATE_BYTES
            or not raw.strip()
        ):
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is unavailable"
            )
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            ) from exc
        expected = {
            "schemaVersion",
            "worker_id",
            "capability_profile",
            "generation",
            "disposable_target",
        }
        if not isinstance(payload, dict) or set(payload) != expected:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            )
        if payload["schemaVersion"] != _SCHEMA:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            )
        _symbolic(payload["worker_id"], "private worker identity")
        if payload["capability_profile"] != _CAPABILITY:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            )
        _positive_int(payload["generation"], "private worker generation")
        disposable = payload["disposable_target"]
        if not isinstance(disposable, dict) or set(disposable) != _DISPOSABLE_KEYS:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            )
        if disposable.get("mode") != "af14-disposable-v1":
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private authority is invalid"
            )
        return payload

    def _require_managed_launcher(self, revision: str) -> None:
        launcher = self.home / ".local" / "bin" / "runner-fabric"
        slots = (
            self.home
            / ".local"
            / "state"
            / "runner-fabric"
            / "control-plane-update"
            / "slots"
        )
        try:
            metadata = launcher.lstat()
            if not stat.S_ISLNK(metadata.st_mode):
                raise OSError
            resolved = launcher.resolve(strict=True)
            expected_slot = (slots / revision).resolve(strict=True)
        except OSError as exc:
            raise FabricWorkerQualificationProvisioningError(
                "managed Runner Fabric launcher is unavailable"
            ) from exc
        if (
            not resolved.is_relative_to(expected_slot)
            or not os.access(resolved, os.X_OK)
        ):
            raise FabricWorkerQualificationProvisioningError(
                "managed Runner Fabric revision does not match request"
            )


def _fingerprint(
    *,
    worker_id: str,
    capability_profile: str,
    generation: int,
    plan_digest: str,
    policy_expires_at: datetime,
    fabric_revision: str,
) -> str:
    payload = {
        "capability_profile": capability_profile,
        "fabric_revision": fabric_revision,
        "generation": generation,
        "plan_digest": plan_digest,
        "policy_expires_at": policy_expires_at.astimezone(UTC).isoformat(),
        "worker_id": worker_id,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _merge_private_env(path: Path, updates: dict[str, str]) -> None:
    _require_private_file(path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification runtime configuration is unavailable"
        ) from exc
    retained: list[str] = []
    update_keys = set(updates)
    seen: set[str] = set()
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            retained.append(raw)
            continue
        key = raw.split("=", 1)[0].strip()
        if key in update_keys:
            if key in seen:
                continue
            retained.append(f"{key}={shlex.quote(updates[key])}")
            seen.add(key)
        else:
            retained.append(raw)
    for key in sorted(update_keys - seen):
        retained.append(f"{key}={shlex.quote(updates[key])}")
    content = ("\n".join(retained).rstrip("\n") + "\n").encode("utf-8")
    try:
        atomic_replace_private(path, content)
    except PrivateAtomicWriteError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification runtime configuration could not be updated"
        ) from exc
    _require_private_file(path)


def _ensure_private_dir(path: Path, parent: Path) -> None:
    if path.is_symlink():
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private directory is unsafe"
        )
    try:
        if not path.exists():
            path.mkdir(mode=0o700)
            os.chmod(path, 0o700)
        resolved = path.resolve(strict=True)
        if resolved.parent != parent:
            raise FabricWorkerQualificationProvisioningError(
                "worker qualification private directory is unsafe"
            )
        info = resolved.stat()
    except OSError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private directory is unavailable"
        ) from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private directory is unsafe"
        )
    if info.st_uid != os.getuid():
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private directory ownership is unsafe"
        )


def _require_private_file(path: Path) -> None:
    if not path.is_absolute() or path.is_symlink():
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private file is unsafe"
        )
    try:
        info = path.stat()
    except OSError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private file is unavailable"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
        or info.st_uid != os.getuid()
    ):
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification private file is unsafe"
        )


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification policy expiry is invalid"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification policy expiry is invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FabricWorkerQualificationProvisioningError(
            "worker qualification policy expiry is invalid"
        )
    return parsed.astimezone(UTC)


def _commit(value: object) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(
            "managed Runner Fabric revision is invalid"
        )
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(f"{label} is invalid")
    return value


def _symbolic(value: object, label: str) -> str:
    if not isinstance(value, str) or _SYMBOLIC_RE.fullmatch(value) is None:
        raise FabricWorkerQualificationProvisioningError(f"{label} is invalid")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise FabricWorkerQualificationProvisioningError(f"{label} is invalid")
    return value
