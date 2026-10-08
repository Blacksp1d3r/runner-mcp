from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from runner_mcp.artifact_custody import (
    ArtifactCustodyError,
    ContentAddressedArtifactCustody,
)


def private_config_dir(tmp_path: Path) -> Path:
    root = tmp_path / "config"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return root


def test_publish_is_content_addressed_private_and_idempotent(tmp_path: Path) -> None:
    data = b"immutable qualification artifact"
    digest = hashlib.sha256(data).hexdigest()
    source = tmp_path / "source.bin"
    source.write_bytes(data)
    source.chmod(0o600)
    custody = ContentAddressedArtifactCustody(
        config_dir=private_config_dir(tmp_path)
    )

    first = custody.publish(
        trusted_source=source,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )
    second = custody.publish(
        trusted_source=source,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )

    assert first.cache_state == "miss"
    assert second.cache_state == "hit"
    assert first.path == second.path
    assert first.path.name == digest
    assert first.path.parent.name == digest[:2]
    assert first.path.read_bytes() == data
    assert first.path.stat().st_mode & 0o777 == 0o600
    assert first.path.parent.stat().st_mode & 0o777 == 0o700
    assert custody.bounded_evidence(second) == {
        "sha256": digest,
        "sizeBytes": len(data),
        "cache": "hit",
    }


def test_resolve_reverifies_digest_and_size(tmp_path: Path) -> None:
    data = b"immutable qualification artifact"
    digest = hashlib.sha256(data).hexdigest()
    source = tmp_path / "source.bin"
    source.write_bytes(data)
    custody = ContentAddressedArtifactCustody(
        config_dir=private_config_dir(tmp_path)
    )
    stored = custody.publish(
        trusted_source=source,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )

    stored.path.write_bytes(b"tampered")
    stored.path.chmod(0o600)

    with pytest.raises(ArtifactCustodyError, match="size mismatch"):
        custody.resolve(
            expected_sha256=digest,
            expected_size_bytes=len(data),
        )


def test_symlink_source_and_symlink_object_fail_closed(tmp_path: Path) -> None:
    data = b"immutable qualification artifact"
    digest = hashlib.sha256(data).hexdigest()
    real = tmp_path / "real.bin"
    real.write_bytes(data)
    source = tmp_path / "source.bin"
    source.symlink_to(real)
    config = private_config_dir(tmp_path)
    custody = ContentAddressedArtifactCustody(config_dir=config)

    with pytest.raises(ArtifactCustodyError, match="source unavailable"):
        custody.publish(
            trusted_source=source,
            expected_sha256=digest,
            expected_size_bytes=len(data),
        )

    source.unlink()
    source.write_bytes(data)
    stored = custody.publish(
        trusted_source=source,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )
    stored.path.unlink()
    stored.path.symlink_to(real)

    with pytest.raises(ArtifactCustodyError, match="unsafe"):
        custody.resolve(
            expected_sha256=digest,
            expected_size_bytes=len(data),
        )


def test_world_readable_existing_object_fails_closed(tmp_path: Path) -> None:
    data = b"immutable qualification artifact"
    digest = hashlib.sha256(data).hexdigest()
    source = tmp_path / "source.bin"
    source.write_bytes(data)
    custody = ContentAddressedArtifactCustody(
        config_dir=private_config_dir(tmp_path)
    )
    stored = custody.publish(
        trusted_source=source,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )
    stored.path.chmod(0o644)

    with pytest.raises(ArtifactCustodyError, match="unsafe"):
        custody.resolve(
            expected_sha256=digest,
            expected_size_bytes=len(data),
        )


@pytest.mark.parametrize(
    ("digest", "size"),
    [
        ("A" * 64, 1),
        ("0" * 63, 1),
        ("0" * 64, 0),
        ("0" * 64, -1),
        ("0" * 64, True),
    ],
)
def test_invalid_identity_is_rejected(
    tmp_path: Path,
    digest: str,
    size: int,
) -> None:
    custody = ContentAddressedArtifactCustody(
        config_dir=private_config_dir(tmp_path)
    )

    with pytest.raises(ArtifactCustodyError, match="identity is invalid"):
        custody.resolve(expected_sha256=digest, expected_size_bytes=size)
