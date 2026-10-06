from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from .agent_bus_worker import (
    _fixed_runner_fabric_executable,
    _valid_secret,
    _validate_agent_mcp_endpoint,
)
from .onboarding import load_env_file, read_private_runtime

_RESOURCE_URL_KEY = "RUNNER_FABRIC_AGENT_RESOURCE_URL"
_BEARER_TOKEN_KEY = "RUNNER_FABRIC_AGENT_BEARER_TOKEN"
_EXTERNAL_TARGET_CONFIG_KEY = "RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG"
_KEYS = (_RESOURCE_URL_KEY, _BEARER_TOKEN_KEY)
_RUNNER_MCP_KEYS = (
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN",
)
_A6_EXCLUSIVE_KEYS = (
    "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT",
    "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN",
    "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_ID",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION",
)
_A6_KEYS = (*_A6_EXCLUSIVE_KEYS, *_RUNNER_MCP_KEYS)
_WORKER_QUALIFICATION_EXCLUSIVE_KEYS = (
    "RUNNER_FABRIC_WORKER_QUALIFICATION_WORKER_ID",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_GENERATION",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_NETWORK_PROFILE",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_CPU_UNITS",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_MEMORY_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_DISK_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_CPU_UNITS",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_MEMORY_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_POLICY_EXPIRES_AT",
)
_WORKER_QUALIFICATION_KEYS = (
    *_WORKER_QUALIFICATION_EXCLUSIVE_KEYS,
    *_RUNNER_MCP_KEYS,
)


class FabricAgentQualificationError(RuntimeError):
    """Safe fixed Runner Fabric qualification-agent wrapper failure."""


def fabric_agent_qualification_configured(config_dir: Path) -> bool:
    """Return whether the private qualification-agent bridge is fully configured."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    present = tuple(bool(values.get(key, "").strip()) for key in _KEYS)
    if any(present) and not all(present):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is incomplete"
        )
    if not all(present):
        return False
    try:
        _validate_agent_mcp_endpoint(values[_RESOURCE_URL_KEY].strip())
    except RuntimeError as exc:
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is invalid"
        ) from exc
    if not _valid_secret(values[_BEARER_TOKEN_KEY]):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is invalid"
        )
    return True


def qualification_agent_environment_additions(
    config_dir: Path,
) -> dict[str, str]:
    """Return only fixed optional Fabric qualification bindings."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    additions: dict[str, str] = {}

    external_target_config = values.get(_EXTERNAL_TARGET_CONFIG_KEY, "").strip()
    if external_target_config:
        if (
            "\x00" in external_target_config
            or "\n" in external_target_config
            or "\r" in external_target_config
            or not Path(external_target_config).is_absolute()
        ):
            raise FabricAgentQualificationError(
                "Runner Fabric qualification agent configuration is invalid"
            )
        additions[_EXTERNAL_TARGET_CONFIG_KEY] = external_target_config

    a6_triggered = any(
        bool(values.get(key, "").strip()) for key in _A6_EXCLUSIVE_KEYS
    )
    if a6_triggered:
        if not all(bool(values.get(key, "").strip()) for key in _A6_KEYS):
            raise FabricAgentQualificationError(
                "Runner Fabric A6 qualification configuration is incomplete"
            )
        _forward_private_values(
            values,
            additions,
            _A6_KEYS,
            invalid_message="Runner Fabric A6 qualification configuration is invalid",
        )

    worker_triggered = any(
        bool(values.get(key, "").strip())
        for key in _WORKER_QUALIFICATION_EXCLUSIVE_KEYS
    )
    if worker_triggered:
        if not all(
            bool(values.get(key, "").strip())
            for key in _WORKER_QUALIFICATION_KEYS
        ):
            raise FabricAgentQualificationError(
                "Runner Fabric worker qualification configuration is incomplete"
            )
        _forward_private_values(
            values,
            additions,
            _WORKER_QUALIFICATION_KEYS,
            invalid_message=(
                "Runner Fabric worker qualification configuration is invalid"
            ),
        )
    return additions


def _forward_private_values(
    values: dict[str, str],
    additions: dict[str, str],
    keys: tuple[str, ...],
    *,
    invalid_message: str,
) -> None:
    for key in keys:
        value = values[key]
        if "\x00" in value or "\n" in value or "\r" in value:
            raise FabricAgentQualificationError(invalid_message)
        additions[key] = value


def run_fabric_agent_qualification_process(
    config_dir: Path,
    *,
    execve: Callable[[str, list[str], dict[str, str]], object] = os.execve,
) -> int:
    """Exec only the fixed qualification-only Runner Fabric Agent MCP."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    if not fabric_agent_qualification_configured(paths.config_dir):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent is not configured"
        )

    endpoint = values[_RESOURCE_URL_KEY].strip()
    token = values[_BEARER_TOKEN_KEY]
    additions = qualification_agent_environment_additions(paths.config_dir)
    executable = _fixed_runner_fabric_executable()
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        _RESOURCE_URL_KEY: endpoint,
        _BEARER_TOKEN_KEY: token,
    }
    environment.update(additions)

    try:
        execve(
            str(executable),
            [str(executable), "agent-serve-qualification"],
            environment,
        )
    except OSError as exc:
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent could not start"
        ) from exc
    return 0
