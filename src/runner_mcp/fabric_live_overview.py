from __future__ import annotations

import os
import stat
from collections.abc import Callable
from pathlib import Path

from .agent_bus_worker import (
    _fixed_runner_fabric_executable,
    _private_state_root,
    agent_bus_worker_configured,
    validate_agent_bus_relay_config,
)
from .onboarding import load_env_file, read_private_runtime


class FabricLiveOverviewError(RuntimeError):
    """Safe fixed Runner Fabric live-overview wrapper failure."""


def fabric_live_overview_configured(config_dir: Path) -> bool:
    """Return whether the fixed private live-overview config is safely present."""

    if not agent_bus_worker_configured(config_dir):
        return False
    path = _fixed_live_overview_config()
    if not path.exists():
        return False
    _assert_private_regular_file(path)
    return True


def run_fabric_live_overview_process(
    config_dir: Path,
    *,
    execve: Callable[[str, list[str], dict[str, str]], object] = os.execve,
) -> int:
    """Exec the fixed loopback-only Runner Fabric live-overview service."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    if not fabric_live_overview_configured(paths.config_dir):
        raise FabricLiveOverviewError(
            "Runner Fabric live overview is not configured"
        )

    try:
        _origin, subject, _credential = validate_agent_bus_relay_config(
            origin=values["RUNNER_FABRIC_RELAY_ORIGIN"],
            subject=values["RUNNER_FABRIC_RELAY_SUBJECT"],
            credential=values["RUNNER_FABRIC_RELAY_CREDENTIAL"],
        )
    except (KeyError, RuntimeError) as exc:
        raise FabricLiveOverviewError(
            "Runner Fabric live overview configuration is invalid"
        ) from exc

    executable = _fixed_runner_fabric_executable()
    state_root = _private_state_root(paths.config_dir / "agent-bus-state")
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "RUNNER_FABRIC_RELAY_SUBJECT": subject,
        "RUNNER_FABRIC_AGENT_BUS_STATE_ROOT": str(state_root),
    }

    try:
        execve(
            str(executable),
            [str(executable), "live-overview-serve"],
            environment,
        )
    except OSError as exc:
        raise FabricLiveOverviewError(
            "Runner Fabric live overview could not start"
        ) from exc
    return 0


def _fixed_live_overview_config() -> Path:
    return (
        Path.home()
        / ".config"
        / "runner-fabric"
        / "live-overview.v1.json"
    )


def _assert_private_regular_file(path: Path) -> None:
    if path.is_symlink():
        raise FabricLiveOverviewError(
            "Runner Fabric live overview configuration is unsafe"
        )
    try:
        metadata = path.stat()
    except OSError as exc:
        raise FabricLiveOverviewError(
            "Runner Fabric live overview configuration is unavailable"
        ) from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & 0o077
        or metadata.st_size <= 0
        or metadata.st_size > 64 * 1024
    ):
        raise FabricLiveOverviewError(
            "Runner Fabric live overview configuration is unsafe"
        )
