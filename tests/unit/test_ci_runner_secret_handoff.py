from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from runner_mcp.ci_runner_guest_enrollment import (
    CIRunnerRegistrationSecret,
)
from runner_mcp.ci_runner_secret_handoff import (
    CIRunnerSecretHandoffError,
    CIRunnerSecretHandoffStore,
    validate_handoff_id,
)


def private_root(tmp_path: Path) -> Path:
    root = tmp_path / "handoff"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return root


def test_create_uses_random_opaque_name_and_mode_0600(
    tmp_path: Path,
) -> None:
    root = private_root(tmp_path)
    store = CIRunnerSecretHandoffStore(
        root=root,
        now=lambda: 1000.0,
        random_bytes=lambda _size: b"\x12" * 16,
    )
    secret = CIRunnerRegistrationSecret("s" * 32)

    handoff = store.create(secret)

    assert handoff.handoff_id == "12" * 16
    assert handoff.expires_at == 1300
    path = root / handoff.handoff_id
    assert path.read_text(encoding="ascii") == secret.value
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert secret.value not in handoff.handoff_id
    assert secret.value not in repr(handoff.to_payload())
    assert str(root) not in repr(handoff.to_payload())


def test_create_refuses_unsafe_root_permissions(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    root.chmod(0o755)

    with pytest.raises(
        CIRunnerSecretHandoffError,
        match="permissions",
    ):
        CIRunnerSecretHandoffStore(root=root).create(
            CIRunnerRegistrationSecret("s" * 32)
        )


def test_create_refuses_symlink_root(tmp_path: Path) -> None:
    target = private_root(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        CIRunnerSecretHandoffError,
        match="unsafe",
    ):
        CIRunnerSecretHandoffStore(root=alias).create(
            CIRunnerRegistrationSecret("s" * 32)
        )


def test_collision_never_overwrites_existing_record(
    tmp_path: Path,
) -> None:
    root = private_root(tmp_path)
    collision = root / ("aa" * 16)
    collision.write_text("existing", encoding="ascii")
    collision.chmod(0o600)

    store = CIRunnerSecretHandoffStore(
        root=root,
        random_bytes=lambda _size: b"\xaa" * 16,
    )

    with pytest.raises(
        CIRunnerSecretHandoffError,
        match="collision",
    ):
        store.create(CIRunnerRegistrationSecret("s" * 32))

    assert collision.read_text(encoding="ascii") == "existing"


def test_reap_expired_uses_metadata_without_parsing_secret(
    tmp_path: Path,
) -> None:
    root = private_root(tmp_path)
    expired = root / ("ab" * 16)
    expired.write_bytes(b"not-even-a-token-format")
    expired.chmod(0o600)
    os.utime(expired, (1000, 1000))

    fresh = root / ("cd" * 16)
    fresh.write_bytes(b"fresh-secret-value")
    fresh.chmod(0o600)
    os.utime(fresh, (1950, 1950))

    ignored = root / "unmanaged-file"
    ignored.write_bytes(b"do-not-touch")
    ignored.chmod(0o600)
    os.utime(ignored, (1000, 1000))

    store = CIRunnerSecretHandoffStore(
        root=root,
        ttl_seconds=300,
        now=lambda: 2000.0,
    )

    assert store.reap_expired() == 1
    assert not expired.exists()
    assert fresh.exists()
    assert ignored.exists()


@pytest.mark.parametrize(
    "value",
    [
        "",
        "short",
        "../" + "a" * 29,
        "g" * 32,
        "a" * 31,
        "a" * 33,
    ],
)
def test_handoff_id_validation_is_exact(value: str) -> None:
    with pytest.raises(
        CIRunnerSecretHandoffError,
        match="handoff id",
    ):
        validate_handoff_id(value)


def test_valid_handoff_id_is_safe_for_transport() -> None:
    value = "01" * 16

    assert validate_handoff_id(value) == value
