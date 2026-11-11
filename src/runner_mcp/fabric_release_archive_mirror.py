"""One fixed BACKUP action for the two locally protected Fabric release archives.

No caller-supplied paths, revisions, commands, environment or credentials.
Reuses the exact pinned first-party Fabric custody and mirror CLI already
installed in the owner-managed offline-release-archive/tools directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .fabric_release_archive_mirror_readiness import FabricReleaseArchiveMirrorReadiness
from .operational_safety import ActionClass, OperatorSafetyGuard

_SHA = re.compile(r"^[0-9a-f]{40}$")
_ACTIVE_SCHEMA = "runner.fabric/control-plane-update-transaction/v1"
_RESULT_SCHEMA = "runner-mcp/protected-release-archive-mirror/v1"
_TOOL_DIGESTS = {
    "control_plane_bundle_custody.py": "f00f1f674a2d9ddbb8466b9b93cf5a425bb32508",
    "control_plane_bundle_mirror.py": "612448169e8a5e5fc5234858928c5e3f3bbb9b43",
}
_PRIMARY = "RUNNER_MCP_FABRIC_RELEASE_CUSTODY_ROOT"
_MOUNT = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_MOUNT_ROOT"
_MIRROR = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_ROOT"


class ProtectedReleaseMirrorError(RuntimeError):
    """A bounded non-sensitive refusal code."""


def _checked_tool(directory: Path, filename: str) -> Path:
    path = directory / filename
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_mode & 0o077
            or info.st_size <= 0
            or info.st_size > 65_536
            or path.is_symlink()
        ):
            raise ProtectedReleaseMirrorError("first-party-tool-untrusted")
        with path.open("rb") as stream:
            data = stream.read(65_537)
        blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        if hashlib.sha1(blob).hexdigest() != _TOOL_DIGESTS[filename]:
            raise ProtectedReleaseMirrorError("first-party-tool-untrusted")
    except (OSError, KeyError) as exc:
        raise ProtectedReleaseMirrorError("first-party-tool-unavailable") from exc
    return path


def _protected_pair(home: Path) -> tuple[str, str, bytes]:
    root = home / ".local" / "state" / "runner-fabric" / "control-plane-update"
    file = root / "transaction.json"
    try:
        info = file.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_mode & 0o077
            or not 0 < info.st_size <= 32_768
        ):
            raise ProtectedReleaseMirrorError("protected-transaction-invalid")
        data = file.read_bytes()
        if len(data) != info.st_size:
            raise ProtectedReleaseMirrorError("protected-transaction-invalid")
        value = json.loads(data)
    except (OSError, ValueError, TypeError) as exc:
        raise ProtectedReleaseMirrorError("protected-transaction-invalid") from exc
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != _ACTIVE_SCHEMA
        or value.get("phase") != "active"
    ):
        raise ProtectedReleaseMirrorError("protected-transaction-invalid")
    active = value.get("commitSha")
    before = value.get("previousTarget")
    after = value.get("newTarget")
    if (
        not isinstance(active, str)
        or _SHA.fullmatch(active) is None
        or not isinstance(before, str)
        or not isinstance(after, str)
    ):
        raise ProtectedReleaseMirrorError("protected-transaction-invalid")
    slots = root / "slots"
    suffix = Path("venv/bin/runner-fabric")
    if Path(after) != slots / active / suffix:
        raise ProtectedReleaseMirrorError("protected-transaction-invalid")
    previous_path = Path(before)
    try:
        previous_sha = previous_path.relative_to(slots).parts
    except ValueError as exc:
        raise ProtectedReleaseMirrorError("protected-transaction-invalid") from exc
    if (
        len(previous_sha) != 4
        or _SHA.fullmatch(previous_sha[0]) is None
        or previous_sha[1:] != ("venv", "bin", "runner-fabric")
        or previous_sha[0] == active
    ):
        raise ProtectedReleaseMirrorError("protected-transaction-invalid")
    return (active, previous_sha[0], data)


def _parse_receipt(data: bytes, *, commit: str) -> dict[str, Any]:
    if len(data) > 4096:
        raise ProtectedReleaseMirrorError("first-party-result-invalid")
    try:
        result = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise ProtectedReleaseMirrorError("first-party-result-invalid") from exc
    if (
        not isinstance(result, dict)
        or result.get("status") != "PASS"
        or result.get("commitSha") != commit
    ):
        raise ProtectedReleaseMirrorError("first-party-result-invalid")
    return result


class ProtectedReleaseArchiveMirror:
    """Zero-argument guarded exact active+rollback archive backup."""

    def __init__(
        self,
        *,
        environment: Mapping[str, str],
        safety: OperatorSafetyGuard,
        readiness: FabricReleaseArchiveMirrorReadiness,
        home: Path | None = None,
        runner: Callable[..., Any] = subprocess.run,
    ) -> None:
        self.environment = environment
        self.safety = safety
        self.readiness = readiness
        self.home = (home if home is not None else Path.home()).resolve()
        self.runner = runner

    def _run(self, script: Path, *args: str, commit: str) -> dict[str, Any]:
        command = [
            sys.executable,
            "-B",
            str(script),
            *args,
        ]
        try:
            finished = self.runner(
                command,
                cwd=str(script.parent),
                env={
                    "HOME": str(self.home),
                    "PATH": "/usr/bin:/bin",
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    "PYTHONNOUSERSITE": "1",
                },
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ProtectedReleaseMirrorError("first-party-execution-failed") from exc
        if finished.returncode != 0:
            raise ProtectedReleaseMirrorError("first-party-execution-failed")
        return _parse_receipt(finished.stdout, commit=commit)

    def run(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.BACKUP)
        if self.readiness.status().get("ready") is not True:
            raise ProtectedReleaseMirrorError("independent-storage-not-ready")
        active, previous, original_transaction = _protected_pair(self.home)
        settings = tuple(self.environment.get(key) for key in (_PRIMARY, _MOUNT, _MIRROR))
        if not all(isinstance(v, str) and v.startswith("/") for v in settings):
            raise ProtectedReleaseMirrorError("storage-bindings-unavailable")
        primary, mount, mirror = (Path(v) for v in settings)
        tools = self.home / ".local" / "share" / "runner-fabric" / "offline-release-archive" / "tools"
        custody = _checked_tool(tools, "control_plane_bundle_custody.py")
        mirror_tool = _checked_tool(tools, "control_plane_bundle_mirror.py")
        verified = 0
        newly_stored = 0
        already_stored = 0
        for commit in (active, previous):
            if self.readiness.status().get("ready") is not True:
                raise ProtectedReleaseMirrorError("independent-storage-not-ready")
            if _protected_pair(self.home) != (active, previous, original_transaction):
                raise ProtectedReleaseMirrorError("protected-transaction-changed")
            source = self._run(
                custody, "verify", "--archive-root", str(primary),
                "--commit", commit, commit=commit,
            )
            if source.get("retentionDays", 0) < 365:
                raise ProtectedReleaseMirrorError("archive-retention-insufficient")
            result = self._run(
                mirror_tool, "--primary-root", str(primary),
                "--mount-root", str(mount), "--mirror-root", str(mirror),
                "--commit", commit, commit=commit,
            )
            if result.get("separateDevice") is not True:
                raise ProtectedReleaseMirrorError("mirror-device-not-independent")
            if result.get("alreadyStored") is True:
                already_stored += 1
            elif result.get("alreadyStored") is False:
                newly_stored += 1
            else:
                raise ProtectedReleaseMirrorError("first-party-result-invalid")
            target = self._run(
                custody, "verify", "--archive-root", str(mirror),
                "--commit", commit, commit=commit,
            )
            if (target.get("bytes") != source.get("bytes")
                or target.get("fileCount") != source.get("fileCount")):
                raise ProtectedReleaseMirrorError("mirror-integrity-mismatch")
            verified += 1
        if _protected_pair(self.home) != (active, previous, original_transaction):
            raise ProtectedReleaseMirrorError("protected-transaction-changed")
        return {
            "schemaVersion": _RESULT_SCHEMA,
            "state": "qualified",
            "protectedRevisionCount": 2,
            "mirroredCount": newly_stored,
            "verifiedCount": verified,
            "alreadyStoredCount": already_stored,
            "separateDeviceReady": True,
            "reasonCode": "ready",
            "mutationScope": "protected-release-archive-mirror",
            "restoreTriggered": False,
            "updateTriggered": False,
            "deleteTriggered": False,
        }
