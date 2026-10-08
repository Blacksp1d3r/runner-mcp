"""Private content-addressed artifact custody for bounded worker use."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_ARTIFACT_BYTES = 4 * 1024 * 1024 * 1024


class ArtifactCustodyError(RuntimeError):
    """Sanitized failure from private content-addressed artifact custody."""


@dataclass(frozen=True, slots=True)
class ArtifactObject:
    sha256: str
    size_bytes: int
    path: Path
    cache_state: str


class ContentAddressedArtifactCustody:
    """Store immutable artifacts under a private digest-derived local root."""

    def __init__(self, *, config_dir: Path) -> None:
        self.config_dir = config_dir.expanduser().resolve()
        self._root = self.config_dir / "artifact-custody" / "sha256"

    def publish(
        self,
        *,
        trusted_source: Path,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> ArtifactObject:
        self._validate_identity(expected_sha256, expected_size_bytes)
        source = trusted_source.expanduser()
        data = self._read_trusted_source(
            source,
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
        )
        return self.publish_bytes(
            data=data,
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
        )

    def publish_bytes(
        self,
        *,
        data: bytes,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> ArtifactObject:
        self._validate_identity(expected_sha256, expected_size_bytes)
        if not isinstance(data, bytes):
            raise ArtifactCustodyError("artifact payload is invalid")
        if len(data) != expected_size_bytes:
            raise ArtifactCustodyError("artifact payload size mismatch")
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ArtifactCustodyError("artifact payload digest mismatch")
        self._ensure_private_tree()

        object_dir = self._root / expected_sha256[:2]
        self._ensure_private_dir(object_dir, self._root)
        target = object_dir / expected_sha256

        if target.exists() or target.is_symlink():
            self._verify_object(
                target,
                expected_sha256=expected_sha256,
                expected_size_bytes=expected_size_bytes,
            )
            return ArtifactObject(
                sha256=expected_sha256,
                size_bytes=expected_size_bytes,
                path=target,
                cache_state="hit",
            )

        try:
            atomic_replace_private(target, data)
        except PrivateAtomicWriteError as exc:
            raise ArtifactCustodyError("artifact custody publish failed") from exc

        self._verify_object(
            target,
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
        )
        return ArtifactObject(
            sha256=expected_sha256,
            size_bytes=expected_size_bytes,
            path=target,
            cache_state="miss",
        )

    def resolve(
        self,
        *,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> ArtifactObject:
        self._validate_identity(expected_sha256, expected_size_bytes)
        target = self._root / expected_sha256[:2] / expected_sha256
        self._verify_object(
            target,
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
        )
        return ArtifactObject(
            sha256=expected_sha256,
            size_bytes=expected_size_bytes,
            path=target,
            cache_state="hit",
        )

    @staticmethod
    def bounded_evidence(artifact: ArtifactObject) -> dict[str, object]:
        return {
            "sha256": artifact.sha256,
            "sizeBytes": artifact.size_bytes,
            "cache": artifact.cache_state,
        }

    def _ensure_private_tree(self) -> None:
        parent = self.config_dir
        artifact_root = parent / "artifact-custody"
        self._ensure_private_dir(artifact_root, parent)
        self._ensure_private_dir(self._root, artifact_root)

    @staticmethod
    def _ensure_private_dir(path: Path, parent: Path) -> None:
        if path.is_symlink():
            raise ArtifactCustodyError("artifact custody directory is unsafe")
        try:
            path.mkdir(mode=0o700, exist_ok=True)
            os.chmod(path, 0o700)
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise ArtifactCustodyError("artifact custody directory unavailable") from exc
        if resolved.parent != parent.resolve():
            raise ArtifactCustodyError("artifact custody directory is unsafe")
        if resolved.stat().st_mode & 0o777 != 0o700:
            raise ArtifactCustodyError("artifact custody directory is unsafe")

    @staticmethod
    def _validate_identity(sha256: str, size_bytes: int) -> None:
        if not isinstance(sha256, str) or _SHA256_RE.fullmatch(sha256) is None:
            raise ArtifactCustodyError("artifact identity is invalid")
        if (
            isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or not 1 <= size_bytes <= _MAX_ARTIFACT_BYTES
        ):
            raise ArtifactCustodyError("artifact identity is invalid")

    @staticmethod
    def _read_trusted_source(
        path: Path,
        *,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> bytes:
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise ArtifactCustodyError("trusted artifact source unavailable") from exc
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise ArtifactCustodyError("trusted artifact source unavailable")
        if metadata.st_size != expected_size_bytes:
            raise ArtifactCustodyError("trusted artifact source size mismatch")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ArtifactCustodyError("trusted artifact source unavailable") from exc
        if len(data) != expected_size_bytes:
            raise ArtifactCustodyError("trusted artifact source size mismatch")
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ArtifactCustodyError("trusted artifact source digest mismatch")
        return data

    @staticmethod
    def _verify_object(
        path: Path,
        *,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> None:
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise ArtifactCustodyError("artifact object unavailable") from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or metadata.st_mode & 0o077
        ):
            raise ArtifactCustodyError("artifact object is unsafe")
        if metadata.st_size != expected_size_bytes:
            raise ArtifactCustodyError("artifact object size mismatch")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ArtifactCustodyError("artifact object unavailable") from exc
        if len(data) != expected_size_bytes:
            raise ArtifactCustodyError("artifact object size mismatch")
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ArtifactCustodyError("artifact object digest mismatch")
