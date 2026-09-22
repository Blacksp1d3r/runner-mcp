from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_WHEEL_LABELS = {"baseline", "target"}


class PackageInstallError(RuntimeError):
    """Safe package-install failure without private path or process output."""


class SelfUpdatePackageInstaller:
    """Stage fixed local wheels and track fail-closed in-place installation."""

    def __init__(
        self,
        *,
        config_dir: Path,
        python_executable: Path,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        executable = python_executable
        try:
            resolved_executable = executable.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError("Runner MCP Python runtime is unavailable") from exc
        if (
            not executable.is_absolute()
            or not resolved_executable.is_file()
            or not os.access(resolved_executable, os.X_OK)
        ):
            raise PackageInstallError("Runner MCP Python runtime is unavailable")
        self.python_executable = executable
        self._runner = runner

        root = config_dir / "self-update-install-artifacts"
        if root.is_symlink():
            raise PackageInstallError("Self-update install artifact storage is unsafe")
        try:
            root.mkdir(parents=True, exist_ok=True)
            if not root.is_dir():
                raise PackageInstallError(
                    "Self-update install artifact storage is unsafe"
                )
            os.chmod(root, 0o700)
            self.artifacts_root = root.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError(
                "Self-update install artifact storage is unavailable"
            ) from exc

        self.transaction_path = config_dir / "self-update-install-transaction.json"

    @staticmethod
    def _environment() -> dict[str, str]:
        environment = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PIP_NO_INPUT": "1",
            "PYTHONNOUSERSITE": "1",
        }
        home = os.environ.get("HOME", "").strip()
        if home and Path(home).is_absolute():
            environment["HOME"] = home
        return environment

    def _job_root(self, job_id: str) -> Path:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise PackageInstallError("Invalid self-update install job identifier")
        return self.artifacts_root / job_id

    def build_wheel(self, *, source_root: Path, job_id: str, label: str) -> Path:
        if label not in _WHEEL_LABELS:
            raise PackageInstallError("Invalid self-update wheel stage")
        if source_root.is_symlink():
            raise PackageInstallError("Self-update source is unsafe")
        try:
            source = source_root.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError("Self-update source is unavailable") from exc
        if not source.is_dir():
            raise PackageInstallError("Self-update source is unsafe")

        job_root = self._job_root(job_id)
        if job_root.is_symlink():
            raise PackageInstallError("Self-update install artifact storage is unsafe")
        try:
            job_root.mkdir(mode=0o700, parents=False, exist_ok=True)
            if not job_root.is_dir():
                raise PackageInstallError(
                    "Self-update install artifact storage is unsafe"
                )
            os.chmod(job_root, 0o700)
        except OSError as exc:
            raise PackageInstallError(
                "Self-update install artifact storage is unavailable"
            ) from exc

        destination = job_root / label
        if destination.is_symlink() or destination.exists():
            raise PackageInstallError("Self-update wheel stage already exists")
        try:
            destination.mkdir(mode=0o700)
        except OSError as exc:
            raise PackageInstallError("Self-update wheel stage is unavailable") from exc

        command = [
            str(self.python_executable),
            "-m",
            "pip",
            "wheel",
            "--no-input",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(destination),
            str(source),
        ]
        try:
            completed = self._runner(
                command,
                cwd=str(source),
                env=self._environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PackageInstallError("Runner MCP wheel staging failed") from exc
        if completed.returncode != 0:
            raise PackageInstallError("Runner MCP wheel staging failed")

        try:
            wheels = [
                candidate
                for candidate in destination.iterdir()
                if candidate.suffix == ".whl"
            ]
        except OSError as exc:
            raise PackageInstallError("Runner MCP wheel stage is unavailable") from exc
        if len(wheels) != 1:
            raise PackageInstallError("Runner MCP wheel staging produced invalid output")
        wheel = wheels[0]
        if wheel.is_symlink() or not wheel.is_file():
            raise PackageInstallError("Runner MCP wheel staging produced unsafe output")
        try:
            os.chmod(wheel, 0o600)
            resolved = wheel.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError("Runner MCP wheel staging produced unsafe output") from exc
        if not resolved.is_relative_to(self.artifacts_root):
            raise PackageInstallError("Runner MCP wheel staging produced unsafe output")
        return resolved

    def staged_wheel(self, *, job_id: str, label: str) -> Path:
        if label not in _WHEEL_LABELS:
            raise PackageInstallError("Invalid self-update wheel stage")
        job_root = self._job_root(job_id)
        if job_root.is_symlink():
            raise PackageInstallError("Self-update install artifact storage is unsafe")
        destination = job_root / label
        if destination.is_symlink():
            raise PackageInstallError("Self-update wheel stage is unsafe")
        if not destination.exists() or not destination.is_dir():
            raise PackageInstallError("Self-update wheel stage is unavailable")
        try:
            wheels = [
                candidate
                for candidate in destination.iterdir()
                if candidate.suffix == ".whl"
            ]
        except OSError as exc:
            raise PackageInstallError("Self-update wheel stage is unavailable") from exc
        if len(wheels) != 1:
            raise PackageInstallError("Self-update wheel stage is invalid")
        wheel = wheels[0]
        if wheel.is_symlink() or not wheel.is_file():
            raise PackageInstallError("Self-update wheel stage is unsafe")
        try:
            resolved = wheel.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError("Self-update wheel stage is unavailable") from exc
        if not resolved.is_relative_to(self.artifacts_root):
            raise PackageInstallError("Self-update wheel stage is unsafe")
        return resolved

    def install_wheel(self, wheel: Path) -> None:
        if wheel.is_symlink():
            raise PackageInstallError("Self-update wheel is unsafe")
        try:
            resolved = wheel.resolve(strict=True)
        except OSError as exc:
            raise PackageInstallError("Self-update wheel is unavailable") from exc
        if not resolved.is_file() or not resolved.is_relative_to(self.artifacts_root):
            raise PackageInstallError("Self-update wheel is unsafe")

        command = [
            str(self.python_executable),
            "-m",
            "pip",
            "install",
            "--no-input",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            str(resolved),
        ]
        try:
            completed = self._runner(
                command,
                cwd=str(self.artifacts_root),
                env=self._environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PackageInstallError("Runner MCP package installation failed") from exc
        if completed.returncode != 0:
            raise PackageInstallError("Runner MCP package installation failed")

    def verify_runtime(self) -> None:
        command = [
            str(self.python_executable),
            "-c",
            "import runner_mcp; import runner_mcp.self_update",
        ]
        try:
            completed = self._runner(
                command,
                cwd=str(self.artifacts_root),
                env=self._environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PackageInstallError("Runner MCP installed runtime verification failed") from exc
        if completed.returncode != 0:
            raise PackageInstallError("Runner MCP installed runtime verification failed")

    def pending_transaction(self) -> dict[str, Any] | None:
        path = self.transaction_path
        if path.is_symlink():
            raise PackageInstallError("Self-update install transaction is unsafe")
        if not path.exists():
            return None
        if not path.is_file():
            raise PackageInstallError("Self-update install transaction is unsafe")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PackageInstallError("Self-update install transaction is invalid") from exc
        if not isinstance(raw, dict) or set(raw) != {
            "job_id",
            "target_commit",
            "baseline_commit",
            "rollback_capable",
        }:
            raise PackageInstallError("Self-update install transaction is invalid")
        job_id = raw.get("job_id")
        target_commit = raw.get("target_commit")
        baseline_commit = raw.get("baseline_commit")
        rollback_capable = raw.get("rollback_capable")
        if not isinstance(job_id, str) or not _JOB_ID_RE.fullmatch(job_id):
            raise PackageInstallError("Self-update install transaction is invalid")
        if not isinstance(target_commit, str) or not _COMMIT_RE.fullmatch(target_commit):
            raise PackageInstallError("Self-update install transaction is invalid")
        if baseline_commit is not None and (
            not isinstance(baseline_commit, str)
            or not _COMMIT_RE.fullmatch(baseline_commit)
        ):
            raise PackageInstallError("Self-update install transaction is invalid")
        if not isinstance(rollback_capable, bool):
            raise PackageInstallError("Self-update install transaction is invalid")
        if rollback_capable != (baseline_commit is not None):
            raise PackageInstallError("Self-update install transaction is invalid")
        return raw

    def begin_transaction(
        self,
        *,
        job_id: str,
        target_commit: str,
        baseline_commit: str | None,
    ) -> None:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise PackageInstallError("Invalid self-update install job identifier")
        if not _COMMIT_RE.fullmatch(target_commit):
            raise PackageInstallError("Invalid self-update target commit")
        if baseline_commit is not None and not _COMMIT_RE.fullmatch(baseline_commit):
            raise PackageInstallError("Invalid self-update baseline commit")
        if self.pending_transaction() is not None:
            raise PackageInstallError("Self-update install recovery is already pending")

        temporary = self.transaction_path.with_suffix(".tmp")
        if temporary.is_symlink() or temporary.exists():
            raise PackageInstallError("Self-update install transaction staging is unsafe")
        payload = {
            "job_id": job_id,
            "target_commit": target_commit,
            "baseline_commit": baseline_commit,
            "rollback_capable": baseline_commit is not None,
        }
        try:
            with temporary.open("x", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(payload, sort_keys=True, separators=(",", ":"))
                )
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.transaction_path)
            os.chmod(self.transaction_path, 0o600)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise PackageInstallError(
                "Self-update install transaction could not be persisted"
            ) from exc

    def clear_transaction(self) -> None:
        path = self.transaction_path
        if path.is_symlink():
            raise PackageInstallError("Self-update install transaction is unsafe")
        if not path.exists():
            return
        if not path.is_file():
            raise PackageInstallError("Self-update install transaction is unsafe")
        try:
            path.unlink()
        except OSError as exc:
            raise PackageInstallError(
                "Self-update install transaction could not be cleared"
            ) from exc

    def cleanup_job(self, job_id: str) -> None:
        root = self._job_root(job_id)
        if root.is_symlink():
            raise PackageInstallError("Self-update install artifact storage is unsafe")
        if not root.exists():
            return
        if not root.is_dir():
            raise PackageInstallError("Self-update install artifact storage is unsafe")
        try:
            shutil.rmtree(root)
        except OSError as exc:
            raise PackageInstallError(
                "Self-update install artifacts could not be cleaned"
            ) from exc
