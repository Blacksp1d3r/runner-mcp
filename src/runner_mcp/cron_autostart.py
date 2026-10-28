from __future__ import annotations

import fcntl
import os
import shlex
import shutil
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .autostart_activation import AutostartActivationPermit, require_clear_autostart_permit
from .safe_diagnostics import (
    DiagnosticComponent,
    DiagnosticErrorCategory,
    DiagnosticEvent,
    render_safe_diagnostic,
)

CRON_BEGIN = "# BEGIN RUNNER MCP AUTOSTART v1"
CRON_END = "# END RUNNER MCP AUTOSTART v1"
CRON_COMPONENTS = (
    "server",
    "tunnel",
    "topology-heartbeat",
    "github-watcher",
    "completion-watcher",
    "agent-bus-worker",
    "fabric-agent-qualification",
    "fabric-live-overview",
)


class CronAutostartError(RuntimeError):
    """Safe cron-autostart failure without private command output."""


def _diagnose_cron_supervisor(
    diagnostic_sink: Callable[[str], object] | None,
    event: DiagnosticEvent,
    error: DiagnosticErrorCategory | None = None,
) -> None:
    if diagnostic_sink is None:
        return
    diagnostic_sink(
        render_safe_diagnostic(
            component=DiagnosticComponent.CRON_SUPERVISOR,
            event=event,
            error=error,
        )
    )


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


def cron_available() -> bool:
    candidate = shutil.which("crontab")
    if not candidate:
        return False
    try:
        resolved = Path(candidate).resolve(strict=True)
    except OSError:
        return False
    return resolved.is_absolute() and resolved.is_file()


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
    if (
        completed.returncode == 1
        and not completed.stdout
        and "no crontab" in completed.stderr.lower()
    ):
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
        # Parse bounded role tokens, reusing the original role registry.
        # An unmanaged legacy "cron-run server" outside the owner block can
        # start a SECOND serving process; " serve " did not detect it.
        try:
            tokens = shlex.split(line)
        except ValueError:
            # Do not admit a malformed runner-mcp cron command as harmless.
            return True
        if any(
            tokens[index] == "cron-run"
            and tokens[index + 1] in CRON_COMPONENTS
            for index in range(len(tokens) - 1)
        ):
            return True
        if any(
            token in lowered
            for token in (
                " serve ",
                " tunnel-run ",
                " topology-heartbeat ",
                " cron-run tunnel",
                " cron-run topology-heartbeat",
                " github-watcher ",
                " completion-watcher ",
                " agent-bus-worker ",
                " fabric-agent-qualification ",
                " fabric-live-overview ",
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
    if component in {"server", "tunnel"}:
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
    activation_permit: AutostartActivationPermit | None = None,
) -> tuple[str, ...]:
    try:
        require_clear_autostart_permit(activation_permit)
    except PermissionError as exc:
        raise CronAutostartError("autostart activation is blocked") from exc
    # Direct Python callers must not bypass the CLI's duplicate-supervisor
    # guard. Inspect the user's existing managed units without running systemctl.
    from .autostart import AutostartError, has_managed_user_units

    try:
        if has_managed_user_units():
            raise CronAutostartError(
                "managed systemd user services exist; refuse parallel cron activation"
            )
    except AutostartError as exc:
        raise CronAutostartError("managed systemd status is unavailable") from exc

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
    """Open the existing fixed cron lock without modifying a foreign inode.

    This is the component START path, not the read-only status observer.
    O_CREAT is necessary for the owned lock but may encounter an existing
    hardlink or FIFO. Pin the opened fd and validate its actual inode BEFORE
    fchmod or flock; O_NONBLOCK prevents opening a FIFO from hanging.
    """
    path = _safe_lock_path(config_dir, component)
    if not hasattr(os, "O_NOFOLLOW"):
        raise CronAutostartError("safe cron autostart lock opening unavailable")
    flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise CronAutostartError("cron autostart lock could not be opened") from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.geteuid()
            or opened.st_nlink != 1
            or opened.st_mode & 0o077
        ):
            raise CronAutostartError("cron autostart lock path is unsafe")
        os.fchmod(fd, 0o600)
        return fd
    except (OSError, CronAutostartError) as exc:
        os.close(fd)
        raise CronAutostartError("cron autostart lock path is unsafe") from exc


