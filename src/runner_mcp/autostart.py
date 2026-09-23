from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .completion_delivery import completion_notifier_status
from .github_mailbox import GITHUB_MAILBOX_ENV_KEYS
from .github_watcher import GitHubWatcherCursorStore, GitHubWatcherError
from .onboarding import load_env_file, read_private_runtime
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

MANAGED_MARKER = "# Managed by Runner MCP autostart."
SERVER_UNIT = "runner-mcp.service"
GITHUB_WATCHER_UNIT = "runner-mcp-github-watcher.service"
COMPLETION_WATCHER_UNIT = "runner-mcp-completion-watcher.service"
KNOWN_UNITS = (SERVER_UNIT, GITHUB_WATCHER_UNIT, COMPLETION_WATCHER_UNIT)


class AutostartError(RuntimeError):
    """Safe user-service packaging failure without private command output."""


@dataclass(frozen=True, slots=True)
class AutostartStatus:
    component: str
    installed: bool
    enabled: bool
    active: bool

    def public_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "installed": self.installed,
            "enabled": self.enabled,
            "active": self.active,
        }


def default_user_unit_dir() -> Path:
    return (Path.home() / ".config" / "systemd" / "user").resolve()


def _validate_executable(executable: Path) -> Path:
    try:
        resolved = executable.expanduser().resolve(strict=True)
    except OSError as exc:
        raise AutostartError("Runner MCP executable is unavailable") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise AutostartError("Runner MCP executable is unavailable")
    return resolved


def _systemd_quote(value: str) -> str:
    if not value or any(char in value for char in "\r\n\x00"):
        raise AutostartError("autostart value contains unsupported characters")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _unit(
    *,
    description: str,
    executable: Path,
    config_dir: Path,
    arguments: tuple[str, ...],
    requires_server: bool,
) -> str:
    exec_parts = [
        _systemd_quote(str(executable)),
        "--config-dir",
        _systemd_quote(str(config_dir)),
        *(_systemd_quote(item) for item in arguments),
    ]
    dependency = ""
    if requires_server:
        dependency = (
            f"After=network-online.target {SERVER_UNIT}\n"
            f"Requires={SERVER_UNIT}\n"
        )
    else:
        dependency = "After=network-online.target\nWants=network-online.target\n"

    return (
        f"{MANAGED_MARKER}\n"
        "[Unit]\n"
        f"Description={description}\n"
        f"{dependency}"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={' '.join(exec_parts)}\n"
        "Restart=on-failure\n"
        "RestartSec=3\n"
        "NoNewPrivileges=true\n"
        "PrivateTmp=true\n"
        "\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def configured_autostart_components(config_dir: Path) -> tuple[str, ...]:
    config_dir = config_dir.expanduser().resolve()
    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)

    components = ["server"]
    mailbox_configured = all(
        values.get(key, "").strip() for key in GITHUB_MAILBOX_ENV_KEYS
    )
    if mailbox_configured:
        cursor = GitHubWatcherCursorStore(
            paths.config_dir / "github-mailbox-cursor.json"
        )
        try:
            cursor_head = cursor.read()
        except GitHubWatcherError as exc:
            raise AutostartError(
                "GitHub watcher bootstrap state is unavailable"
            ) from exc
        if cursor_head is None:
            raise AutostartError(
                "GitHub watcher is configured but not bootstrapped"
            )
        components.append("github-watcher")

    notifier = completion_notifier_status(config_dir)
    if notifier["configured"]:
        if not notifier["initialized"]:
            raise AutostartError(
                "completion notifier is configured but not bootstrapped"
            )
        components.append("completion-watcher")
    return tuple(components)


