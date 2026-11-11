"""Offline, fail-closed artifact receipt preflight for #669.

This does NOT attest a serving process, trust the receipt signer, or authorize a
deployment. Runtime build identity must remain unknown until a separate
trusted installation/serving-generation witness has been qualified.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")
_SCHEMA = "runner-mcp/offline-artifact-receipt/v1"
_LIMIT = 64 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_offline_input(path: Path) -> bool:
    """Reject redirecting evidence paths before reading a private receipt.

    A leaf-only lstat() does not detect a symlinked grandparent. This
    bounded offline comparator never creates directories or scans a host.
    """
    if not path.is_absolute() or ".." in path.parts:
        return False
    try:
        return not any(ancestor.is_symlink() for ancestor in (path, *path.parents))
    except (OSError, RuntimeError, ValueError):
        return False


def _safe_regular(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not (
        info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    )


def _raise_walk_error(exc: OSError) -> None:
    raise exc


def offline_artifact_receipt_preflight(
    receipt: Path, wheel: Path, installed_package: Path
) -> dict[str, object]:
    """Verify bounded local bytes; never represent the result as active identity.

    A receipt is *input*, not self-authenticating evidence. An authorized
    installer must separately bind this preflight to trusted manifests,
    immutable venv generation and a currently serving process.
    """
    unavailable: dict[str, object] = {
        "schema_version": "runner-mcp/artifact-preflight/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    if not all(isinstance(p, Path) for p in (receipt, wheel, installed_package)):
        return unavailable
    if not all(
        _canonical_offline_input(path)
        for path in (receipt, wheel, installed_package)
    ):
        return unavailable
    if not _safe_regular(receipt) or not _safe_regular(wheel):
        return unavailable
    try:
        # A private receipt is necessary, but never sufficient, as an attestation.
        receipt_info = receipt.lstat()
        if receipt_info.st_uid != os.geteuid() or receipt_info.st_mode & 0o077:
            return unavailable
        if receipt_info.st_size > _LIMIT or not installed_package.is_dir():
            return unavailable
        raw = json.loads(receipt.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or set(raw) != {
            "schema_version", "source_revision", "wheel_sha256", "modules"
        } or raw["schema_version"] != _SCHEMA:
            return unavailable
        revision, expected_wheel, modules = (
            raw["source_revision"], raw["wheel_sha256"], raw["modules"]
        )
        if not isinstance(revision, str) or not _REV.fullmatch(revision):
            return unavailable
        if not isinstance(expected_wheel, str) or not _SHA.fullmatch(expected_wheel):
            return unavailable
        if not isinstance(modules, dict) or not 1 <= len(modules) <= 4096:
            return unavailable
        if _sha256(wheel) != expected_wheel:
            return unavailable
        if installed_package.is_symlink():
            return unavailable
        root = installed_package.resolve(strict=True)
        # Scan without following links. Linked directories must never hide extra modules.
        observed_names: set[str] = set()
        count = 0
        for current, directories, files in os.walk(root, followlinks=False, onerror=_raise_walk_error):
            for name in (*directories, *files):
                count += 1
                if count > 8192:
                    return unavailable
                entry = Path(current) / name
                if entry.is_symlink():
                    return unavailable
            for name in files:
                # This v1 receipt only specifies .py module digests. Fail closed
                # rather than treating unaccounted native extension code as safe.
                if name.endswith((".so", ".pyd", ".dll", ".dylib")):
                    return unavailable
                if name.endswith(".py"):
                    observed_names.add((Path(current) / name).relative_to(root).as_posix())
        if observed_names != set(modules):
            return unavailable
        for relative, expected in modules.items():
            if not isinstance(relative, str) or not isinstance(expected, str):
                return unavailable
            if not _SHA.fullmatch(expected) or len(relative) > 240 or not relative.endswith(".py"):
                return unavailable
            parts = Path(relative).parts
            if not parts or any(part in ("", ".", "..") for part in parts):
                return unavailable
            if Path(relative).is_absolute() or chr(92) in relative:
                return unavailable
            candidate = root.joinpath(*parts)
            if not _safe_regular(candidate) or not candidate.resolve().is_relative_to(root):
                return unavailable
            if _sha256(candidate) != expected:
                return unavailable
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return unavailable
    return {
        **unavailable,
        "state": "offline_bytes_match",
    }
