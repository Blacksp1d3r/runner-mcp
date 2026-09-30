from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

RUNTIME_SMOKE_IMPORT_ATTEMPTS = 32
RUNTIME_SMOKE_CLI_ATTEMPTS = 8
RUNTIME_SMOKE_TIMEOUT_SECONDS = 10

_IMPORT_PROGRAM = """import importlib
for module_name in (
    "runner_mcp",
    "runner_mcp.cli",
    "mcp",
    "pydantic",
    "starlette",
    "uvicorn",
    "setuptools.build_meta",
):
    importlib.import_module(module_name)
"""


def _run_fixed(
    argv: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[bytes]],
    input_bytes: bytes | None = None,
) -> bool:
    try:
        completed = runner(
            argv,
            input=input_bytes,
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=RUNTIME_SMOKE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def run_autostart_runtime_smoke(
    *,
    python_executable: Path,
    runner_mcp_executable: Path,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> bool:
    """Repeat fixed fresh-process runtime checks before autostart activation."""

    try:
        python = python_executable.expanduser().resolve(strict=True)
        launcher = runner_mcp_executable.expanduser().resolve(strict=True)
    except OSError:
        return False
    if not python.is_file() or not launcher.is_file():
        return False

    import_argv = [str(python), "-B", "-X", "faulthandler", "-"]
    import_program = _IMPORT_PROGRAM.encode("utf-8")
    for _ in range(RUNTIME_SMOKE_IMPORT_ATTEMPTS):
        if not _run_fixed(import_argv, runner=runner, input_bytes=import_program):
            return False

    help_argv = [str(launcher), "--help"]
    for _ in range(RUNTIME_SMOKE_CLI_ATTEMPTS):
        if not _run_fixed(help_argv, runner=runner):
            return False

    return True
