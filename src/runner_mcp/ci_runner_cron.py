from __future__ import annotations

import shlex
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .ci_runner_lifecycle import CIRunnerSpec

CI_CRON_BEGIN = "# BEGIN RUNNER MCP CI RUNNERS v1"
CI_CRON_END = "# END RUNNER MCP CI RUNNERS v1"


class CIRunnerCronError(RuntimeError):
    """Bounded CI runner cron admission failure without private values."""


@dataclass(frozen=True, slots=True)
class CIRunnerCronStatus:
    installed: bool
    aliases: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "installed": self.installed,
            "aliases": list(self.aliases),
        }


def render_ci_runner_cron_block(
    *,
    executable: Path,
    config_dir: Path,
    specs: dict[str, CIRunnerSpec],
) -> list[str]:
    resolved_executable = _safe_executable(executable)
    resolved_config = _safe_config_dir(config_dir)
    aliases = tuple(sorted(specs))
    if not aliases:
        raise CIRunnerCronError("no CI runners are configured")
    if any(specs[alias].alias != alias for alias in aliases):
        raise CIRunnerCronError("CI runner aliases are inconsistent")

    return [
        CI_CRON_BEGIN,
        'MAILTO=""',
        *[
            "* * * * * "
            + " ".join(
                shlex.quote(item)
                for item in (
                    str(resolved_executable),
                    "--config-dir",
                    str(resolved_config),
                    "ci-runner",
                    "run",
                    alias,
                )
            )
            + " >/dev/null 2>&1"
            for alias in aliases
        ],
        CI_CRON_END,
    ]


def install_ci_runner_cron(
    *,
    executable: Path,
    config_dir: Path,
    specs: dict[str, CIRunnerSpec],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CIRunnerCronStatus:
    existing = _read_crontab(runner=runner)
    lines = existing.splitlines()
    _reject_unmanaged_ci_runner_entries(lines)
    bounds = _managed_bounds(lines)
    if bounds is not None:
        start, end = bounds
        lines = lines[:start] + lines[end + 1 :]

    while lines and not lines[-1].strip():
        lines.pop()
    block = render_ci_runner_cron_block(
        executable=executable,
        config_dir=config_dir,
        specs=specs,
    )
    output = [*lines]
    if output:
        output.append("")
    output.extend(block)
    _write_crontab("
".join(output) + "
", runner=runner)
    return CIRunnerCronStatus(
        installed=True,
        aliases=tuple(sorted(specs)),
    )


def remove_ci_runner_cron(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    lines = _read_crontab(runner=runner).splitlines()
    bounds = _managed_bounds(lines)
    if bounds is None:
        return False
    start, end = bounds
    remaining = lines[:start] + lines[end + 1 :]
    while remaining and not remaining[-1].strip():
        remaining.pop()
    payload = ("
".join(remaining) + "
") if remaining else ""
    _write_crontab(payload, runner=runner)
    return True


def ci_runner_cron_status(
    *,
    specs: dict[str, CIRunnerSpec],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CIRunnerCronStatus:
    lines = _read_crontab(runner=runner).splitlines()
    bounds = _managed_bounds(lines)
    return CIRunnerCronStatus(
        installed=bounds is not None,
        aliases=tuple(sorted(specs)) if bounds is not None else (),
    )


def _managed_bounds(lines: list[str]) -> tuple[int, int] | None:
    begins = [index for index, line in enumerate(lines) if line == CI_CRON_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == CI_CRON_END]
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise CIRunnerCronError("managed CI runner cron block is malformed")
    return begins[0], ends[0]


def _reject_unmanaged_ci_runner_entries(lines: list[str]) -> None:
    bounds = _managed_bounds(lines)
    for index, raw in enumerate(lines):
        if bounds is not None and bounds[0] <= index <= bounds[1]:
            continue
        stripped = raw.strip().lower()
        if not stripped or stripped.startswith("#"):
            continue
        if "runner-mcp" in stripped and "ci-runner" in stripped:
            raise CIRunnerCronError(
                "unmanaged CI runner cron entry already exists"
            )


def _crontab_executable() -> str:
    candidate = shutil.which("crontab")
    if not candidate:
        raise CIRunnerCronError("crontab is unavailable")
    resolved = Path(candidate).resolve()
    if not resolved.is_absolute() or not resolved.is_file():
        raise CIRunnerCronError("crontab is unavailable")
    return str(resolved)


def _read_crontab(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> str:
    executable = _crontab_executable()
    completed = runner(
        [executable, "-l"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode == 0:
        return completed.stdout
    if completed.returncode == 1:
        return ""
    raise CIRunnerCronError("crontab could not be read")


def _write_crontab(
    payload: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    executable = _crontab_executable()
    completed = runner(
        [executable, "-"],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise CIRunnerCronError("crontab could not be updated")


def _safe_executable(path: Path) -> Path:
    if path.is_symlink():
        raise CIRunnerCronError("Runner MCP executable is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerCronError("Runner MCP executable is unavailable") from exc
    if not resolved.is_file():
        raise CIRunnerCronError("Runner MCP executable is unavailable")
    return resolved


def _safe_config_dir(path: Path) -> Path:
    if path.is_symlink():
        raise CIRunnerCronError("Runner MCP config directory is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerCronError("Runner MCP config directory is unavailable") from exc
    if not resolved.is_dir():
        raise CIRunnerCronError("Runner MCP config directory is unavailable")
    return resolved
