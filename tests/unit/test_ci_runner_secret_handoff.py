from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

import runner_mcp.ci_runner_secret_handoff as handoff_module
from runner_mcp.ci_runner_guest_enrollment import (
    CIRunnerRegistrationSecret,
)
from runner_mcp.ci_runner_secret_handoff import (
    CIRunnerSecretHandoff,
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


def test_reap_refuses_oversized_directory_without_deleting_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = private_root(tmp_path)
    expired = root / ("ab" * 16)
    expired.write_bytes(b"secret")
    expired.chmod(0o600)
    os.utime(expired, (1000, 1000))
    (root / "ignored-one").touch()
    (root / "ignored-two").touch()
    monkeypatch.setattr(handoff_module, "_MAX_REAP_ENTRIES", 2)
    store = CIRunnerSecretHandoffStore(root=root, now=lambda: 2000.0)
    with pytest.raises(CIRunnerSecretHandoffError, match="too many entries"):
        store.reap_expired()
    assert expired.exists()


def test_reap_accepts_exact_directory_entry_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = private_root(tmp_path)
    expired = root / ("ab" * 16)
    expired.write_bytes(b"secret")
    expired.chmod(0o600)
    os.utime(expired, (1000, 1000))
    (root / "ignored").touch()
    monkeypatch.setattr(handoff_module, "_MAX_REAP_ENTRIES", 2)
    store = CIRunnerSecretHandoffStore(root=root, now=lambda: 2000.0)
    assert store.reap_expired() == 1
    assert not expired.exists()


@pytest.mark.parametrize("bad", [None, 123, [], b"a" * 16])
def test_public_handoff_record_rejects_nonstrings_without_typeerror(
    bad: object,
) -> None:
    with pytest.raises(CIRunnerSecretHandoffError, match="handoff id"):
        CIRunnerSecretHandoff(handoff_id=bad, expires_at=2000)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [0, -1, 1 << 53, True, "2000"])
def test_public_handoff_record_rejects_invalid_expiry_bounds(
    bad: object,
) -> None:
    with pytest.raises(CIRunnerSecretHandoffError, match="expiry"):
        CIRunnerSecretHandoff(handoff_id="ab" * 16, expires_at=bad)  # type: ignore[arg-type]


def test_public_handoff_record_accepts_valid_expiry_boundary() -> None:
    record = CIRunnerSecretHandoff(handoff_id="ab" * 16, expires_at=(1 << 53) - 1)
    assert record.to_payload()["expires_at"] == (1 << 53) - 1


@pytest.mark.parametrize(
    "invalid_clock",
    [float("nan"), float("inf"), float("-inf"), -1.0, 0.0, float(1 << 54)],
)
def test_create_with_bad_clock_writes_no_secret_file(
    tmp_path: Path, invalid_clock: float,
) -> None:
    root = private_root(tmp_path)
    store = CIRunnerSecretHandoffStore(
        root=root,
        now=lambda: invalid_clock,
        random_bytes=lambda _size: b"\x12" * 16,
    )
    with pytest.raises(CIRunnerSecretHandoffError, match="clock"):
        store.create(CIRunnerRegistrationSecret("s" * 32))
    assert list(root.iterdir()) == []


def test_create_uses_one_clock_sample_for_expiry_and_file_mtime(tmp_path: Path) -> None:
    root = private_root(tmp_path)
    sampled = []

    def clock() -> float:
        sampled.append(1)
        return 2000.0 + len(sampled) - 1

    record = CIRunnerSecretHandoffStore(
        root=root,
        now=clock,
        random_bytes=lambda _size: b"\x34" * 16,
    ).create(CIRunnerRegistrationSecret("s" * 32))
    assert sampled == [1]
    assert record.expires_at == 2300
    assert int((root / record.handoff_id).stat().st_mtime) == 2000