def component_active(config_dir: Path, component: str) -> bool:
    """Observe an existing cron lock without creating or modifying it.

    A short-lived cron task may legitimately have no resident lock between
    scheduled executions; False must not be used as a failed-job receipt.
    This read-only observer is not trusted process/wheel attestation.
    """
    path = _safe_lock_path(config_dir, component)
    if not hasattr(os, "O_NOFOLLOW"):
        raise CronAutostartError("safe cron lock observation is unavailable")
    try:
        fd = os.open(
            path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
        )
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise CronAutostartError("cron lock observation is unavailable") from exc
    try:
        observed = os.fstat(fd)
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_uid != os.geteuid()
            or observed.st_nlink != 1
            or observed.st_mode & 0o077
        ):
            raise CronAutostartError("cron lock observation is unsafe")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        except OSError as exc:
            raise CronAutostartError(
                "cron lock observation is unavailable"
            ) from exc
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def cron_status(
    *,
    config_dir: Path,
    components: tuple[str, ...],
    executable: Path | None = None,
    port: int | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[CronComponentStatus]:
    """Observe this configuration's exact cron launcher without changing cron.

    A matching command structure for another config/release is not proof that
    THIS instance is managed. Callers with the expected release entrypoint
    must supply executable; no imported wheel or live process is attested.
    """
    if port is not None and not 1 <= port <= 65535:
        raise CronAutostartError("autostart port must be between 1 and 65535")
    expected_config = str(config_dir.expanduser().resolve())
    expected_executable = str(executable) if executable is not None else None
    lines = read_crontab(runner=runner).splitlines()
    bounds = _managed_block_bounds(lines)
    # Status must not falsely report one uniquely owned role if another
    # legacy supervisor command outside the managed block can start it too.
    if _has_unmanaged_runner_mcp_entries(lines):
        raise CronAutostartError(
            "unmanaged Runner MCP cron entries already exist"
        )
    block = lines[bounds[0] : bounds[1] + 1] if bounds is not None else []
    # Only exact owner-managed schedule entries count. Comments, suffix
    # aliases (e.g. 'server-old') and a quoted sentence containing cron-run
    # cannot be interpreted as installed role evidence.
    def exact_scheduled_role(line: str, role: str) -> bool:
        if not line.startswith("* * * * * "):
            return False
        try:
            tokens = shlex.split(line)
        except ValueError:
            return False
        if tokens[:5] != ["*"] * 5 or tokens[-2:] != [">/dev/null", "2>&1"]:
            return False
        argv = tokens[5:-2]
        if (
            len(argv) not in (6, 8)
            or not argv[0].startswith("/")
            or not argv[2].startswith("/")
            or argv[1:2] != ["--config-dir"]
            or argv[2] != expected_config
            or (
                expected_executable is not None
                and argv[0] != expected_executable
            )
            or argv[3:6] != ["autostart", "cron-run", role]
        ):
            return False
        if role in {"server", "tunnel"}:
            return (
                len(argv) == 8
                and argv[6] == "--port"
                and argv[7].isascii()
                and argv[7].isdecimal()
                and len(argv[7]) <= 5
                and 1 <= int(argv[7]) <= 65535
                and (port is None or int(argv[7]) == port)
            )
        return len(argv) == 6

    def claimed_role(line: str, role: str) -> bool:
        # Count managed role claims independently of source path, so an
        # old and a new release cannot coexist unnoticed in one block.
        if not line.startswith("* * * * * "):
            return False
        try:
            tokens = shlex.split(line)
        except ValueError:
            return False
        return (
            tokens[:5] == ["*"] * 5
            and len(tokens) >= 11
            and tokens[8:11] == ["autostart", "cron-run", role]
        )

    results: list[CronComponentStatus] = []
    for component in CRON_COMPONENTS:
        claims = [line for line in block if claimed_role(line, component)]
        installed = (
            component in components
            and len(claims) == 1
            and exact_scheduled_role(claims[0], component)
        )
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
    diagnostic_sink: Callable[[str], object] | None = None,
) -> int:
    if component not in CRON_COMPONENTS:
        raise CronAutostartError("unknown cron autostart component")
    if not 1 <= port <= 65535:
        raise CronAutostartError("autostart port must be between 1 and 65535")

    try:
        fd = _open_component_lock(config_dir, component)
    except CronAutostartError:
        _diagnose_cron_supervisor(
            diagnostic_sink,
            DiagnosticEvent.SUPERVISOR_RESTART_FAILED,
            DiagnosticErrorCategory.RESTART_FAILED,
        )
        raise

    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _diagnose_cron_supervisor(
                diagnostic_sink,
                DiagnosticEvent.SUPERVISOR_RESTART_FAILED,
                DiagnosticErrorCategory.SUPERVISOR_LOCKED,
            )
            return 0
        os.set_inheritable(fd, True)

        if component == "tunnel" and not component_active(config_dir, "server"):
            fcntl.flock(fd, fcntl.LOCK_UN)
            return 0

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
        elif component == "tunnel":
            argv.extend(["tunnel-run", "--port", str(port)])
        elif component == "topology-heartbeat":
            argv.extend(["topology-heartbeat", "run"])
        elif component == "github-watcher":
            argv.extend(["github-watcher", "run"])
        elif component == "completion-watcher":
            argv.extend(["completion-watcher", "run"])
        elif component == "agent-bus-worker":
            argv.extend(["agent-bus-worker", "run"])
        elif component == "fabric-agent-qualification":
            argv.extend(["fabric-agent-qualification", "run"])
        else:
            argv.extend(["fabric-live-overview", "run"])

        _diagnose_cron_supervisor(
            diagnostic_sink,
            DiagnosticEvent.SUPERVISOR_RESTART_HANDOFF,
        )
        exec_fn(str(executable), argv)
        return 0
    except OSError as exc:
        _diagnose_cron_supervisor(
            diagnostic_sink,
            DiagnosticEvent.SUPERVISOR_RESTART_FAILED,
            DiagnosticErrorCategory.RESTART_FAILED,
        )
        raise CronAutostartError("cron autostart component could not start") from exc
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
