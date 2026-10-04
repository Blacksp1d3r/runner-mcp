from __future__ import annotations

import hashlib
import io
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .fabric_bootstrap import _private_env_value
from .operational_safety import OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_REPOSITORY = "Blacksp1d3r/Runner-Fabric"
_WORKFLOW = "control-plane-update-bundle.yml"
_TOKEN_ENV = "RUNNER_MCP_GITHUB_TOKEN"
_JOB_SCHEMA = "runner-mcp/fabric-update-job/v1"
_MAX_JSON = 16_384
_MAX_API_RESPONSE = 2 * 1024 * 1024
_MAX_ARCHIVE = 256 * 1024 * 1024
_MAX_UNCOMPRESSED = 256 * 1024 * 1024
_MAX_ENTRY = 64 * 1024 * 1024
_MAX_FILES = 160
_TERMINAL = frozenset({"completed", "error", "interrupted"})


class FabricUpdateError(RuntimeError):
    """Bounded managed Runner Fabric update failure."""


class FabricUpdateState(StrEnum):
    QUEUED = "queued"
    FETCHING = "fetching"
    PREFLIGHT = "preflight"
    APPLYING = "applying"
    COMPLETED = "completed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class FabricUpdateJob:
    job_id: str
    commit: str
    state: FabricUpdateState
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_category: str | None = None
    already_active: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "commit": self.commit,
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "error_category": self.error_category,
            "already_active": self.already_active,
        }

    def persisted_dict(self) -> dict[str, Any]:
        return {"schemaVersion": _JOB_SCHEMA, **self.public_dict()}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FabricUpdateManager:
    def __init__(
        self,
        *,
        config_dir: Path,
        safety: OperatorSafetyGuard,
        self_update_status_provider: Callable[[], dict[str, Any]],
        runner=subprocess.run,
        opener: Any | None = None,
        home: Path | None = None,
    ) -> None:
        if not config_dir.is_absolute():
            raise FabricUpdateError("fabric_update_storage_invalid")
        try:
            self.config_dir = config_dir.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc
        self.safety = safety
        self._self_update_status_provider = self_update_status_provider
        self._runner = runner
        self._opener = opener or urllib.request.build_opener(_NoRedirect())
        self.home = (home or Path.home()).expanduser().resolve()
        self.jobs_root = _private_dir(self.config_dir / "fabric-update-jobs", create=True)
        self.state_root = _private_dir(
            self.home / ".local" / "state" / "runner-fabric" / "control-plane-update",
            create=True,
            parents=True,
        )
        self.bundle = self.state_root / "bundle"
        self.launcher = self.home / ".local" / "bin" / "runner-fabric"
        self.transaction = self.state_root / "transaction.json"
        self._lock = threading.RLock()
        self._jobs: dict[str, FabricUpdateJob] = {}
        self._load_existing()

    def runtime_status(self) -> dict[str, Any]:
        return {
            "fabric_update_active": any(
                job.state.value not in _TERMINAL for job in self._jobs.values()
            ),
        }

    def readiness(self, commit: str) -> dict[str, Any]:
        """Verify the exact canonical Actions run/artifact metadata without mutation."""
        _require_commit(commit)
        self._require_safe_runtime()
        self._assert_managed_launcher()
        token = _private_env_value(self.config_dir / "runner-mcp.env", _TOKEN_ENV)
        self._resolve_exact_artifact(token, commit)
        return {"commit": commit, "artifact_ready": True}

    def start(self, commit: str) -> dict[str, Any]:
        _require_commit(commit)
        self._require_safe_runtime()
        with self._lock:
            active = [j for j in self._jobs.values() if j.state.value not in _TERMINAL]
            if active:
                if len(active) == 1 and active[0].commit == commit:
                    return active[0].public_dict()
                raise FabricUpdateError("fabric_update_active")
            active_commit = self._active_commit()
            if active_commit == commit:
                job = FabricUpdateJob(
                    job_id=uuid4().hex,
                    commit=commit,
                    state=FabricUpdateState.COMPLETED,
                    created_at=_now(),
                    finished_at=_now(),
                    already_active=True,
                )
                self._persist(job)
                self._jobs[job.job_id] = job
                return job.public_dict()
            self._assert_managed_launcher()
            job = FabricUpdateJob(
                job_id=uuid4().hex,
                commit=commit,
                state=FabricUpdateState.QUEUED,
                created_at=_now(),
            )
            self._persist(job)
            self._jobs[job.job_id] = job
        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id,),
            name=f"runner-mcp-fabric-update-{job.job_id[:8]}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError as exc:
            self._finish(job.job_id, FabricUpdateState.ERROR, "worker_start_failed")
            raise FabricUpdateError("worker_start_failed") from exc
        return job.public_dict()

    def status(self, job_id: str) -> dict[str, Any]:
        if not isinstance(job_id, str) or _JOB_ID_RE.fullmatch(job_id) is None:
            raise FabricUpdateError("fabric_update_job_invalid")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise FabricUpdateError("fabric_update_job_unknown")
            return job.public_dict()

    def rollback(self, commit: str) -> dict[str, str]:
        _require_commit(commit)
        self._require_safe_runtime()
        with self._lock:
            if any(job.state.value not in _TERMINAL for job in self._jobs.values()):
                raise FabricUpdateError("fabric_update_active")
            if self._active_commit() != commit:
                raise FabricUpdateError("fabric_update_target_mismatch")
            bootstrap = self._validated_bootstrap(commit)
            self._run_fixed(bootstrap, "rollback", "rollback_failed")
        return {"state": "completed", "commit": commit}

    def _require_safe_runtime(self) -> None:
        if self.safety.status().stop_active:
            raise FabricUpdateError("operator_stop")
        try:
            status = self._self_update_status_provider()
        except Exception as exc:
            raise FabricUpdateError("runner_mcp_state_unavailable") from exc
        for key, category in (
            ("active_update", "runner_mcp_self_update_active"),
            ("restart_pending", "runner_mcp_restart_pending"),
            ("install_recovery_pending", "runner_mcp_install_recovery_pending"),
        ):
            value = status.get(key)
            if not isinstance(value, bool):
                raise FabricUpdateError("runner_mcp_state_unavailable")
            if value:
                raise FabricUpdateError(category)

    def _assert_managed_launcher(self) -> None:
        if not self.launcher.is_symlink():
            raise FabricUpdateError("fabric_launcher_unmanaged")
        try:
            target = self.launcher.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_launcher_unmanaged") from exc
        slots = self.state_root / "slots"
        try:
            slots_root = slots.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_launcher_unmanaged") from exc
        if not target.is_relative_to(slots_root):
            raise FabricUpdateError("fabric_launcher_unmanaged")

    def _active_commit(self) -> str | None:
        if not self.transaction.exists():
            return None
        raw = _read_json(self.transaction, 32 * 1024, "fabric_transaction_invalid")
        if raw.get("schemaVersion") != "runner.fabric/control-plane-update-transaction/v1":
            raise FabricUpdateError("fabric_transaction_invalid")
        if raw.get("phase") != "active":
            raise FabricUpdateError("fabric_recovery_required")
        commit = raw.get("commitSha")
        if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
            raise FabricUpdateError("fabric_transaction_invalid")
        return commit

    def _run_job(self, job_id: str) -> None:
        job = self._update(
            job_id,
            state=FabricUpdateState.FETCHING,
            started_at=_now(),
        )
        try:
            archive = self._fetch_exact_artifact(job.commit)
            staged = self._extract_bundle(archive, job)
            previous = self._activate_bundle(staged, job)
            try:
                bootstrap = self._validated_bootstrap(job.commit)
                self._update(job_id, state=FabricUpdateState.PREFLIGHT)
                self._run_fixed(bootstrap, "preflight", "fabric_preflight_failed")
                if self.safety.status().stop_active:
                    raise FabricUpdateError("operator_stop")
                self._update(job_id, state=FabricUpdateState.APPLYING)
                self._run_fixed(bootstrap, "apply", "fabric_apply_failed")
            except Exception:
                self._restore_bundle(previous)
                raise
            else:
                if previous is not None:
                    shutil.rmtree(previous, ignore_errors=True)
        except FabricUpdateError as exc:
            self._finish(job_id, FabricUpdateState.ERROR, _category(exc))
        except Exception:  # noqa: BLE001 - background update must fail closed
            self._finish(job_id, FabricUpdateState.ERROR, "fabric_update_failed")
        else:
            self._finish(job_id, FabricUpdateState.COMPLETED, None)

    def _fetch_exact_artifact(self, commit: str) -> bytes:
        token = _private_env_value(self.config_dir / "runner-mcp.env", _TOKEN_ENV)
        artifact_id = self._resolve_exact_artifact(token, commit)
        return self._download_artifact(token, artifact_id)

    def _resolve_exact_artifact(self, token: str, commit: str) -> int:
        owner, repo = _REPOSITORY.split("/", 1)
        runs = self._api_json(
            token,
            f"/repos/{owner}/{repo}/actions/workflows/{_WORKFLOW}/runs"
            f"?head_sha={commit}&status=success&per_page=100",
            category="actions_run_unavailable",
        )
        rows = runs.get("workflow_runs") if isinstance(runs, dict) else None
        if not isinstance(rows, list):
            raise FabricUpdateError("actions_run_unavailable")
        exact = [
            row for row in rows
            if isinstance(row, dict)
            and row.get("head_sha") == commit
            and row.get("conclusion") == "success"
            and row.get("head_branch") == "main"
            and row.get("event") in {"push", "workflow_dispatch"}
        ]
        pushed = [row for row in exact if row.get("event") == "push"]
        fallback = [row for row in exact if row.get("event") == "workflow_dispatch"]
        if len(pushed) == 1:
            selected = pushed[0]
        elif len(pushed) > 1 or len(fallback) != 1:
            raise FabricUpdateError("actions_run_unavailable")
        else:
            selected = fallback[0]
        if not isinstance(selected.get("id"), int):
            raise FabricUpdateError("actions_run_unavailable")
        run_id = selected["id"]
        artifacts = self._api_json(
            token,
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page=100",
            category="artifact_metadata_unavailable",
        )
        rows = artifacts.get("artifacts") if isinstance(artifacts, dict) else None
        expected = f"runner-fabric-control-plane-update-{commit}"
        candidates = [
            row for row in (rows or [])
            if isinstance(row, dict)
            and row.get("name") == expected
            and row.get("expired") is False
            and isinstance(row.get("id"), int)
        ]
        if len(candidates) != 1:
            raise FabricUpdateError("artifact_metadata_unavailable")
        return candidates[0]["id"]

    def _api_json(
        self,
        token: str,
        path: str,
        *,
        category: str,
    ) -> dict[str, Any]:
        raw = self._request(
            f"https://api.github.com{path}",
            token=token,
            max_bytes=_MAX_API_RESPONSE,
            category=category,
        )
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FabricUpdateError(category) from exc
        if not isinstance(value, dict):
            raise FabricUpdateError(category)
        return value

    def _download_artifact(self, token: str, artifact_id: int) -> bytes:
        owner, repo = _REPOSITORY.split("/", 1)
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/"
            f"{artifact_id}/zip"
        )
        redirect = self._request_redirect(url, token)
        return self._request(
            redirect,
            token=None,
            max_bytes=_MAX_ARCHIVE,
            category="artifact_download_unavailable",
        )

    def _request_redirect(self, url: str, token: str) -> str:
        request = urllib.request.Request(
            url,
            headers=self._headers(token),
            method="GET",
        )
        try:
            self._opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code not in {301, 302, 303, 307, 308}:
                raise FabricUpdateError("artifact_download_unavailable") from exc
            location = exc.headers.get("Location", "")
        except (OSError, urllib.error.URLError) as exc:
            raise FabricUpdateError("artifact_download_unavailable") from exc
        else:
            raise FabricUpdateError("artifact_download_unavailable")
        parsed = urllib.parse.urlsplit(location)
        hostname = (parsed.hostname or "").lower()
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or hostname == "localhost"
            or hostname.endswith(".local")
        ):
            raise FabricUpdateError("artifact_download_unavailable")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_unspecified
        ):
            raise FabricUpdateError("artifact_download_unavailable")
        return location

    def _request(
        self,
        url: str,
        *,
        token: str | None,
        max_bytes: int,
        category: str,
    ) -> bytes:
        request = urllib.request.Request(
            url,
            headers=self._headers(token),
            method="GET",
        )
        try:
            with self._opener.open(request, timeout=60) as response:
                raw = response.read(max_bytes + 1)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise FabricUpdateError(category) from exc
        if len(raw) > max_bytes:
            raise FabricUpdateError(category)
        return raw

    @staticmethod
    def _headers(token: str | None) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "runner-mcp",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _extract_bundle(self, archive: bytes, job: FabricUpdateJob) -> Path:
        staged = self.state_root / f".bundle-{job.job_id}"
        if staged.exists() or staged.is_symlink():
            raise FabricUpdateError("fabric_bundle_storage_conflict")
        staged.mkdir(mode=0o700)
        try:
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                infos = zf.infolist()
                if not 1 <= len(infos) <= _MAX_FILES:
                    raise FabricUpdateError("fabric_bundle_invalid")
                if sum(info.file_size for info in infos) > _MAX_UNCOMPRESSED:
                    raise FabricUpdateError("fabric_bundle_invalid")
                names: set[str] = set()
                for info in infos:
                    name = info.filename
                    mode = info.external_attr >> 16
                    if (
                        not name
                        or name in names
                        or "/" in name
                        or "\\" in name
                        or info.is_dir()
                        or info.file_size > _MAX_ENTRY
                        or stat.S_ISLNK(mode)
                    ):
                        raise FabricUpdateError("fabric_bundle_invalid")
                    names.add(name)
                    target = staged / name
                    target.write_bytes(zf.read(info))
                    target.chmod(0o600)
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            shutil.rmtree(staged, ignore_errors=True)
            raise FabricUpdateError("fabric_bundle_invalid") from exc
        return staged

    def _activate_bundle(self, staged: Path, job: FabricUpdateJob) -> Path | None:
        previous = self.state_root / f".bundle-previous-{job.job_id}"
        try:
            if self.bundle.exists():
                if self.bundle.is_symlink() or not self.bundle.is_dir():
                    raise FabricUpdateError("fabric_bundle_storage_conflict")
                os.replace(self.bundle, previous)
            os.replace(staged, self.bundle)
        except OSError as exc:
            if previous.exists() and not self.bundle.exists():
                os.replace(previous, self.bundle)
            raise FabricUpdateError("fabric_bundle_storage_conflict") from exc
        return previous if previous.exists() else None

    def _restore_bundle(self, previous: Path | None) -> None:
        try:
            if self.bundle.exists():
                failed = self.state_root / ".bundle-failed"
                shutil.rmtree(failed, ignore_errors=True)
                os.replace(self.bundle, failed)
                shutil.rmtree(failed, ignore_errors=True)
            if previous is not None and previous.exists():
                os.replace(previous, self.bundle)
        except OSError as exc:
            raise FabricUpdateError("fabric_bundle_recovery_failed") from exc

    def _validated_bootstrap(self, commit: str) -> Path:
        manifest = _read_json(
            self.bundle / "BUNDLE.json",
            32 * 1024,
            "fabric_bundle_invalid",
        )
        if (
            manifest.get("schemaVersion")
            != "runner.fabric/control-plane-update-bundle/v1"
            or manifest.get("commitSha") != commit
            or manifest.get("python") != "3.12"
        ):
            raise FabricUpdateError("fabric_bundle_invalid")

        project_wheel = manifest.get("projectWheel")
        wheel_count = manifest.get("wheelCount")
        bootstrap_sha = manifest.get("bootstrapSha256")
        if (
            not isinstance(project_wheel, str)
            or not project_wheel.startswith("runner_fabric-")
            or not project_wheel.endswith(".whl")
            or not isinstance(wheel_count, int)
            or isinstance(wheel_count, bool)
            or not 1 <= wheel_count <= _MAX_FILES
            or not isinstance(bootstrap_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", bootstrap_sha) is None
        ):
            raise FabricUpdateError("fabric_bundle_invalid")

        commit_file = self.bundle / "COMMIT_SHA"
        try:
            if (
                commit_file.is_symlink()
                or commit_file.read_text(encoding="ascii").strip() != commit
            ):
                raise FabricUpdateError("fabric_bundle_invalid")
        except (OSError, UnicodeDecodeError) as exc:
            raise FabricUpdateError("fabric_bundle_invalid") from exc

        sums = _parse_sums(
            _read_regular(
                self.bundle / "SHA256SUMS",
                128 * 1024,
                "fabric_bundle_invalid",
            )
        )
        bootstrap = self.bundle / "BOOTSTRAP.py"
        bootstrap_bytes = _read_regular(
            bootstrap,
            512 * 1024,
            "fabric_bundle_invalid",
        )
        if hashlib.sha256(bootstrap_bytes).hexdigest() != bootstrap_sha:
            raise FabricUpdateError("fabric_bundle_integrity_failed")

        try:
            wheels = sorted(self.bundle.glob("*.whl"))
            actual_entries = {entry.name for entry in self.bundle.iterdir()}
        except OSError as exc:
            raise FabricUpdateError("fabric_bundle_invalid") from exc
        if len(wheels) != wheel_count or project_wheel not in {w.name for w in wheels}:
            raise FabricUpdateError("fabric_bundle_invalid")

        payload_names = {"BOOTSTRAP.py", *(wheel.name for wheel in wheels)}
        expected_entries = payload_names | {
            "BUNDLE.json",
            "COMMIT_SHA",
            "SHA256SUMS",
        }
        if actual_entries != expected_entries or set(sums) != payload_names:
            raise FabricUpdateError("fabric_bundle_invalid")

        payloads = {"BOOTSTRAP.py": bootstrap_bytes}
        for wheel in wheels:
            payloads[wheel.name] = _read_regular(
                wheel,
                _MAX_ENTRY,
                "fabric_bundle_invalid",
            )
        for name, payload in payloads.items():
            if hashlib.sha256(payload).hexdigest() != sums[name]:
                raise FabricUpdateError("fabric_bundle_integrity_failed")
        return bootstrap

    def _run_fixed(self, bootstrap: Path, action: str, category: str) -> None:
        if action not in {"preflight", "apply", "rollback"}:
            raise FabricUpdateError("fabric_update_action_invalid")
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONNOUSERSITE": "1",
        }
        try:
            completed = self._runner(
                [sys.executable, str(bootstrap), action],
                cwd=str(self.state_root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricUpdateError(category) from exc
        if completed.returncode != 0:
            raise FabricUpdateError(category)

    def _persist(self, job: FabricUpdateJob) -> None:
        raw = (
            json.dumps(job.persisted_dict(), sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        if len(raw) > _MAX_JSON:
            raise FabricUpdateError("fabric_update_job_invalid")
        try:
            atomic_replace_private(self.jobs_root / f"{job.job_id}.json", raw)
        except PrivateAtomicWriteError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc

    def _update(self, job_id: str, **changes: Any) -> FabricUpdateJob:
        with self._lock:
            job = replace(self._jobs[job_id], **changes)
            self._persist(job)
            self._jobs[job_id] = job
            return job

    def _finish(
        self,
        job_id: str,
        state: FabricUpdateState,
        category: str | None,
    ) -> None:
        self._update(
            job_id,
            state=state,
            finished_at=_now(),
            error_category=category,
        )

    def _load_existing(self) -> None:
        try:
            entries = tuple(self.jobs_root.iterdir())
        except OSError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc
        for path in entries:
            if path.suffix != ".json" or _JOB_ID_RE.fullmatch(path.stem) is None:
                raise FabricUpdateError("fabric_update_storage_invalid")
            raw = _read_json(path, _MAX_JSON, "fabric_update_job_invalid")
            try:
                if raw.pop("schemaVersion") != _JOB_SCHEMA:
                    raise ValueError
                job = FabricUpdateJob(
                    job_id=raw["job_id"],
                    commit=raw["commit"],
                    state=FabricUpdateState(raw["state"]),
                    created_at=_parse(raw["created_at"]),
                    started_at=_parse_optional(raw["started_at"]),
                    finished_at=_parse_optional(raw["finished_at"]),
                    error_category=raw["error_category"],
                    already_active=raw["already_active"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise FabricUpdateError("fabric_update_job_invalid") from exc
            if job.job_id != path.stem or _COMMIT_RE.fullmatch(job.commit) is None:
                raise FabricUpdateError("fabric_update_job_invalid")
            if job.state.value not in _TERMINAL:
                job = replace(
                    job,
                    state=FabricUpdateState.INTERRUPTED,
                    finished_at=_now(),
                    error_category="runner_restart",
                )
                self._persist(job)
            self._jobs[job.job_id] = job


def _require_commit(commit: str) -> None:
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        raise FabricUpdateError("fabric_update_commit_invalid")


def _private_dir(path: Path, *, create: bool, parents: bool = False) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise FabricUpdateError("fabric_update_storage_invalid")
    try:
        if create:
            path.mkdir(mode=0o700, parents=parents, exist_ok=True)
            os.chmod(path, 0o700)
        resolved = path.resolve(strict=True)
        info = resolved.stat()
    except OSError as exc:
        raise FabricUpdateError("fabric_update_storage_invalid") from exc
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise FabricUpdateError("fabric_update_storage_invalid")
    return resolved


def _read_json(path: Path, max_bytes: int, category: str) -> dict[str, Any]:
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_size <= 0
            or info.st_size > max_bytes
        ):
            raise FabricUpdateError(category)
        raw = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FabricUpdateError(category) from exc
    if not isinstance(raw, dict):
        raise FabricUpdateError(category)
    return raw



def _read_regular(path: Path, max_bytes: int, category: str) -> bytes:
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_size <= 0
            or info.st_size > max_bytes
        ):
            raise FabricUpdateError(category)
        raw = path.read_bytes()
    except OSError as exc:
        raise FabricUpdateError(category) from exc
    if len(raw) > max_bytes:
        raise FabricUpdateError(category)
    return raw


def _parse_sums(raw: bytes) -> dict[str, str]:
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise FabricUpdateError("fabric_bundle_invalid") from exc
    rows: dict[str, str] = {}
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise FabricUpdateError("fabric_bundle_invalid")
        digest, name = parts
        if (
            re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not name
            or name in rows
            or "/" in name
            or "\\" in name
        ):
            raise FabricUpdateError("fabric_bundle_invalid")
        rows[name] = digest
    if not rows:
        raise FabricUpdateError("fabric_bundle_invalid")
    return rows

def _category(exc: FabricUpdateError) -> str:
    value = str(exc)
    allowed = {
        "operator_stop",
        "runner_mcp_state_unavailable",
        "runner_mcp_self_update_active",
        "runner_mcp_restart_pending",
        "runner_mcp_install_recovery_pending",
        "fabric_launcher_unmanaged",
        "fabric_recovery_required",
        "fabric_transaction_invalid",
        "fabric_artifact_unavailable",
        "actions_run_unavailable",
        "artifact_metadata_unavailable",
        "artifact_download_unavailable",
        "fabric_bundle_invalid",
        "fabric_bundle_integrity_failed",
        "fabric_bundle_storage_conflict",
        "fabric_bundle_recovery_failed",
        "fabric_preflight_failed",
        "fabric_apply_failed",
        "rollback_failed",
        "fabric_update_failed",
    }
    return value if value in allowed else "fabric_update_failed"


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse(value: object) -> datetime:
    parsed = _parse_optional(value)
    if parsed is None:
        raise ValueError
    return parsed


def _parse_optional(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError
    return parsed.astimezone(UTC)
