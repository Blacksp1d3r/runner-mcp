from __future__ import annotations

import json
import socket
from collections.abc import Callable, MutableMapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .fabric_worker_qualification_provisioning import (
    _DISPOSABLE_KEYS,
    _merge_private_env,
    _require_private_file,
)
from .operational_safety import ActionClass, OperatorSafetyGuard

_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_GENERATION = 1
_NETWORK_PROFILE = "deny-private"
_POLICY_TTL = timedelta(hours=2)
_ENDPOINT = "http://127.0.0.1:8000/mcp"
_TEMPLATE_ENV = "RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON"
_SOURCE_CONFIG_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_BEARER_ENV = "RUNNER_MCP_BEARER_TOKEN"
_PREFIX = "RUNNER_FABRIC_WORKER_QUALIFICATION_"
_SCHEMA = "runner-mcp/worker-qualification-private/v1"


class BewindWorkerQualificationPolicyError(RuntimeError):
    """Sanitized fixed Bewind worker-policy configuration failure."""


class BewindWorkerQualificationPolicyConfigurator:
    """Prepare the fixed local Bewind worker qualification policy."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: MutableMapping[str, str],
        config_dir: Path,
        hostname_provider: Callable[[], str] = socket.gethostname,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
        self.hostname_provider = hostname_provider
        self.now = now or (lambda: datetime.now(UTC))

    def configure(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        if self.hostname_provider().strip().casefold() != _WORKER_ID:
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_host_mismatch"
            )

        env_path = self.config_dir / "runner-mcp.env"
        _require_private_file(env_path)

        bearer = self.environment.get(_BEARER_ENV, "")
        if not _valid_secret(bearer):
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_runner_mcp_auth_unavailable"
            )

        target = self._source_target()
        observed_at = self.now()
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_clock_invalid"
            )
        observed_at = observed_at.astimezone(UTC)
        expires = observed_at + _POLICY_TTL

        cpu = _positive_int(target.get("cpu_count"))
        memory = _positive_int(target.get("memory_mib"))
        disk_gib = _positive_int(target.get("root_disk_gib"))
        soft_cpu = min(2, max(0, cpu - 1))
        soft_memory = min(2048, max(0, memory - 512))

        disposable = dict(target)
        disposable["binding_created_at"] = observed_at.isoformat()
        disposable["binding_expires_at"] = expires.isoformat()
        template = {
            "schemaVersion": _SCHEMA,
            "worker_id": _WORKER_ID,
            "capability_profile": _CAPABILITY,
            "generation": _GENERATION,
            "disposable_target": disposable,
        }

        updates = {
            f"{_PREFIX}WORKER_ID": _WORKER_ID,
            f"{_PREFIX}GENERATION": str(_GENERATION),
            f"{_PREFIX}NETWORK_PROFILE": _NETWORK_PROFILE,
            f"{_PREFIX}HARD_CPU_UNITS": str(cpu),
            f"{_PREFIX}HARD_MEMORY_MIB": str(memory),
            f"{_PREFIX}HARD_DISK_MIB": str(disk_gib * 1024),
            f"{_PREFIX}SOFT_RESERVE_CPU_UNITS": str(soft_cpu),
            f"{_PREFIX}SOFT_RESERVE_MEMORY_MIB": str(soft_memory),
            f"{_PREFIX}POLICY_EXPIRES_AT": expires.isoformat(),
            "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": _ENDPOINT,
            "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": bearer,
            _TEMPLATE_ENV: json.dumps(
                template,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ),
        }
        _merge_private_env(env_path, updates)
        self.environment.update(updates)

        return {
            "schemaVersion": "runner-mcp/bewind-worker-qualification-policy/v1",
            "state": "configured",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "generation": _GENERATION,
            "policyValid": True,
            "sourceTargetReady": True,
            "agentRestartRequired": True,
            "normalActivationEnabled": False,
        }

    def _source_target(self) -> dict[str, Any]:
        raw = self.environment.get(_SOURCE_CONFIG_ENV, "")
        if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_source_target_unavailable"
            )
        path = Path(raw)
        if not path.is_absolute():
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_source_target_unavailable"
            )
        try:
            _require_private_file(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_source_target_unavailable"
            ) from exc
        if (
            not isinstance(payload, dict)
            or set(payload) != _DISPOSABLE_KEYS
            or payload.get("mode") != "af14-disposable-v1"
        ):
            raise BewindWorkerQualificationPolicyError(
                "worker_qualification_policy_source_target_invalid"
            )
        for field in (
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
            "incus_executable",
            "image_remote",
            "image_fingerprint",
        ):
            value = payload.get(field)
            if not isinstance(value, str) or not value:
                raise BewindWorkerQualificationPolicyError(
                    "worker_qualification_policy_source_target_invalid"
                )
        _positive_int(payload.get("cpu_count"))
        _positive_int(payload.get("memory_mib"))
        _positive_int(payload.get("root_disk_gib"))
        return payload


def _valid_secret(value: object) -> bool:
    return (
        isinstance(value, str)
        and 32 <= len(value) <= 4096
        and value.isascii()
        and all(33 <= ord(char) < 127 for char in value)
    )


def _positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise BewindWorkerQualificationPolicyError(
            "worker_qualification_policy_source_target_invalid"
        )
    return value
