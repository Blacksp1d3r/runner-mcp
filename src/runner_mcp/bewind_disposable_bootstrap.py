from __future__ import annotations

import json
import re
import socket
import subprocess
from collections.abc import Callable, MutableMapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from .fabric_worker_qualification_provisioning import (
    _ensure_private_dir,
    _merge_private_env,
    _require_private_file,
)
from .operational_safety import ActionClass, OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_GENERATION = 1
_QUALIFICATION_ID = "bewind-ocr-lab-v1"
_MODE = "af14-disposable-v1"
_TTL = timedelta(hours=2)
_PRIVATE_DIR = "worker-qualification"
_CONFIG_NAME = "disposable-target.json"
_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_NAMESPACE = UUID("3a5c4596-031a-5c72-92ae-6b99487de8e6")

_PROJECT_BINDING_KEY = "bewind-qualification"
_PROJECT_NAME = "rf-bewind-qualification"
_INSTANCE_BINDING_KEY = "bewind-ocr-guest"
_INSTANCE_NAME = "rf-bewind-ocr"
_NETWORK_BINDING_KEY = "bewind-ocr-net"
_NETWORK_NAME = "rf-bewind-ocr-net"
_STORAGE_BINDING_KEY = "default"
_STORAGE_POOL_NAME = "default"
_INCUS_EXECUTABLE = "/usr/bin/incus"
_IMAGE_REMOTE = "local"
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_TRUSTED_IMAGE_OS = "ubuntu"
_TRUSTED_IMAGE_RELEASE = "noble"
_TRUSTED_IMAGE_TYPE = "virtual-machine"
_TRUSTED_IMAGE_SERVER = "https://images.linuxcontainers.org"
_TRUSTED_IMAGE_PROTOCOL = "simplestreams"
_TRUSTED_IMAGE_ALIAS = "ubuntu/24.04"
_CPU_COUNT = 4
_MEMORY_MIB = 8192
_ROOT_DISK_GIB = 20