def systemd_user_available(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    try:
        completed = _run_systemctl(
            ["show-environment"],
            runner=runner,
            check=False,
        )
    except AutostartError:
        return False
    return completed.returncode == 0


def has_managed_user_units(
    *,
    unit_dir: Path | None = None,
) -> bool:
    target = unit_dir or default_user_unit_dir()
    expanded = target.expanduser()
    if not expanded.exists():
        return False
    if expanded.is_symlink() or not expanded.is_dir():
        raise AutostartError("systemd user unit directory is unavailable")
    for unit_name in KNOWN_UNITS:
        path = expanded / unit_name
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if content.startswith(MANAGED_MARKER + "\n"):
            return True
    return False


def render_user_units(
    *,
    config_dir: Path,
    executable: Path,
    port: int = 8000,
) -> dict[str, str]:
    if not 1 <= port <= 65535:
        raise AutostartError("autostart port must be between 1 and 65535")

    config_dir = config_dir.expanduser().resolve()
    executable = _validate_executable(executable)
    components = configured_autostart_components(config_dir)

    units = {
        SERVER_UNIT: _unit(
            description="Runner MCP loopback service",
            executable=executable,
            config_dir=config_dir,
            arguments=(
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ),
            requires_server=False,
        )
    }
    if "github-watcher" in components:
        units[GITHUB_WATCHER_UNIT] = _unit(
            description="Runner MCP GitHub mailbox watcher",
            executable=executable,
            config_dir=config_dir,
            arguments=("github-watcher", "run"),
            requires_server=True,
        )
    if "completion-watcher" in components:
        units[COMPLETION_WATCHER_UNIT] = _unit(
            description="Runner MCP completion watcher",
            executable=executable,
            config_dir=config_dir,
            arguments=("completion-watcher", "run"),
            requires_server=True,
        )
    return units


def _safe_unit_dir(unit_dir: Path) -> Path:
    expanded = unit_dir.expanduser()
    if expanded.exists() and expanded.is_symlink():
        raise AutostartError("systemd user unit directory must not be a symlink")
    try:
        expanded.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AutostartError("systemd user unit directory is unavailable") from exc
    if expanded.is_symlink() or not expanded.is_dir():
        raise AutostartError("systemd user unit directory is unavailable")
    try:
        return expanded.resolve(strict=True)
    except OSError as exc:
        raise AutostartError("systemd user unit directory is unavailable") from exc


def _write_managed_unit(path: Path, content: str) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not existing.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to replace a user service not managed by Runner MCP"
            )
    try:
        atomic_replace_private(path, content.encode("utf-8"))
    except PrivateAtomicWriteError as exc:
        raise AutostartError("autostart unit could not be written") from exc


def _run_systemctl(
    arguments: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = runner(
            ["systemctl", "--user", *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AutostartError("systemd user manager is unavailable") from exc
    if check and completed.returncode != 0:
        raise AutostartError("systemd user service operation failed")
    return completed


def install_user_services(
    config_dir: Path,
    *,
    executable: Path,
    port: int = 8000,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[str]:
    # Verify a user manager before touching service files.
    _run_systemctl(["show-environment"], runner=runner)
    units = render_user_units(
        config_dir=config_dir,
        executable=executable,
        port=port,
    )
    target = _safe_unit_dir(unit_dir or default_user_unit_dir())

    for unit_name, content in units.items():
        _write_managed_unit(target / unit_name, content)

    # Remove obsolete optional units only if Runner MCP created them.
    for unit_name in KNOWN_UNITS:
        if unit_name in units:
            continue
        path = target / unit_name
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not existing.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to remove a user service not managed by Runner MCP"
            )
        _run_systemctl(["disable", "--now", unit_name], runner=runner, check=False)
        path.unlink()

    _run_systemctl(["daemon-reload"], runner=runner)
    ordered = [name for name in KNOWN_UNITS if name in units]
    _run_systemctl(["enable", "--now", *ordered], runner=runner)
    return ordered


def user_service_status(
    *,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[AutostartStatus]:
    target = _safe_unit_dir(unit_dir or default_user_unit_dir())
    results: list[AutostartStatus] = []
    names = (
        ("server", SERVER_UNIT),
        ("github-watcher", GITHUB_WATCHER_UNIT),
        ("completion-watcher", COMPLETION_WATCHER_UNIT),
    )
    for component, unit_name in names:
        path = target / unit_name
        installed = path.exists() and path.is_file() and not path.is_symlink()
        enabled = False
        active = False
        if installed:
            enabled = (
                _run_systemctl(
                    ["is-enabled", unit_name],
                    runner=runner,
                    check=False,
                ).returncode
                == 0
            )
            active = (
                _run_systemctl(
                    ["is-active", unit_name],
                    runner=runner,
                    check=False,
                ).returncode
                == 0
            )
        results.append(
            AutostartStatus(
                component=component,
                installed=installed,
                enabled=enabled,
                active=active,
            )
        )
    return results


def remove_user_services(
    *,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[str]:
    _run_systemctl(["show-environment"], runner=runner)
    target = _safe_unit_dir(unit_dir or default_user_unit_dir())
    removed: list[str] = []
    for unit_name in KNOWN_UNITS:
        path = target / unit_name
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not content.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to remove a user service not managed by Runner MCP"
            )
        _run_systemctl(["disable", "--now", unit_name], runner=runner, check=False)
        try:
            path.unlink()
        except OSError as exc:
            raise AutostartError("autostart unit could not be removed") from exc
        removed.append(unit_name)
    _run_systemctl(["daemon-reload"], runner=runner)
    return removed
