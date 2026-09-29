from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .onboarding import load_env_file, read_private_runtime
from .operational_safety import OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_CANONICAL_REPOSITORY = "Blacksp1d3r/Runner-Fabric"
_CLONE_URL = "https://github.com/Blacksp1d3r/Runner-Fabric.git"
_GITHUB_TOKEN_ENV = "RUNNER_MCP_GITHUB_TOKEN"
_SCHEMA = "runner-mcp/fabric-bootstrap-job/v1"
_STATE_SCHEMA = "runner-mcp/fabric-bootstrap-state/v1"
_MAX_METADATA_BYTES = 16_384
_TERMINAL = frozenset({"completed", "error", "stopped", "interrupted"})


class FabricBootstrapError(RuntimeError):
    """Bounded Runner Fabric bootstrap failure."""


class FabricBootstrapState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class FabricBootstrapJob:
    job_id: str
    commit: str
    state: FabricBootstrapState
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_category: str | None = None
    already_installed: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "commit": self.commit,
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "error_category": self.error_category,
            "already_installed": self.already_installed,
        }

    def persisted_dict(self) -> dict[str, Any]:
        return {"schemaVersion": _SCHEMA, **self.public_dict()}


class FabricBootstrapManager:
    """Install one exact canonical Runner Fabric commit behind a fixed launcher."""

    def __init__(
        self,
        *,
        config_dir: Path,
        safety: OperatorSafetyGuard,
        runner=subprocess.run,
        data_root: Path | None = None,
    ) -> None:
        if not isinstance(config_dir, Path) or not config_dir.is_absolute():
            raise FabricBootstrapError("Fabric bootstrap config root is invalid")
        try:
            self.config_dir = config_dir.resolve(strict=True)
        except OSError as exc:
            raise FabricBootstrapError("Fabric bootstrap config root is unavailable") from exc
        self.safety = safety
        self._runner = runner
        self.jobs_root = _private_dir(
            self.config_dir / "fabric-bootstrap-jobs",
            create=True,
        )
        self.data_root = _private_dir(
            data_root
            if data_root is not None
            else Path.home() / ".local" / "share" / "runner-fabric",
            create=True,
            parents=True,
        )
        self.releases_root = _private_dir(
            self.data_root / "releases",
            create=True,
        )
        self.state_path = self.config_dir / "fabric-bootstrap-state.json"
        self.current_link = self.data_root / "current"
        self.launcher = (
            self.data_root.parent.parent / "bin" / "runner-fabric"
            if data_root is not None
            else Path.home() / ".local" / "bin" / "runner-fabric"
        )
        self._lock = threading.RLock()
        self._jobs: dict[str, FabricBootstrapJob] = {}
        self._load_existing()

    def runtime_status(self) -> dict[str, Any]:
        return {
            "fabric_bootstrap_installed_commit": self.installed_commit(),
            "fabric_bootstrap_active": any(
                job.state
                in {FabricBootstrapState.QUEUED, FabricBootstrapState.RUNNING}
                for job in self._jobs.values()
            ),
        }

    def installed_commit(self) -> str | None:
        if not self.state_path.exists():
            return None
        raw = _read_private_json(self.state_path)
        expected = {"schemaVersion", "commit"}
        if set(raw) != expected or raw.get("schemaVersion") != _STATE_SCHEMA:
            raise FabricBootstrapError("Fabric bootstrap state is invalid")
        commit = raw.get("commit")
        if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
            raise FabricBootstrapError("Fabric bootstrap state is invalid")
        return commit

    def start(self, commit: str) -> dict[str, Any]:
        if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
            raise FabricBootstrapError(
                "Fabric bootstrap requires a full lowercase commit"
            )
        if self.safety.status().stop_active:
            raise FabricBootstrapError(
                "Fabric bootstrap is blocked by the operator emergency stop"
            )
        with self._lock:
            active = [
                job
                for job in self._jobs.values()
                if job.state
                in {FabricBootstrapState.QUEUED, FabricBootstrapState.RUNNING}
            ]
            if active:
                raise FabricBootstrapError("A Fabric bootstrap job is already active")
            current = self.installed_commit()
            job = FabricBootstrapJob(
                job_id=uuid4().hex,
                commit=commit,
                state=(
                    FabricBootstrapState.COMPLETED
                    if current == commit
                    else FabricBootstrapState.QUEUED
                ),
                created_at=_now(),
                finished_at=_now() if current == commit else None,
                already_installed=current == commit,
            )
            self._persist(job)
            self._jobs[job.job_id] = job
            if current == commit:
                return job.public_dict()

        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id,),
            name=f"runner-mcp-fabric-bootstrap-{job.job_id[:8]}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError as exc:
            self._finish(
                job.job_id,
                state=FabricBootstrapState.ERROR,
                category="worker_start_failed",
            )
            raise FabricBootstrapError("Fabric bootstrap worker could not start") from exc
        return job.public_dict()

    def status(self, job_id: str) -> dict[str, Any]:
        if not isinstance(job_id, str) or _JOB_ID_RE.fullmatch(job_id) is None:
            raise FabricBootstrapError("Invalid Fabric bootstrap job identifier")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise FabricBootstrapError("Unknown Fabric bootstrap job")
            return job.public_dict()

    def _load_existing(self) -> None:
        try:
            entries = tuple(self.jobs_root.iterdir())
        except OSError as exc:
            raise FabricBootstrapError("Fabric bootstrap job storage is unavailable") from exc
        for path in entries:
            if path.suffix != ".json" or _JOB_ID_RE.fullmatch(path.stem) is None:
                raise FabricBootstrapError(
                    "Fabric bootstrap job storage contains an unsafe entry"
                )
            raw = _read_private_json(path)
            try:
                if raw.pop("schemaVersion") != _SCHEMA:
                    raise ValueError
                job = FabricBootstrapJob(
                    job_id=raw["job_id"],
                    commit=raw["commit"],
                    state=FabricBootstrapState(raw["state"]),
                    created_at=_parse_time(raw["created_at"]),
                    started_at=_parse_optional_time(raw["started_at"]),
                    finished_at=_parse_optional_time(raw["finished_at"]),
                    error_category=raw["error_category"],
                    already_installed=raw["already_installed"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise FabricBootstrapError(
                    "Fabric bootstrap job metadata is invalid"
                ) from exc
            if job.job_id != path.stem or _COMMIT_RE.fullmatch(job.commit) is None:
                raise FabricBootstrapError(
                    "Fabric bootstrap job metadata is invalid"
                )
            if job.state in {
                FabricBootstrapState.QUEUED,
                FabricBootstrapState.RUNNING,
            }:
                job = replace(
                    job,
                    state=FabricBootstrapState.INTERRUPTED,
                    finished_at=_now(),
                    error_category="runner_restart",
                )
                self._persist(job)
            self._jobs[job.job_id] = job

    def _persist(self, job: FabricBootstrapJob) -> None:
        payload = (
            json.dumps(
                job.persisted_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if len(payload) > _MAX_METADATA_BYTES:
            raise FabricBootstrapError("Fabric bootstrap job metadata is too large")
        try:
            atomic_replace_private(self.jobs_root / f"{job.job_id}.json", payload)
        except PrivateAtomicWriteError as exc:
            raise FabricBootstrapError(
                "Fabric bootstrap job metadata could not be written"
            ) from exc

    def _update(self, job_id: str, **changes: Any) -> FabricBootstrapJob:
        with self._lock:
            previous = self._jobs[job_id]
            updated = replace(previous, **changes)
            self._persist(updated)
            self._jobs[job_id] = updated
            return updated

    def _finish(
        self,
        job_id: str,
        *,
        state: FabricBootstrapState,
        category: str | None = None,
    ) -> None:
        self._update(
            job_id,
            state=state,
            finished_at=_now(),
            error_category=category,
        )

    def _run_job(self, job_id: str) -> None:
        job = self._update(
            job_id,
            state=FabricBootstrapState.RUNNING,
            started_at=_now(),
        )
        try:
            if self.safety.status().stop_active:
                self._finish(
                    job_id,
                    state=FabricBootstrapState.STOPPED,
                    category="operator_stop",
                )
                return
            self._bootstrap(job)
        except FabricBootstrapError as exc:
            category = _category(exc)
            self._finish(
                job_id,
                state=FabricBootstrapState.ERROR,
                category=category,
            )
        except Exception:  # noqa: BLE001 - background bootstrap must fail closed
            self._finish(
                job_id,
                state=FabricBootstrapState.ERROR,
                category="unexpected_error",
            )
        else:
            self._finish(job_id, state=FabricBootstrapState.COMPLETED)

    def _bootstrap(self, job: FabricBootstrapJob) -> None:
        work = self.jobs_root / f".work-{job.job_id}"
        if work.exists() or work.is_symlink():
            raise FabricBootstrapError("bootstrap_storage_conflict")
        work.mkdir(mode=0o700)
        try:
            source = work / "source"
            wheels = work / "wheels"
            wheels.mkdir(mode=0o700)
            token = self._github_token()
            askpass, token_file = self._write_askpass(work, token)
            git_env = self._base_environment()
            git_env.update(
                {
                    "GIT_ASKPASS": str(askpass),
                    "GIT_TERMINAL_PROMPT": "0",
                }
            )
            self._run(
                [
                    "git",
                    "clone",
                    "--depth=64",
                    "--no-checkout",
                    _CLONE_URL,
                    str(source),
                ],
                cwd=work,
                env=git_env,
                category="source_unavailable",
                timeout=180,
            )
            self._run(
                ["git", "-C", str(source), "fetch", "--depth=1", "origin", job.commit],
                cwd=work,
                env=git_env,
                category="source_unavailable",
                timeout=120,
            )
            self._run(
                ["git", "-C", str(source), "checkout", "--detach", job.commit],
                cwd=work,
                env=self._base_environment(),
                category="source_unavailable",
                timeout=60,
            )
            try:
                token_file.unlink(missing_ok=True)
                askpass.unlink(missing_ok=True)
            except OSError as exc:
                raise FabricBootstrapError("secret_cleanup_failed") from exc
            head = self._run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                cwd=work,
                env=self._base_environment(),
                category="source_invalid",
                timeout=30,
                capture=True,
            ).strip()
            if head != job.commit:
                raise FabricBootstrapError("source_invalid")
            dirty = self._run(
                ["git", "-C", str(source), "status", "--porcelain"],
                cwd=work,
                env=self._base_environment(),
                category="source_invalid",
                timeout=30,
                capture=True,
            )
            if dirty.strip():
                raise FabricBootstrapError("source_invalid")

            build_env = self._base_environment()
            build_env.update(
                {
                    "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                    "PIP_NO_INPUT": "1",
                    "PIP_NO_INDEX": "1",
                    "PYTHONNOUSERSITE": "1",
                }
            )
            self._run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-input",
                    "--disable-pip-version-check",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(wheels),
                    str(source),
                ],
                cwd=source,
                env=build_env,
                category="build_failed",
                timeout=180,
            )
            wheel_files = tuple(wheels.glob("*.whl"))
            if len(wheel_files) != 1 or wheel_files[0].is_symlink():
                raise FabricBootstrapError("build_failed")
            wheel = wheel_files[0].resolve(strict=True)

            release = self.releases_root / job.commit
            if release.exists():
                raise FabricBootstrapError("release_conflict")
            staged = self.releases_root / f".{job.commit}-{job.job_id}.staged"
            if staged.exists() or staged.is_symlink():
                raise FabricBootstrapError("bootstrap_storage_conflict")
            staged.mkdir(mode=0o700)
            site = staged / "site"
            site.mkdir(mode=0o700)
            self._run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-input",
                    "--disable-pip-version-check",
                    "--no-deps",
                    "--no-index",
                    "--target",
                    str(site),
                    str(wheel),
                ],
                cwd=work,
                env=build_env,
                category="install_failed",
                timeout=180,
            )
            self._write_release_launcher(staged)
            verify_env = self._base_environment()
            verify_env["PYTHONPATH"] = str(site)
            self._run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import runner_fabric; "
                        "from runner_fabric.cli import build_parser; "
                        "build_parser(); "
                        "print(runner_fabric.__version__)"
                    ),
                ],
                cwd=work,
                env=verify_env,
                category="verification_failed",
                timeout=30,
            )
            if self.safety.status().stop_active:
                raise FabricBootstrapError("operator_stop")

            os.replace(staged, release)
            self._activate_release(release, job)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _activate_release(self, release: Path, job: FabricBootstrapJob) -> None:
        current_tmp = self.data_root / f".current-{job.job_id}"
        try:
            current_tmp.symlink_to(release)
            os.replace(current_tmp, self.current_link)
        except OSError as exc:
            current_tmp.unlink(missing_ok=True)
            raise FabricBootstrapError("activation_failed") from exc

        bin_dir = self.launcher.parent
        bin_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        launcher_tmp = bin_dir / f".runner-fabric-{job.job_id}"
        try:
            launcher_tmp.symlink_to(self.current_link / "runner-fabric")
            os.replace(launcher_tmp, self.launcher)
        except OSError as exc:
            launcher_tmp.unlink(missing_ok=True)
            raise FabricBootstrapError("activation_failed") from exc

        state = (
            json.dumps(
                {"schemaVersion": _STATE_SCHEMA, "commit": job.commit},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        try:
            atomic_replace_private(self.state_path, state)
        except PrivateAtomicWriteError as exc:
            raise FabricBootstrapError("activation_state_failed") from exc

    def _write_release_launcher(self, staged: Path) -> None:
        launcher = staged / "runner-fabric"
        script = (
            f"#!{sys.executable}\n"
            "from pathlib import Path\n"
            "import sys\n"
            "site = Path(__file__).resolve().parent / 'site'\n"
            "sys.path.insert(0, str(site))\n"
            "from runner_fabric.cli import main\n"
            "raise SystemExit(main())\n"
        )
        try:
            launcher.write_text(script, encoding="utf-8")
            os.chmod(launcher, 0o700)
        except OSError as exc:
            raise FabricBootstrapError("install_failed") from exc

    def _github_token(self) -> str:
        paths, _settings, _registry = read_private_runtime(self.config_dir)
        values = load_env_file(paths.env_file)
        token = values.get(_GITHUB_TOKEN_ENV, "")
        if (
            not isinstance(token, str)
            or not 20 <= len(token) <= 4096
            or not token.isascii()
            or any(ord(char) < 33 or ord(char) == 127 for char in token)
        ):
            raise FabricBootstrapError("source_auth_unavailable")
        return token

    def _write_askpass(self, work: Path, token: str) -> tuple[Path, Path]:
        token_file = work / ".github-token"
        askpass = work / ".git-askpass"
        try:
            token_file.write_text(token, encoding="ascii")
            os.chmod(token_file, 0o600)
            askpass.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  *Username*) printf '%s\\n' 'x-access-token' ;;\n"
                f"  *Password*) cat '{token_file}' ;;\n"
                "  *) exit 1 ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            os.chmod(askpass, 0o700)
        except OSError as exc:
            raise FabricBootstrapError("source_auth_unavailable") from exc
        return askpass, token_file

    @staticmethod
    def _base_environment() -> dict[str, str]:
        return {
            "HOME": str(Path.home()),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }

    def _run(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        category: str,
        timeout: int,
        capture: bool = False,
    ) -> str:
        try:
            completed = self._runner(
                command,
                cwd=str(cwd),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricBootstrapError(category) from exc
        if completed.returncode != 0:
            raise FabricBootstrapError(category)
        if capture:
            return completed.stdout
        return ""


def _private_dir(path: Path, *, create: bool, parents: bool = False) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise FabricBootstrapError("Fabric bootstrap storage is invalid")
    try:
        if create:
            path.mkdir(mode=0o700, parents=parents, exist_ok=True)
            os.chmod(path, 0o700)
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise FabricBootstrapError("Fabric bootstrap storage is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_mode & 0o077:
        raise FabricBootstrapError("Fabric bootstrap storage is unsafe")
    if metadata.st_uid != os.getuid():
        raise FabricBootstrapError("Fabric bootstrap storage ownership is unsafe")
    return resolved


def _read_private_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise FabricBootstrapError("Fabric bootstrap metadata is unsafe")
    try:
        metadata = path.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_uid != os.getuid()
            or metadata.st_size <= 0
            or metadata.st_size > _MAX_METADATA_BYTES
        ):
            raise FabricBootstrapError("Fabric bootstrap metadata is unsafe")
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FabricBootstrapError("Fabric bootstrap metadata is invalid") from exc
    if not isinstance(raw, dict):
        raise FabricBootstrapError("Fabric bootstrap metadata is invalid")
    return raw


def _category(exc: FabricBootstrapError) -> str:
    value = str(exc)
    allowed = {
        "source_auth_unavailable",
        "source_unavailable",
        "source_invalid",
        "build_failed",
        "install_failed",
        "verification_failed",
        "operator_stop",
        "release_conflict",
        "bootstrap_storage_conflict",
        "secret_cleanup_failed",
        "activation_failed",
        "activation_state_failed",
    }
    return value if value in allowed else "bootstrap_failed"


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_time(value: object) -> datetime:
    parsed = _parse_optional_time(value)
    if parsed is None:
        raise ValueError("timestamp is required")
    return parsed


def _parse_optional_time(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp is invalid")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone aware")
    return parsed.astimezone(UTC)
