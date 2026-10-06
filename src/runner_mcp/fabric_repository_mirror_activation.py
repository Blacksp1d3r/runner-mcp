from __future__ import annotations

import base64
import json
import os
import shlex
import stat
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_STORAGE_NAMESPACE = Path("/srv/runner-data/runner-fabric/f34")
_INVENTORY_ROOT = _STORAGE_NAMESPACE / "inventory"
_MIRROR_ROOT = _STORAGE_NAMESPACE / "mirrors"
_CONFIG_SUBDIR = "repository-mirrors"
_DESIRED_NAME = "managed-repositories.v1.json"
_GIT_CONFIG_NAME = "gitconfig"
_ENV_FILE_NAME = "runner-mcp.env"

_ENV_BINDINGS = {
    "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT": _INVENTORY_ROOT,
    "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT": _MIRROR_ROOT,
}

_DESIRED_STATE = {
    "schemaVersion": "runner.fabric/managed-repositories/v1",
    "repositories": [
        {
            "provider": "github",
            "repository": repository,
            "defaultBranch": "main",
            "backupPolicy": "source.standard",
            "restorePolicy": "source.standard",
        }
        for repository in (
            "Blacksp1d3r/AIfordable",
            "Blacksp1d3r/EnerCue",
            "Blacksp1d3r/Fiscero",
            "Blacksp1d3r/PastEntrance",
            "Blacksp1d3r/PatrimAI",
            "Blacksp1d3r/Runner-Fabric",
            "Blacksp1d3r/UnifiedESG",
            "Blacksp1d3r/bewind",
            "Blacksp1d3r/rasff-lens",
            "Blacksp1d3r/runner-mcp",
            "Blacksp1d3r/safety",
        )
    ],
}


class FabricRepositoryMirrorActivationError(RuntimeError):
    """Sanitized bounded activation failure."""


class FabricRepositoryMirrorActivator:
    """Activate only the fixed F34 mirror bindings after host storage delegation."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: MutableMapping[str, str],
        config_dir: Path,
        github_token: str | None,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
        self.github_token = github_token

    def activate(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.BACKUP)
        _require_private_dir(self.config_dir, require_writable=True)
        _require_private_dir(_INVENTORY_ROOT, require_writable=True)
        _require_private_dir(_MIRROR_ROOT, require_writable=True)

        token = _validated_token(self.github_token)
        private_dir = self.config_dir / _CONFIG_SUBDIR
        _ensure_private_child_dir(private_dir, self.config_dir)

        desired_file = private_dir / _DESIRED_NAME
        git_config = private_dir / _GIT_CONFIG_NAME
        env_file = self.config_dir / _ENV_FILE_NAME

        desired_content = (
            json.dumps(
                _DESIRED_STATE,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            + "\n"
        )
        _write_private_exact(desired_file, desired_content)

        encoded = base64.b64encode(
            f"x-access-token:{token}".encode()
        ).decode("ascii")
        git_config_content = (
            '[http "https://github.com/"]\n'
            f"\textraHeader = AUTHORIZATION: basic {encoded}\n"
        )
        _write_private_exact(git_config, git_config_content)

        bindings = {
            **{key: str(path) for key, path in _ENV_BINDINGS.items()},
            "RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE": str(desired_file),
            "RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG": str(git_config),
        }
        _merge_private_env(env_file, bindings)
        self.environment.update(bindings)

        for path in (_INVENTORY_ROOT, _MIRROR_ROOT):
            _require_private_dir(path, require_writable=True)
        for path in (desired_file, git_config, env_file):
            _require_private_file(path)

        return {
            "schemaVersion": "runner-mcp/fabric-repository-mirror-activation/v1",
            "activated": True,
            "storageReady": True,
            "desiredStateBound": True,
            "credentialBindingPresent": True,
            "serviceBindingReady": all(
                self.environment.get(key) == value
                for key, value in bindings.items()
            ),
            "mutationScope": "repository-mirror-activation",
            "reconcileTriggered": False,
        }


def _validated_token(value: object) -> str:
    if not isinstance(value, str):
        raise FabricRepositoryMirrorActivationError(
            "github-credential-binding-unavailable"
        )
    token = value.strip()
    if (
        len(token) < 20
        or len(token) > 4096
        or any(char in token for char in ("\x00", "\r", "\n"))
    ):
        raise FabricRepositoryMirrorActivationError(
            "github-credential-binding-unavailable"
        )
    return token


def _ensure_private_child_dir(path: Path, parent: Path) -> None:
    if path.is_symlink():
        raise FabricRepositoryMirrorActivationError(
            "private-activation-directory-unsafe"
        )
    if path.exists():
        _require_private_dir(path, require_writable=True)
        if path.parent.resolve(strict=True) != parent:
            raise FabricRepositoryMirrorActivationError(
                "private-activation-directory-unsafe"
            )
        return
    try:
        path.mkdir(mode=0o700)
        os.chmod(path, 0o700)
        _fsync_dir(parent)
    except OSError as exc:
        raise FabricRepositoryMirrorActivationError(
            "private-activation-directory-unavailable"
        ) from exc
    _require_private_dir(path, require_writable=True)


def _require_private_dir(path: Path, *, require_writable: bool) -> None:
    if not path.is_absolute() or path.is_symlink():
        raise FabricRepositoryMirrorActivationError("private-directory-unsafe")
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise FabricRepositoryMirrorActivationError(
            "private-directory-unavailable"
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise FabricRepositoryMirrorActivationError("private-directory-unsafe")
    if require_writable and not os.access(resolved, os.W_OK | os.X_OK):
        raise FabricRepositoryMirrorActivationError(
            "private-directory-unavailable"
        )


def _require_private_file(path: Path) -> None:
    if not path.is_absolute() or path.is_symlink():
        raise FabricRepositoryMirrorActivationError("private-file-unsafe")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise FabricRepositoryMirrorActivationError(
            "private-file-unavailable"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600:
        raise FabricRepositoryMirrorActivationError("private-file-unsafe")


def _write_private_exact(path: Path, content: str) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            raise FabricRepositoryMirrorActivationError("private-file-unsafe")
        _require_private_file(path)
        try:
            current = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FabricRepositoryMirrorActivationError(
                "private-file-unavailable"
            ) from exc
        if current == content:
            return

    encoded = content.encode("utf-8")
    fd, raw = tempfile.mkstemp(prefix=".incoming-", dir=path.parent)
    temp = Path(raw)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
        _fsync_dir(path.parent)
    except OSError as exc:
        raise FabricRepositoryMirrorActivationError(
            "private-file-write-failed"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)
        temp.unlink(missing_ok=True)


def _merge_private_env(path: Path, updates: dict[str, str]) -> None:
    _require_private_file(path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FabricRepositoryMirrorActivationError(
            "private-runtime-configuration-unavailable"
        ) from exc

    retained: list[str] = []
    update_keys = set(updates)
    seen: set[str] = set()
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            retained.append(raw)
            continue
        key = raw.split("=", 1)[0].strip()
        if key in update_keys:
            if key in seen:
                continue
            retained.append(f"{key}={shlex.quote(updates[key])}")
            seen.add(key)
        else:
            retained.append(raw)
    for key in sorted(update_keys - seen):
        retained.append(f"{key}={shlex.quote(updates[key])}")
    content = "\n".join(retained).rstrip("\n") + "\n"
    _write_private_exact(path, content)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
