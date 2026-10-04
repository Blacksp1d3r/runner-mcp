from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .ci_runner_github import CIRunnerGitHubController, CIRunnerGitHubError
from .ci_runner_lifecycle import CIRunnerLifecycleError, CIRunnerSpec

_MAX_PROCESS_OUTPUT_BYTES = 64 * 1024
_CONFIG_TIMEOUT_SECONDS = 120.0
_VERIFY_ATTEMPTS = 5


class CIRunnerEnrollmentError(RuntimeError):
    """Bounded local runner enrollment failure without token/output disclosure."""


@dataclass(frozen=True, slots=True)
class CIRunnerEnrollmentResult:
    state: str
    alias: str
    runner_name: str
    registered: bool
    online: bool
    busy: bool
    custom_labels: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "state": self.state,
            "alias": self.alias,
            "runner_name": self.runner_name,
            "registered": self.registered,
            "online": self.online,
            "busy": self.busy,
            "custom_labels": list(self.custom_labels),
        }


RunProcess = Callable[..., subprocess.CompletedProcess[str]]
UidProvider = Callable[[], int]
Sleep = Callable[[float], None]


class CIRunnerEnrollmentManager:
    def __init__(
        self,
        *,
        github: CIRunnerGitHubController,
        run_process: RunProcess = subprocess.run,
        uid_provider: UidProvider = os.geteuid,
        sleeper: Sleep = time.sleep,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        if not isinstance(github, CIRunnerGitHubController):
            raise TypeError("github must be CIRunnerGitHubController")
        if not callable(run_process):
            raise TypeError("run_process must be callable")
        if not callable(uid_provider):
            raise TypeError("uid_provider must be callable")
        if not callable(sleeper):
            raise TypeError("sleeper must be callable")
        self._github = github
        self._run_process = run_process
        self._uid_provider = uid_provider
        self._sleeper = sleeper
        self._environment = dict(os.environ if environment is None else environment)

    def enroll(self, spec: CIRunnerSpec) -> CIRunnerEnrollmentResult:
        _require_spec(spec)
        if self._uid_provider() == 0:
            raise CIRunnerEnrollmentError("CI runner enrollment refuses root execution")

        config_script = _safe_runner_script(spec.runner_root, "config.sh")
        work_folder = _safe_work_folder(spec)
        marker = spec.runner_root / ".runner"

        remote = self._safe_remote_status(spec)
        if marker.is_file():
            if remote is None:
                raise CIRunnerEnrollmentError(
                    "local CI runner registration is not present on GitHub"
                )
            return _result("already-registered", spec, remote)

        if marker.exists():
            raise CIRunnerEnrollmentError("local CI runner registration marker is unsafe")
        if remote is not None:
            raise CIRunnerEnrollmentError(
                "configured CI runner identity already exists on GitHub"
            )

        _ensure_work_root(spec)
        token = self._registration_token(spec)

        argv = [
            str(config_script),
            "--unattended",
            "--url",
            f"https://github.com/{spec.repository}",
            "--token",
            token,
            "--name",
            spec.runner_name,
            "--labels",
            ",".join(spec.labels),
            "--work",
            work_folder,
            "--disableupdate",
        ]

        try:
            completed = self._run_process(
                argv,
                cwd=str(spec.runner_root),
                env=_child_environment(self._environment),
                capture_output=True,
                text=True,
                timeout=_CONFIG_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CIRunnerEnrollmentError("CI runner enrollment timed out") from exc
        except OSError as exc:
            raise CIRunnerEnrollmentError(
                "CI runner enrollment process is unavailable"
            ) from exc

        if not isinstance(completed, subprocess.CompletedProcess):
            raise CIRunnerEnrollmentError("CI runner enrollment result is invalid")
        if completed.returncode != 0:
            raise CIRunnerEnrollmentError("CI runner enrollment was rejected")
        if not isinstance(completed.stdout, str) or not isinstance(completed.stderr, str):
            raise CIRunnerEnrollmentError("CI runner enrollment result is invalid")
        if (
            len(completed.stdout.encode("utf-8")) > _MAX_PROCESS_OUTPUT_BYTES
            or len(completed.stderr.encode("utf-8")) > _MAX_PROCESS_OUTPUT_BYTES
        ):
            raise CIRunnerEnrollmentError("CI runner enrollment output is oversized")
        if not marker.is_file() or marker.is_symlink():
            raise CIRunnerEnrollmentError(
                "CI runner enrollment did not create a safe registration marker"
            )

        verified = self._wait_for_remote_registration(spec)
        if set(verified.custom_labels) != set(spec.labels):
            raise CIRunnerEnrollmentError(
                "CI runner registration labels did not converge"
            )
        return _result("registered", spec, verified)

    def _registration_token(self, spec: CIRunnerSpec) -> str:
        try:
            token = self._github.create_registration_token(spec)
        except CIRunnerGitHubError as exc:
            raise CIRunnerEnrollmentError(
                "CI runner registration token is unavailable"
            ) from exc
        return token.value

    def _safe_remote_status(self, spec: CIRunnerSpec):
        try:
            return self._github.status(spec)
        except CIRunnerGitHubError as exc:
            raise CIRunnerEnrollmentError(
                "CI runner GitHub status is unavailable"
            ) from exc

    def _wait_for_remote_registration(self, spec: CIRunnerSpec):
        for attempt in range(_VERIFY_ATTEMPTS):
            state = self._safe_remote_status(spec)
            if state is not None:
                return state
            if attempt + 1 < _VERIFY_ATTEMPTS:
                self._sleeper(1.0)
        raise CIRunnerEnrollmentError(
            "CI runner registration did not become visible on GitHub"
        )


def _safe_runner_script(root: Path, name: str) -> Path:
    if root.is_symlink():
        raise CIRunnerEnrollmentError("CI runner root is unsafe")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerEnrollmentError("CI runner root is unavailable") from exc
    if not resolved_root.is_dir():
        raise CIRunnerEnrollmentError("CI runner root is unavailable")

    script = resolved_root / name
    if script.is_symlink() or not script.is_file() or not os.access(script, os.X_OK):
        raise CIRunnerEnrollmentError("CI runner configuration script is unavailable")
    return script


def _safe_work_folder(spec: CIRunnerSpec) -> str:
    try:
        relative = spec.work_root.relative_to(spec.runner_root)
    except ValueError as exc:
        raise CIRunnerEnrollmentError("CI runner work root is unsafe") from exc
    value = relative.as_posix()
    if not value or value.startswith("../") or value == ".":
        raise CIRunnerEnrollmentError("CI runner work folder is unsafe")
    return value


def _ensure_work_root(spec: CIRunnerSpec) -> None:
    if spec.runner_root.is_symlink() or spec.work_root.is_symlink():
        raise CIRunnerEnrollmentError("CI runner work root is unsafe")
    try:
        resolved_root = spec.runner_root.resolve(strict=True)
    except OSError as exc:
        raise CIRunnerEnrollmentError("CI runner root is unavailable") from exc

    if spec.work_root.exists():
        try:
            resolved_work = spec.work_root.resolve(strict=True)
            resolved_work.relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            raise CIRunnerEnrollmentError("CI runner work root is unsafe") from exc
        if not resolved_work.is_dir():
            raise CIRunnerEnrollmentError("CI runner work root is unsafe")
        return

    try:
        spec.work_root.mkdir(mode=0o700, parents=False)
    except OSError as exc:
        raise CIRunnerEnrollmentError(
            "CI runner work root could not be created"
        ) from exc


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


def _result(state: str, spec: CIRunnerSpec, remote) -> CIRunnerEnrollmentResult:
    return CIRunnerEnrollmentResult(
        state=state,
        alias=spec.alias,
        runner_name=spec.runner_name,
        registered=True,
        online=remote.online,
        busy=remote.busy,
        custom_labels=remote.custom_labels,
    )


def _require_spec(spec: CIRunnerSpec) -> None:
    if not isinstance(spec, CIRunnerSpec):
        raise TypeError("spec must be CIRunnerSpec")
    try:
        CIRunnerSpec(
            alias=spec.alias,
            repository=spec.repository,
            runner_name=spec.runner_name,
            runner_root=spec.runner_root,
            work_root=spec.work_root,
            labels=spec.labels,
        )
    except CIRunnerLifecycleError as exc:
        raise CIRunnerEnrollmentError("CI runner spec is invalid") from exc
