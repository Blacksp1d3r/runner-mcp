"""Fixed local-identity coding workspace allocation; never a remote mkdir transport.

The authenticated MCP caller selects a known worker alias and an opaque task ID,
NOT a host, operating-system user, filesystem path, command or environment.
A private operator-owned binding names one *already existing* workspace root.
The process must run as that root's non-root OS owner. Cross-host delivery is a
separate Fabric/Agent Bus qualification and is never inferred here.
"""

from __future__ import annotations

import os
import pwd
import re
import stat
from collections.abc import Mapping
from contextlib import ExitStack
from pathlib import Path

_SCHEMA = "runner-mcp/coding-workspace/v1"
_WORKERS = frozenset({"claude", "qwen"})
_TASK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$", re.ASCII)
_PREFIX = "RUNNER_MCP_CODING_WORKSPACE_"
_KEYS = ("WORKER", "OWNER", "ROOT")
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_MAX_TASKS = 128


class WorkspaceDenied(RuntimeError):
    """One sanitized failure classification (no raw OS exceptions)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _reply(state: str, reason: str, worker: str | None = None,
           task: str | None = None) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA,
        "state": state,
        "reason_code": reason,
        "worker_id": worker if worker in _WORKERS else None,
        "work_unit_id": task if isinstance(task, str) and _TASK.fullmatch(task) else None,
        "filesystem_path_exposed": False,
        "cross_host_execution_authorized": False,
    }


class CodingWorkspaceProvisioner:
    """Directory-only capability scoped to exactly one private local owner."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._settings = tuple(values.get(_PREFIX + key, "") for key in _KEYS)

    def _binding(self, worker_id: str) -> tuple[int, Path]:
        if not all(self._settings):
            if any(self._settings):
                raise WorkspaceDenied("private_binding_incomplete")
            raise WorkspaceDenied("private_binding_unavailable")
        worker, owner, directory = self._settings
        if worker not in _WORKERS or worker_id != worker:
            raise WorkspaceDenied("worker_binding_mismatch")
        if type(owner) is not str or not owner or "/" in owner:
            raise WorkspaceDenied("owner_binding_invalid")
        try:
            uid = pwd.getpwnam(owner).pw_uid
        except (KeyError, OSError):
            raise WorkspaceDenied("owner_identity_unavailable") from None
        if uid == 0 or os.geteuid() != uid:
            raise WorkspaceDenied("local_owner_mismatch")
        if type(directory) is not str or len(directory) > 1024:
            raise WorkspaceDenied("workspace_root_invalid")
        root = Path(directory)
        if (not root.is_absolute() or root == Path("/")
                or any(part in {".", ".."} for part in root.parts)):
            raise WorkspaceDenied("workspace_root_invalid")
        return uid, root

    @staticmethod
    def _open_directory(stack: ExitStack, name: str, parent: int,
                        uid: int, *, private: bool) -> int:
        try:
            fd = os.open(name, _DIR_FLAGS, dir_fd=parent)
        except (OSError, ValueError):
            raise WorkspaceDenied("workspace_directory_unsafe") from None
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):
            raise WorkspaceDenied("workspace_directory_unsafe")
        if private:
            if info.st_uid != uid or info.st_mode & 0o077:
                raise WorkspaceDenied("workspace_directory_unsafe")
        elif info.st_mode & 0o022:
            # Existing public sticky parents such as /tmp are safe to traverse
            # through no-follow directory descriptors; ordinary writable
            # ancestors could be swapped by another account.
            if not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX):
                raise WorkspaceDenied("workspace_directory_unsafe")
        return fd

    def _root(self, stack: ExitStack, uid: int, root: Path) -> int:
        fd = os.open("/", _DIR_FLAGS)
        stack.callback(os.close, fd)
        parts = root.parts[1:]
        for index, part in enumerate(parts):
            fd = self._open_directory(
                stack, part, fd, uid, private=index == len(parts) - 1,
            )
        return fd

    @staticmethod
    def _entry(parent: int, name: str, uid: int) -> bool:
        try:
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError:
            raise WorkspaceDenied("workspace_entry_unsafe") from None
        if (not stat.S_ISDIR(info.st_mode)
                or info.st_uid != uid or info.st_mode & 0o077):
            raise WorkspaceDenied("workspace_entry_unsafe")
        return True

    def _checked_layout(self, stack: ExitStack, uid: int, root: Path) -> tuple[int, int]:
        fd = self._root(stack, uid, root)
        jobfd = self._open_directory(stack, "jobs", fd, uid, private=True)
        patchfd = self._open_directory(stack, "patches", fd, uid, private=True)
        return jobfd, patchfd

    def preflight(self, worker_id: str) -> dict[str, object]:
        try:
            uid, root = self._binding(worker_id)
            with ExitStack() as stack:
                self._checked_layout(stack, uid, root)
        except WorkspaceDenied as exc:
            return _reply("unavailable", exc.reason, worker_id)
        except OSError:
            return _reply("unavailable", "workspace_storage_unavailable", worker_id)
        return _reply("ready", "ready", worker_id)

    def prepare(self, worker_id: str, work_unit_id: str) -> dict[str, object]:
        if type(work_unit_id) is not str or _TASK.fullmatch(work_unit_id) is None:
            return _reply("blocked", "work_unit_id_invalid", worker_id)
        try:
            uid, root = self._binding(worker_id)
            with ExitStack() as stack:
                jobs, patches = self._checked_layout(stack, uid, root)
                job_exists = self._entry(jobs, work_unit_id, uid)
                patch_exists = self._entry(patches, work_unit_id, uid)
                if job_exists != patch_exists:
                    raise WorkspaceDenied("workspace_partial_existing")
                if job_exists:
                    return _reply("already_prepared", "already_prepared", worker_id, work_unit_id)
                if len(os.listdir(jobs)) >= _MAX_TASKS or len(os.listdir(patches)) >= _MAX_TASKS:
                    raise WorkspaceDenied("workspace_capacity_reached")
                created: list[int] = []
                try:
                    for fd in (jobs, patches):
                        os.mkdir(work_unit_id, mode=0o700, dir_fd=fd)
                        created.append(fd)
                        if not self._entry(fd, work_unit_id, uid):
                            raise WorkspaceDenied("workspace_entry_unsafe")
                        os.fsync(fd)
                except (OSError, WorkspaceDenied):
                    for fd in reversed(created):
                        try:
                            os.rmdir(work_unit_id, dir_fd=fd)
                            os.fsync(fd)
                        except OSError:
                            # Never declare an uncertain partial creation safe.
                            return _reply("blocked", "workspace_recovery_required", worker_id,
                                          work_unit_id)
                    raise WorkspaceDenied("workspace_create_failed") from None
                return _reply("prepared", "prepared", worker_id, work_unit_id)
        except WorkspaceDenied as exc:
            return _reply("unavailable", exc.reason, worker_id, work_unit_id)
        except OSError:
            return _reply("unavailable", "workspace_storage_unavailable", worker_id, work_unit_id)
