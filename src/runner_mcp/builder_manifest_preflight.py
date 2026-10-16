"""Fail-closed offline builder-manifest validation against an EXTERNALLY trusted digest.

The expected digest MUST originate from an independent protected authority.
This comparator cannot authenticate where a caller obtained that digest,
cannot issue trust, and NEVER proves or promotes a serving process.
"""
from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path

_REV = re.compile(r"^[0-9a-f]{40}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SCHEMA = "runner-mcp/builder-manifest/v1"
_LIMIT = 65536


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()



def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result

def pinned_builder_manifest_preflight(
    manifest: Path, wheel: Path, expected_manifest_sha256: str
) -> dict[str, object]:
    """Offline equality only, no authority to deploy, install or attest runtime."""
    result: dict[str, object] = {
        "schema_version": "runner-mcp/builder-manifest-preflight/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    if not isinstance(manifest, Path) or not isinstance(wheel, Path):
        return result
    if not isinstance(expected_manifest_sha256, str) or not _SHA.fullmatch(
        expected_manifest_sha256
    ):
        return result
    try:
        info = manifest.lstat()
        wheel_info = wheel.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return result
        if info.st_size > _LIMIT or info.st_mode & 0o022:
            return result
        if not stat.S_ISREG(wheel_info.st_mode) or wheel_info.st_nlink != 1:
            return result
        if wheel_info.st_mode & 0o022:
            return result
        # The pinned SHA must come from outside this manifest and from a
        # separate protected trust channel. Never read it from the manifest.
        # Hash and parse the SAME bounded bytes to avoid an in-place swap
        # between separately opening the manifest for hash and JSON parsing.
        manifest_bytes = manifest.read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
            return result
        document = json.loads(
            manifest_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        if not isinstance(document, dict) or set(document) != {
            "schema_version",
            "source_revision",
            "distribution_version",
            "wheel_sha256",
            "interface_schema_digest",
        }:
            return result
        if document["schema_version"] != _SCHEMA:
            return result
        revision = document["source_revision"]
        version = document["distribution_version"]
        digest = document["wheel_sha256"]
        schema = document["interface_schema_digest"]
        if not isinstance(revision, str) or not _REV.fullmatch(revision):
            return result
        if not isinstance(version, str) or not _VERSION.fullmatch(version):
            return result
        if any(not isinstance(item, str) or not _SHA.fullmatch(item)
               for item in (digest, schema)):
            return result
        if _hash_file(wheel) != digest:
            return result
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        return result
    return {**result, "state": "offline_manifest_and_wheel_match"}