def _load_image_inventory() -> object:
    try:
        completed = subprocess.run(
            (_INCUS_EXECUTABLE, "image", "list", "--format=json"),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
            env={"LANG": "C", "LC_ALL": "C"},
            cwd="/",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BewindDisposableBootstrapError(
            "bewind_disposable_bootstrap_image_inventory_unavailable"
        ) from exc
    if completed.returncode != 0:
        raise BewindDisposableBootstrapError(
            "bewind_disposable_bootstrap_image_inventory_unavailable"
        )
    try:
        return json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise BewindDisposableBootstrapError(
            "bewind_disposable_bootstrap_image_inventory_invalid"
        ) from exc


def _resolve_trusted_image_fingerprint(payload: object) -> str:
    if not isinstance(payload, list):
        raise BewindDisposableBootstrapError(
            "bewind_disposable_bootstrap_image_inventory_invalid"
        )
    matches: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        properties = item.get("properties")
        source = item.get("update_source")
        fingerprint = item.get("fingerprint")
        image_type = str(item.get("type", "")).strip().casefold()
        if not isinstance(properties, dict) or not isinstance(source, dict):
            continue
        if image_type != _TRUSTED_IMAGE_TYPE:
            continue
        if str(properties.get("os", "")).strip().casefold() != _TRUSTED_IMAGE_OS:
            continue
        if str(properties.get("release", "")).strip().casefold() != _TRUSTED_IMAGE_RELEASE:
            continue
        if str(source.get("server", "")).strip() != _TRUSTED_IMAGE_SERVER:
            continue
        if str(source.get("protocol", "")).strip().casefold() != _TRUSTED_IMAGE_PROTOCOL:
            continue
        if str(source.get("alias", "")).strip() != _TRUSTED_IMAGE_ALIAS:
            continue
        if not isinstance(fingerprint, str) or _HEX64_RE.fullmatch(fingerprint) is None:
            continue
        matches.append(fingerprint)
    if len(matches) != 1:
        raise BewindDisposableBootstrapError(
            "bewind_disposable_bootstrap_trusted_image_unavailable"
        )
    return matches[0]


class BewindDisposableBootstrapError(RuntimeError):
    """Sanitized fixed Bewind disposable-target bootstrap failure."""


class BewindDisposableBootstrapRestorer:
    """Restore only the fixed owner-only aifordable-lab Bewind bootstrap."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: MutableMapping[str, str],
        config_dir: Path,
        hostname_provider: Callable[[], str] = socket.gethostname,
        now: Callable[[], datetime] | None = None,
        image_inventory_provider: Callable[[], object] | None = None,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
        self.hostname_provider = hostname_provider
        self.now = now or (lambda: datetime.now(UTC))
        self.image_inventory_provider = image_inventory_provider or _load_image_inventory

    def restore(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        if self.hostname_provider().strip().casefold() != _WORKER_ID:
            raise BewindDisposableBootstrapError(
                "bewind_disposable_bootstrap_host_mismatch"
            )

        env_path = self.config_dir / "runner-mcp.env"
        try:
            _require_private_file(env_path)
        except RuntimeError as exc:
            raise BewindDisposableBootstrapError(
                "bewind_disposable_bootstrap_private_runtime_unavailable"
            ) from exc

        observed_at = self.now()
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise BewindDisposableBootstrapError(
                "bewind_disposable_bootstrap_clock_invalid"
            )
        observed_at = observed_at.astimezone(UTC)
        expires_at = observed_at + _TTL

        private_dir = self.config_dir / _PRIVATE_DIR
        try:
            _ensure_private_dir(private_dir, self.config_dir)
        except RuntimeError as exc:
            raise BewindDisposableBootstrapError(
                "bewind_disposable_bootstrap_private_state_unavailable"
            ) from exc

        image_fingerprint = _resolve_trusted_image_fingerprint(
            self.image_inventory_provider()
        )

        allocation_id = uuid5(
            _NAMESPACE,
            f"{_WORKER_ID}:{_CAPABILITY}:{_GENERATION}",
        )
        payload = {
            "mode": _MODE,
            "qualification_id": _QUALIFICATION_ID,
            "target_allocation_id": str(allocation_id),
            "host_binding_key": _WORKER_ID,
            "project_binding_key": _PROJECT_BINDING_KEY,
            "project_name": _PROJECT_NAME,
            "instance_binding_key": _INSTANCE_BINDING_KEY,
            "instance_name": _INSTANCE_NAME,
            "network_binding_key": _NETWORK_BINDING_KEY,
            "network_name": _NETWORK_NAME,
            "storage_binding_key": _STORAGE_BINDING_KEY,
            "storage_pool_name": _STORAGE_POOL_NAME,
            "binding_created_at": observed_at.isoformat(),
            "binding_expires_at": expires_at.isoformat(),
            "incus_executable": _INCUS_EXECUTABLE,
            "image_remote": _IMAGE_REMOTE,
            "image_fingerprint": image_fingerprint,
            "cpu_count": _CPU_COUNT,
            "memory_mib": _MEMORY_MIB,
            "root_disk_gib": _ROOT_DISK_GIB,
        }

        config_path = private_dir / _CONFIG_NAME
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
            _require_private_file(config_path)
            _merge_private_env(env_path, {_CONFIG_ENV: str(config_path)})
        except (PrivateAtomicWriteError, RuntimeError) as exc:
            raise BewindDisposableBootstrapError(
                "bewind_disposable_bootstrap_write_failed"
            ) from exc

        self.environment[_CONFIG_ENV] = str(config_path)
        return {
            "schemaVersion": "runner-mcp/bewind-disposable-bootstrap/v1",
            "state": "restored",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "generation": _GENERATION,
            "qualificationId": _QUALIFICATION_ID,
            "targetAllocationId": str(allocation_id),
            "policyValid": True,
            "normalActivationEnabled": False,
        }
