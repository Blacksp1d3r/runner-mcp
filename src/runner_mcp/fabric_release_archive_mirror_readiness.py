from __future__ import annotations

import os
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

_SCHEMA = "runner-mcp/fabric-release-archive-mirror-readiness/v1"

_PRIMARY_ENV = "RUNNER_MCP_FABRIC_RELEASE_CUSTODY_ROOT"
_MOUNT_ENV = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_MOUNT_ROOT"
_MIRROR_ENV = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_ROOT"
_ENV_KEYS = (_PRIMARY_ENV, _MOUNT_ENV, _MIRROR_ENV)

_MAX_PATH_TEXT = 4096


class FabricReleaseArchiveMirrorReadiness:
    """Read-only admission evidence for an independent release-archive volume."""

    def __init__(
        self,
        *,
        environment: Mapping[str, str],
        mount_checker: Callable[[Path], bool] | None = None,
        device_reader: Callable[[Path], int] | None = None,
    ) -> None:
        self.environment = environment
        self._mount_checker = mount_checker or _default_mount_checker
        self._device_reader = device_reader or _default_device_reader

    def status(self) -> dict[str, Any]:
        values = {key: self.environment.get(key) for key in _ENV_KEYS}
        present = {
            key: isinstance(value, str) and bool(value)
            for key, value in values.items()
        }
        count = sum(present.values())

        if count == 0:
            return _result(
                configuration_state="unconfigured",
                reason_code="storage-bindings-unconfigured",
            )
        if count != len(_ENV_KEYS):
            return _result(
                configuration_state="partial",
                reason_code="storage-bindings-partial",
            )

        paths: dict[str, Path] = {}
        for key in _ENV_KEYS:
            value = values[key]
            path = _bounded_absolute_path(value)
            if path is None:
                return _result(
                    configuration_state="configured",
                    reason_code="storage-binding-invalid",
                )
            paths[key] = path

        primary = paths[_PRIMARY_ENV]
        mount = paths[_MOUNT_ENV]
        mirror = paths[_MIRROR_ENV]

        primary_ready = _private_directory(primary)
        if not primary_ready:
            return _result(
                configuration_state="configured",
                reason_code="primary-custody-unavailable",
            )

        mount_directory_ready = _private_directory(mount)
        if not mount_directory_ready:
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                reason_code="mirror-mount-unavailable",
            )

        try:
            mounted = bool(self._mount_checker(mount))
        except OSError:
            mounted = False
        if not mounted:
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                reason_code="mirror-mount-not-mounted",
            )

        mirror_ready = _private_directory(mirror)
        if not mirror_ready:
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                mount_ready=True,
                reason_code="mirror-root-unavailable",
            )

        if not _strict_child_without_symlink_ancestors(mirror, mount):
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                mount_ready=True,
                mirror_root_ready=True,
                reason_code="mirror-root-outside-mount",
            )

        try:
            primary_device = self._device_reader(primary)
            mount_device = self._device_reader(mount)
            mirror_device = self._device_reader(mirror)
        except (OSError, ValueError):
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                mount_ready=True,
                mirror_root_ready=True,
                reason_code="storage-device-unavailable",
            )

        if (
            isinstance(primary_device, bool)
            or isinstance(mount_device, bool)
            or isinstance(mirror_device, bool)
            or not isinstance(primary_device, int)
            or not isinstance(mount_device, int)
            or not isinstance(mirror_device, int)
            or primary_device < 0
            or mount_device < 0
            or mirror_device < 0
        ):
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                mount_ready=True,
                mirror_root_ready=True,
                reason_code="storage-device-unavailable",
            )

        if primary_device == mount_device or mirror_device != mount_device:
            return _result(
                configuration_state="configured",
                primary_custody_ready=True,
                mount_ready=True,
                mirror_root_ready=True,
                reason_code="independent-device-required",
            )

        return _result(
            ready=True,
            configuration_state="configured",
            primary_custody_ready=True,
            mount_ready=True,
            mirror_root_ready=True,
            distinct_device_ready=True,
            reason_code="ready",
        )


def _result(
    *,
    ready: bool = False,
    configuration_state: str,
    primary_custody_ready: bool = False,
    mount_ready: bool = False,
    mirror_root_ready: bool = False,
    distinct_device_ready: bool = False,
    reason_code: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": _SCHEMA,
        "ready": ready,
        "configurationState": configuration_state,
        "primaryCustodyReady": primary_custody_ready,
        "mountReady": mount_ready,
        "mirrorRootReady": mirror_root_ready,
        "distinctDeviceReady": distinct_device_ready,
        "reasonCode": reason_code,
        "mutationEnabled": False,
    }


def _bounded_absolute_path(value: object) -> Path | None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_PATH_TEXT
        or "\x00" in value
    ):
        return None
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        return None
    return path


def _private_directory(path: Path) -> bool:
    if not path.is_absolute():
        return False
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISDIR(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o700
        and os.access(path, os.R_OK | os.X_OK)
    )


def _strict_child_without_symlink_ancestors(child: Path, parent: Path) -> bool:
    if child == parent or not child.is_relative_to(parent):
        return False
    current = child.parent
    while current != parent:
        try:
            metadata = current.lstat()
        except OSError:
            return False
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            return False
        current = current.parent
    try:
        child_resolved = child.resolve(strict=True)
        parent_resolved = parent.resolve(strict=True)
    except OSError:
        return False
    return child_resolved != parent_resolved and child_resolved.is_relative_to(
        parent_resolved
    )


def _default_mount_checker(path: Path) -> bool:
    return os.path.ismount(path)


def _default_device_reader(path: Path) -> int:
    return path.stat().st_dev
