"""Offline detached Ed25519 signature verification for an independently pinned builder key.

A matching signature demonstrates possession of a corresponding private key,
NOT that the key is authorized, current, unrevoked, or that the software runs.
The expected public-key digest must come from an INDEPENDENT trusted operator
channel. Never accept its value from an untrusted manifest or receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
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


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate manifest key")
        out[key] = value
    return out


def _builder_schema_valid(raw: bytes) -> bool:
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    return (
        isinstance(obj, dict)
        and set(obj) == {
            "schema_version",
            "source_revision",
            "distribution_version",
            "wheel_sha256",
            "interface_schema_digest",
        }
        and obj["schema_version"] == "runner-mcp/builder-manifest/v1"
        and isinstance(obj["source_revision"], str)
        and bool(_REV.fullmatch(obj["source_revision"]))
        and isinstance(obj["distribution_version"], str)
        and bool(_VERSION.fullmatch(obj["distribution_version"]))
        and isinstance(obj["wheel_sha256"], str)
        and bool(_SHA.fullmatch(obj["wheel_sha256"]))
        and isinstance(obj["interface_schema_digest"], str)
        and bool(_SHA.fullmatch(obj["interface_schema_digest"]))
    )


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
        if not _builder_schema_valid(raw_manifest):
            return unverified
    except (OSError, ValueError, TypeError, RecursionError, InvalidSignature):
        return unverified
    return {**unverified, "state": "offline_signature_match"}
