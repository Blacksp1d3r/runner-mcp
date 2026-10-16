"""Offline detached Ed25519 signature verification for an independently pinned builder key.

A matching signature demonstrates possession of a corresponding private key,
NOT that the key is authorized, current, unrevoked, or that the software runs.
The expected public-key digest must come from an INDEPENDENT trusted operator
channel. Never accept its value from an untrusted manifest or receipt.
"""
from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_SHA = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST = 65536


def _safe_regular_file(path: Path, *, limit: int) -> bool:
    if not isinstance(path, Path):
        return False
    try:
        info = path.lstat()
        return (
            stat.S_ISREG(info.st_mode)
            and info.st_nlink == 1
            and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            and 0 < info.st_size <= limit
        )
    except OSError:
        return False


def detached_builder_signature_preflight(
    manifest: Path,
    public_key: Path,
    signature: Path,
    expected_public_key_sha256: str,
) -> dict[str, object]:
    """Compare offline signature bytes; NEVER report active installed identity."""
    unverified: dict[str, object] = {
        "schema_version": "runner-mcp/detached-builder-signature-preflight/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    if not isinstance(expected_public_key_sha256, str) or not _SHA.fullmatch(
        expected_public_key_sha256
    ):
        return unverified
    if not all(
        _safe_regular_file(p, limit=limit)
        for p, limit in (
            (manifest, _MAX_MANIFEST),
            (public_key, 32),
            (signature, 64),
        )
    ):
        return unverified
    try:
        raw_manifest = manifest.read_bytes()
        raw_public_key = public_key.read_bytes()
        raw_signature = signature.read_bytes()
        if len(raw_public_key) != 32 or len(raw_signature) != 64:
            return unverified
        if not (0 < len(raw_manifest) <= _MAX_MANIFEST):
            return unverified
        if hashlib.sha256(raw_public_key).hexdigest() != expected_public_key_sha256:
            return unverified
        Ed25519PublicKey.from_public_bytes(raw_public_key).verify(
            raw_signature, raw_manifest
        )
    except (OSError, ValueError, TypeError, InvalidSignature):
        return unverified
    return {**unverified, "state": "offline_signature_match"}
