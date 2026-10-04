from __future__ import annotations

import fcntl
import os
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .ci_runner_lifecycle import CIRunnerSpec

_LOCK_NAME = ".runner-mcp-ci.lock"
_RUNNER_MARKER = ".runner"
_RUNNER_SCRIPT = "run.sh"


class CIRunnerSupervisorError(RuntimeError):
    """Bounded CI runner supervisor failure without private path/output disclosure."""


@dataclass(frozen=True, slots=True)
class CIRunnerSupervisorStatus:
    alias: str
    registered: bool
    active: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "registered": self.registered,
            "active": self.active,
        }


RunProcess = Callable[..., subprocess.CompletedProcess[str]]


class CIRunnerSupervisor:
    def __init__(
        self,
        *,
        environment: Mapping[str, str] | None = None,
        runner: RunProcess = subprocess.run,
    ) -> None:
        if not callable(runner):
            raise TypeError("runner must be callable")
        self._environment = dict(os.environ if environment is None else environment)
        self._runner = runner

    def status(self, spec: CIRunnerSpec) -> CIRunnerSupervisorStatus:
        _require_spec(spec)
        root = _safe_root(spec.runner_root)
        registered = _safe_marker(root)
        active = _lock_is_held(root / _LOCK_NAME)
        return CIRunnerSupervisorStatus(
            alias=spec.alias,
            registered=registered,
            active=active,
        )

    def run_once(self, spec: CIRunnerSpec) -> CIRunnerSupervisorStatus:
        _require_spec(spec)
        root = _safe_root(spec.runner_root)
        if not _safe_marker(root):
            raise CIRunnerSupervisorError(
                "CI runner supervisor requires an enrolled runner"
            )
        script = _safe_runner_script(root)
        lock_fd = _open_lock(root / _LOCK_NAME)
        try:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise CIRunnerSupervisorError(
                    "CI runner supervisor is already active"
                ) from exc

            try:
                completed = self._runner(
                    [str(script)],
                    cwd=str(root),
                    env=_child_environment(self._environment),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    shell=False,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise CIRunnerSupervisorError(
                    "CI runner supervisor process failed"
                ) from exc

            if not isinstance(completed, subprocess.CompletedProcess):
                raise CIRunnerSupervisorError(
                    "CI runner supervisor result is invalid"
                )
            if completed.returncode != 0:
                raise CIRunnerSupervisorError(
                    "CI runner process exited unsuccessfully"
                )
        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)

        return self.status(spec)


def _require_spec(spec: CIRunnerSpec) -> None:
    if not isinstance(spec, CIRunnerSpec):
        raise TypeError("spec must be CIRunnerSpec")


def _safe_root(path: Path) -> Path:
    if path.is_symlink():
        raise CIRunnerSupervisorError("CI runner root is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerSupervisorError("CI runner root is unavailable") from exc
    if not resolved.is_dir():
        raise CIRunnerSupervisorError("CI runner root is unavailable")
    return resolved


def _safe_marker(root: Path) -> bool:
    marker = root / _RUNNER_MARKER
    if marker.is_symlink():
        raise CIRunnerSupervisorError("CI runner registration marker is unsafe")
    return marker.is_file()


def _safe_runner_script(root: Path) -> Path:
    script = root / _RUNNER_SCRIPT
    if script.is_symlink():
        raise CIRunnerSupervisorError("CI runner script is unsafe")
    try:
        resolved = script.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerSupervisorError("CI runner script is unavailable") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CIRunnerSupervisorError("CI runner script is unsafe") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise CIRunnerSupervisorError("CI runner script is unavailable")
    return resolved


def _open_lock(path: Path) -> int:
    if path.exists() and path.is_symlink():
        raise CIRunnerSupervisorError("CI runner supervisor lock is unsafe")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
        os.fchmod(fd, 0o600)
        return fd
    except OSError as exc:
        raise CIRunnerSupervisorError(
            "CI runner supervisor lock is unavailable"
        ) from exc


def _lock_is_held(path: Path) -> bool:
    fd = _open_lock(path)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def _child_environment(source: Mapping[str, str]) -> dict[str, str]:
    result = {
        "PATH": source.get("PATH", "/usr/bin:/bin"),
        "LANG": source.get("LANG", "C.UTF-8"),
        "LC_ALL": source.get("LC_ALL", "C.UTF-8"),
    }
    home = source.get("HOME")
    if home:
        result["HOME"] = home
    return result
