from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path

from .onboarding import (
    PrivatePaths,
    TunnelRestartConfigState,
    inspect_tunnel_restart_config,
    load_env_file,
)


class TunnelRuntimeError(RuntimeError):
    """Bounded tunnel runtime failure without private process details."""


def _resolve_tunnel_client() -> Path:
    candidate = shutil.which("tunnel-client")
    if not candidate:
        raise TunnelRuntimeError("tunnel-client is unavailable")
    try:
        resolved = Path(candidate).expanduser().resolve(strict=True)
    except OSError as exc:
        raise TunnelRuntimeError("tunnel-client is unavailable") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise TunnelRuntimeError("tunnel-client is unavailable")
    return resolved


def run_managed_tunnel(
    config_dir: Path,
    *,
    port: int = 8000,
    exec_fn: Callable[[str, list[str], dict[str, str]], object] = os.execve,
) -> int:
    """Exec one fixed tunnel-client runtime against the local Runner MCP server."""

    if not 1 <= port <= 65_535:
        raise TunnelRuntimeError("tunnel MCP port is outside the supported range")

    paths = PrivatePaths.for_config_dir(config_dir)
    if inspect_tunnel_restart_config(paths.config_dir) is not TunnelRestartConfigState.COMPLETE:
        raise TunnelRuntimeError("private tunnel restart configuration is incomplete or unsafe")

    values = load_env_file(paths.config_dir / "tunnel.env")
    tunnel_id = values["CONTROL_PLANE_TUNNEL_ID"].strip()
    api_key = values["CONTROL_PLANE_API_KEY"].strip()

    health_url_file = paths.config_dir / "tunnel-health.url"
    if health_url_file.is_symlink() or (
        health_url_file.exists() and not health_url_file.is_file()
    ):
        raise TunnelRuntimeError("tunnel health evidence path is unsafe")
    try:
        health_url_file.unlink(missing_ok=True)
    except OSError as exc:
        raise TunnelRuntimeError("tunnel health evidence could not be reset safely") from exc

    executable = _resolve_tunnel_client()
    argv = [
        str(executable),
        "run",
        "--mcp-server-url",
        f"http://127.0.0.1:{port}/mcp",
        "--health-listen-addr",
        "127.0.0.1:0",
        "--health-url-file",
        str(health_url_file),
    ]
    env = os.environ.copy()
    env["CONTROL_PLANE_TUNNEL_ID"] = tunnel_id
    env["CONTROL_PLANE_API_KEY"] = api_key

    try:
        exec_fn(str(executable), argv, env)
    except OSError as exc:
        raise TunnelRuntimeError("tunnel-client could not start") from exc
    return 0
