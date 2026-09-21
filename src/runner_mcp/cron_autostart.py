from __future__ import annotations

import fcntl
import os
import shlex
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

CRON_BEGIN = "# BEGIN RUNNER MCP AUTOSTART v1"
CRON_END = "# END RUNNER MCP AUTOSTART v1"
CRON_COMPONENTS = ("server", "github-watcher", "completion-watcher")


class CronAutostartError(RuntimeError):
    """Safe cron-autostart failure without private command output."""


@dataclass(frozen=True, slots=True)
class CronComponentStatus:
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


def _crontab_executable() -> str:
    candidate = shutil.which("crontab")
    if not candidate:
        raise CronAutostartError("crontab is unavailable")
    resolved = Path(candidate).resolve()
    if not resolved.is_absolute() or not resolved.is_file():
        raise CronAutostartError("crontab is unavailable")
    return str(resolved)


def _run_crontab(
    arguments: list[str],
    *,
    input_text: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    executable = _crontab_executable()
    try:
        completed = runner(
            [executable, *arguments],
            input=input_text,
            stdin=None if input_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CronAutostartError("crontab operation failed") from exc
    if check and completed.returncode != 0:
        raise CronAutostartError("crontab operation failed")
    return completed


def read_crontab(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    completed = _run_crontab(["-l"], runner=runner, check=False)
    if completed.returncode == 0:
        return completed.stdout
    # Most cron implementations return 1 when the user has no crontab.
    if completed.returncode == 1:
        return ""
    raise CronAutostartError("crontab could not be read")


def _managed_block_bounds(lines: list[str]) -> tuple[int, int] | None:
    begins = [index for index, line in enumerate(lines) if line == CRON_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == CRON_END]
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise CronAutostartError("managed Runner MCP crontab block is malformed")
    return begins[0], ends[0]


def has_managed_cron(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    lines = read_crontab(runner=runner).splitlines()
    return _managed_block_bounds(lines) is not None


def _outside_managed_block(lines: list[str]) -> list[str]:
    bounds = _managed_block_bounds(lines)
    if bounds is None:
        return lines
    start, end = bounds
    return lines[:start] + lines[end + 1 :]


def _has_unmanaged_runner_mcp_entries(lines: list[str]) -> bool:
    for raw in _outside_managed_block(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lowered = line.lower()
        if "runner-mcp" not in lowered:
            continue
        if any(
            token in lowered
            for token in (
                " serve ",
                " github-watcher ",
                " completion-watcher ",
                "ensure-running",
            )
        ):
            return True
    return False


def _cron_command(
    *,
    executable: Path,
    config_dir: Path,
    component: str,
    port: int,
) -> str:
    if component not in CRON_COMPONENTS:
        raise CronAutostartError("unknown cron autostart component")
    argv = [
        str(executable),
        "--config-dir",
        str(config_dir),
        "autostart",
        "cron-run",
        component,
    ]
    if component == "server":
        argv.extend(["--port", str(port)])
    command = " ".join(shlex.quote(item) for item in argv)
    return f"* * * * * {command} >/dev/null 2>&1"


def render_cron_block(
    *,
    executable: Path,
    config_dir: Path,
    components: tuple[str, ...],
    port: int,
) -> list[str]:
    if not 1 <= port <= 65535:
        raise CronAutostartError("autostart port must be between 1 and 65535")
    if len(set(components)) != len(components):
        raise CronAutostartError("duplicate cron autostart component")
    for component in components:
        if component not in CRON_COMPONENTS:
            raise CronAutostartError("unknown cron autostart component")
    return [
        CRON_BEGIN,
        'MAILTO=""',
        *[
            _cron_command(
                executable=executable,
                config_dir=config_dir,
                component=component,
                port=port,
            )
            for component in components
        ],
        CRON_END,
    ]


def install_cron_services(
    *,
    executable: Path,
    config_dir: Path,
    components: tuple[str, ...],
    port: int = 8000,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[str, ...]:
    existing = read_crontab(runner=runner)
    lines = existing.splitlines()
    if _has_unmanaged_runner_mcp_entries(lines):
        raise CronAutostartError(
            "unmanaged Runner MCP cron entries already exist; remove or migrate them first"
        )

    bounds = _managed_block_bounds(lines)
    if bounds is not None:
        start, end = bounds
        lines = lines[:start] + lines[end + 1 :]
    while lines and not lines[-1].strip():
        lines.pop()

    block = render_cron_block(
        executable=executable,
        config_dir=config_dir,
        components=components,
        port=port,
    )
    output_lines = [*lines]
    if output_lines:
        output_lines.append("")
    output_lines.extend(block)
    payload = "\n".join(output_lines) + "\n"
    _run_crontab(["-"], input_text=payload, runner=runner)
    return components


def remove_cron_services(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    existing = read_crontab(runner=runner)
    lines = existing.splitlines()
    bounds = _managed_block_bounds(lines)
    if bounds is None:
        return False
    start, end = bounds
    remaining = lines[:start] + lines[end + 1 :]
    while remaining and not remaining[-1].strip():
        remaining.pop()
    payload = ("\n".join(remaining) + "\n") if remaining else ""
    _run_crontab(["-"], input_text=payload, runner=runner)
    return True


def _safe_lock_path(config_dir: Path, component: str) -> Path:
    if component not in CRON_COMPONENTS:
        raise CronAutostartError("unknown cron autostart component")
    config_dir = config_dir.expanduser().resolve()
    return config_dir / f"autostart-{component}.lock"


def _open_component_lock(config_dir: Path, component: str) -> int:
    path = _safe_lock_path(config_dir, component)
    if path.exists() and path.is_symlink():
        raise CronAutostartError("cron autostart lock path is unsafe")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
        os.fchmod(fd, 0o600)
        return fd
    except OSError as exc:
        raise CronAutostartError("cron autostart lock could not be opened") from exc


def component_active(config_dir: Path, component: str) -> bool:
    fd = _open_component_lock(config_dir, component)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def cron_status(
    *,
    config_dir: Path,
    components: tuple[str, ...],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[CronComponentStatus]:
    lines = read_crontab(runner=runner).splitlines()
    bounds = _managed_block_bounds(lines)
    block = lines[bounds[0] : bounds[1] + 1] if bounds is not None else []
    joined = "\n".join(block)
    results: list[CronComponentStatus] = []
    for component in CRON_COMPONENTS:
        installed = component in components and f" cron-run {component}" in joined
        results.append(
            CronComponentStatus(
                component=component,
                installed=installed,
                enabled=installed,
                active=component_active(config_dir, component) if installed else False,
            )
        )
    return results


def run_cron_component(
    *,
    config_dir: Path,
    executable: Path,
    component: str,
    port: int = 8000,
    exec_fn: Callable[[str, list[str]], object] = os.execv,
) -> int:
    if component not in CRON_COMPONENTS:
        raise CronAutostartError("unknown cron autostart component")
    if not 1 <= port <= 65535:
        raise CronAutostartError("autostart port must be between 1 and 65535")

    fd = _open_component_lock(config_dir, component)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        os.set_inheritable(fd, True)

        argv = [
            str(executable),
            "--config-dir",
            str(config_dir.expanduser().resolve()),
        ]
        if component == "server":
            argv.extend(
                [
                    "serve",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ]
            )
        elif component == "github-watcher":
            argv.extend(["github-watcher", "run"])
        else:
            argv.extend(["completion-watcher", "run"])

        exec_fn(str(executable), argv)
        return 0
    except OSError as exc:
        raise CronAutostartError("cron autostart component could not start") from exc
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
