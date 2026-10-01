from __future__ import annotations

import os
import stat
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit

from .onboarding import load_env_file, read_private_runtime

_RELAY_KEYS = (
    "RUNNER_FABRIC_RELAY_ORIGIN",
    "RUNNER_FABRIC_RELAY_SUBJECT",
    "RUNNER_FABRIC_RELAY_CREDENTIAL",
)
_LOCAL_ENDPOINT_KEY = "RUNNER_MCP_AGENT_BUS_LOCAL_ENDPOINT"


class AgentBusWorkerError(RuntimeError):
    """Safe Agent Bus worker wrapper failure without private values."""


def validate_agent_bus_relay_config(
    *,
    origin: object,
    subject: object,
    credential: object,
) -> tuple[str, str, str]:
    if not isinstance(origin, str) or not origin:
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid")
    try:
        parsed = urlsplit(origin)
    except ValueError as exc:
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid")

    if not isinstance(subject, str) or not subject.startswith("runner:"):
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid")
    suffix = subject.removeprefix("runner:")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._:-")
    if (
        not suffix
        or len(subject) > 127
        or suffix[0] not in "abcdefghijklmnopqrstuvwxyz0123456789"
        or any(char not in allowed for char in suffix)
    ):
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid")

    if not _valid_secret(credential):
        raise AgentBusWorkerError("Agent Bus relay configuration is invalid")
    return origin.rstrip("/"), subject, credential


def agent_bus_worker_configured(config_dir: Path) -> bool:
    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    present = tuple(bool(values.get(key, "").strip()) for key in _RELAY_KEYS)
    if any(present) and not all(present):
        raise AgentBusWorkerError("Agent Bus worker configuration is incomplete")
    return all(present)


def run_agent_bus_worker_process(
    config_dir: Path,
    *,
    once: bool = False,
    execve: Callable[[str, list[str], dict[str, str]], object] = os.execve,
) -> int:
    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)

    if not agent_bus_worker_configured(paths.config_dir):
        raise AgentBusWorkerError("Agent Bus worker is not configured")

    relay_origin, relay_subject, relay_credential = validate_agent_bus_relay_config(
        origin=values["RUNNER_FABRIC_RELAY_ORIGIN"],
        subject=values["RUNNER_FABRIC_RELAY_SUBJECT"],
        credential=values["RUNNER_FABRIC_RELAY_CREDENTIAL"],
    )

    runner_mcp_token = values.get("RUNNER_MCP_BEARER_TOKEN", "")
    if not _valid_secret(runner_mcp_token):
        raise AgentBusWorkerError("Agent Bus worker configuration is invalid")

    endpoint = values.get(
        _LOCAL_ENDPOINT_KEY,
        "http://127.0.0.1:8000/mcp",
    ).strip()
    _validate_loopback_endpoint(endpoint)

    if not isinstance(once, bool):
        raise TypeError("once must be a boolean")
    executable = _fixed_runner_fabric_executable()
    state_root = _private_state_root(paths.config_dir / "agent-bus-state")

    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "RUNNER_FABRIC_RELAY_ORIGIN": relay_origin,
        "RUNNER_FABRIC_RELAY_SUBJECT": relay_subject,
        "RUNNER_FABRIC_RELAY_CREDENTIAL": relay_credential,
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": endpoint,
        "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": runner_mcp_token,
        "RUNNER_FABRIC_AGENT_BUS_STATE_ROOT": str(state_root),
    }

    try:
        execve(
            str(executable),
            [
                str(executable),
                "agent-bus-run-once" if once else "agent-bus-run",
            ],
            environment,
        )
    except OSError as exc:
        raise AgentBusWorkerError("Agent Bus worker could not start") from exc
    return 0


def _fixed_runner_fabric_executable() -> Path:
    launcher = Path.home() / ".local" / "bin" / "runner-fabric"
    try:
        resolved = launcher.resolve(strict=True)
    except OSError as exc:
        raise AgentBusWorkerError("Runner Fabric executable is unavailable") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise AgentBusWorkerError("Runner Fabric executable is unavailable")
    return resolved


def _private_state_root(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.exists() and expanded.is_symlink():
        raise AgentBusWorkerError("Agent Bus state directory is unsafe")
    try:
        expanded.mkdir(mode=0o700, parents=False, exist_ok=True)
        os.chmod(expanded, 0o700)
        resolved = expanded.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise AgentBusWorkerError("Agent Bus state directory is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_mode & 0o077:
        raise AgentBusWorkerError("Agent Bus state directory is unsafe")
    return resolved


def _validate_loopback_endpoint(value: str) -> None:
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise AgentBusWorkerError("Agent Bus worker configuration is invalid") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/mcp"
    ):
        raise AgentBusWorkerError("Agent Bus worker configuration is invalid")


def _valid_secret(value: object) -> bool:
    return (
        isinstance(value, str)
        and 32 <= len(value) <= 4096
        and value.isascii()
        and all(ord(char) >= 33 and ord(char) != 127 for char in value)
    )
