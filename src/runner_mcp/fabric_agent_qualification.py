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
    external_target_config = values.get(_EXTERNAL_TARGET_CONFIG_KEY, "").strip()
    if external_target_config and (
        "\x00" in external_target_config
        or "\n" in external_target_config
        or "\r" in external_target_config
        or not Path(external_target_config).is_absolute()
    ):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is invalid"
        )
    executable = _fixed_runner_fabric_executable()
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        _RESOURCE_URL_KEY: endpoint,
        _BEARER_TOKEN_KEY: token,
    }
    if external_target_config:
        environment[_EXTERNAL_TARGET_CONFIG_KEY] = external_target_config

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
