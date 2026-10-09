import os
from pathlib import Path

import pytest

from runner_mcp.fabric_release_archive_mirror_readiness import (
    FabricReleaseArchiveMirrorReadiness,
)

PRIMARY = "RUNNER_MCP_FABRIC_RELEASE_CUSTODY_ROOT"
MOUNT = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_MOUNT_ROOT"
MIRROR = "RUNNER_MCP_FABRIC_RELEASE_MIRROR_ROOT"


def _private(path: Path) -> None:
    path.mkdir(parents=True, mode=0o700)
    current = path
    while current.name and current != current.parent:
        if current.exists():
            os.chmod(current, 0o700)
        current = current.parent


def _fixture(tmp_path: Path):
    primary = tmp_path / "primary"
    mount = tmp_path / "volume"
    mirror = mount / "owner" / "releases"
    _private(primary)
    _private(mirror)
    os.chmod(mount, 0o700)
    os.chmod(mount / "owner", 0o700)
    environment = {
        PRIMARY: str(primary),
        MOUNT: str(mount),
        MIRROR: str(mirror),
    }
    return environment, primary, mount, mirror


def _ready_subject(environment, primary, mount, mirror):
    def device(path: Path) -> int:
        if path == primary:
            return 11
        if path in {mount, mirror}:
            return 22
        raise AssertionError("unexpected device lookup")

    return FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: path == mount,
        device_reader=device,
    )


def test_ready_when_private_roots_are_on_distinct_mounted_device(tmp_path):
    environment, primary, mount, mirror = _fixture(tmp_path)

    result = _ready_subject(environment, primary, mount, mirror).status()

    assert result == {
        "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
        "ready": True,
        "configurationState": "configured",
        "primaryCustodyReady": True,
        "mountReady": True,
        "mirrorRootReady": True,
        "distinctDeviceReady": True,
        "reasonCode": "ready",
        "mutationEnabled": False,
    }
    encoded = repr(result)
    assert str(primary) not in encoded
    assert str(mount) not in encoded
    assert str(mirror) not in encoded


def test_unconfigured_and_partial_bindings_fail_closed(tmp_path):
    unconfigured = FabricReleaseArchiveMirrorReadiness(environment={}).status()
    partial = FabricReleaseArchiveMirrorReadiness(
        environment={PRIMARY: str(tmp_path / "primary")}
    ).status()

    assert unconfigured["ready"] is False
    assert unconfigured["configurationState"] == "unconfigured"
    assert unconfigured["reasonCode"] == "storage-bindings-unconfigured"
    assert partial["ready"] is False
    assert partial["configurationState"] == "partial"
    assert partial["reasonCode"] == "storage-bindings-partial"


@pytest.mark.parametrize("key", [PRIMARY, MOUNT, MIRROR])
def test_missing_private_root_fails_closed(tmp_path, key):
    environment, primary, mount, mirror = _fixture(tmp_path)
    target = Path(environment[key])
    if target == mirror:
        target.rmdir()
    elif target == mount:
        mirror.rmdir()
        (mount / "owner").rmdir()
        target.rmdir()
    else:
        target.rmdir()

    result = _ready_subject(environment, primary, mount, mirror).status()

    assert result["ready"] is False
    assert result["mutationEnabled"] is False


@pytest.mark.parametrize("key", [PRIMARY, MOUNT, MIRROR])
def test_symlink_root_is_rejected(tmp_path, key):
    environment, primary, mount, mirror = _fixture(tmp_path)
    target = Path(environment[key])
    replacement = tmp_path / f"{key.lower()}-real"
    _private(replacement)

    if target == mirror:
        target.rmdir()
    elif target == mount:
        mirror.rmdir()
        (mount / "owner").rmdir()
        target.rmdir()
    else:
        target.rmdir()
    target.symlink_to(replacement, target_is_directory=True)

    result = _ready_subject(environment, primary, mount, mirror).status()

    assert result["ready"] is False
    assert result["mutationEnabled"] is False


def test_intermediate_symlink_is_rejected(tmp_path):
    primary = tmp_path / "primary"
    mount = tmp_path / "volume"
    outside = tmp_path / "outside"
    _private(primary)
    _private(mount)
    _private(outside)
    alias = mount / "owner"
    alias.symlink_to(outside, target_is_directory=True)
    mirror = alias / "releases"
    _private(outside / "releases")

    environment = {
        PRIMARY: str(primary),
        MOUNT: str(mount),
        MIRROR: str(mirror),
    }
    result = FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: path == mount,
        device_reader=lambda path: 11 if path == primary else 22,
    ).status()

    assert result["ready"] is False
    assert result["reasonCode"] in {
        "mirror-root-unavailable",
        "mirror-root-outside-mount",
    }


def test_directory_is_not_accepted_as_mount(tmp_path):
    environment, primary, mount, mirror = _fixture(tmp_path)

    result = FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: False,
        device_reader=lambda path: 22,
    ).status()

    assert result["ready"] is False
    assert result["mountReady"] is False
    assert result["reasonCode"] == "mirror-mount-not-mounted"


def test_same_device_is_rejected(tmp_path):
    environment, primary, mount, mirror = _fixture(tmp_path)

    result = FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: path == mount,
        device_reader=lambda path: 7,
    ).status()

    assert result["ready"] is False
    assert result["distinctDeviceReady"] is False
    assert result["reasonCode"] == "independent-device-required"


def test_mirror_root_must_be_strictly_inside_mount(tmp_path):
    environment, primary, mount, _ = _fixture(tmp_path)
    outside = tmp_path / "outside"
    _private(outside)
    environment[MIRROR] = str(outside)

    result = FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: path == mount,
        device_reader=lambda path: 11 if path == primary else 22,
    ).status()

    assert result["ready"] is False
    assert result["reasonCode"] == "mirror-root-outside-mount"


def test_mirror_root_must_report_mount_device(tmp_path):
    environment, primary, mount, mirror = _fixture(tmp_path)

    def device(path: Path) -> int:
        return {primary: 11, mount: 22, mirror: 33}[path]

    result = FabricReleaseArchiveMirrorReadiness(
        environment=environment,
        mount_checker=lambda path: path == mount,
        device_reader=device,
    ).status()

    assert result["ready"] is False
    assert result["reasonCode"] == "independent-device-required"


@pytest.mark.parametrize("key", [PRIMARY, MOUNT, MIRROR])
def test_broad_directory_permissions_are_rejected(tmp_path, key):
    environment, primary, mount, mirror = _fixture(tmp_path)
    os.chmod(Path(environment[key]), 0o755)

    result = _ready_subject(environment, primary, mount, mirror).status()

    assert result["ready"] is False


def test_readiness_performs_no_filesystem_mutation(tmp_path, monkeypatch):
    environment, primary, mount, mirror = _fixture(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("readiness attempted a mutation")

    for name in ("mkdir", "chmod", "unlink", "rename", "replace", "write_text", "write_bytes"):
        monkeypatch.setattr(Path, name, forbidden)

    result = _ready_subject(environment, primary, mount, mirror).status()

    assert result["ready"] is True
    assert result["mutationEnabled"] is False


@pytest.mark.parametrize(
    "value",
    ["relative/path", "/safe/../escape", "x" * 5000, "bad\x00path"],
)
def test_invalid_binding_text_is_rejected(value):
    result = FabricReleaseArchiveMirrorReadiness(
        environment={PRIMARY: value, MOUNT: "/m", MIRROR: "/m/r"}
    ).status()

    assert result["ready"] is False
    assert result["reasonCode"] == "storage-binding-invalid"
