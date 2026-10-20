"""Offline-only evidence-chain comparator for #669.

This function is a consistency aid, NOT an attestation of trusted custody,
immutable bytes, or any serving process. All evidence remains mutable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight
from runner_mcp.builder_manifest_preflight import pinned_builder_manifest_preflight
from runner_mcp.generation_layout_preflight import offline_generation_layout_preflight

_REV = re.compile(r"^[0-9a-f]{40}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _canonical_offline_evidence_path(candidate: Path) -> bool:
    """Refuse syntactically redirected offline evidence paths before any reads.

    Path.is_relative_to() is lexical. In particular, foo/../bar can pass that
    predicate while resolving elsewhere. The offline chain must not accept
    symlinked ancestors of the manifest, receipt, wheel, package or generation
    as evidence of one fixed release location.
    """
    if (
        not isinstance(candidate, Path)
        or not candidate.is_absolute()
        or ".." in candidate.parts
    ):
        return False
    try:
        return not any(
            part.is_symlink() for part in (candidate, *candidate.parents)
        )
    except (OSError, RuntimeError, ValueError):
        return False


def offline_evidence_chain_preflight(
    manifest: Path,
    receipt: Path,
    wheel: Path,
    installed_package: Path,
    generation: Path,
    independently_pinned_manifest_sha256: str,
) -> dict[str, object]:
    """Check offline relationships; ALWAYS refuse active provenance claims."""
    unverified: dict[str, object] = {
        "schema_version": "runner-mcp/offline-evidence-chain/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    try:
        if not all(
            _canonical_offline_evidence_path(path)
            for path in (manifest, receipt, wheel, installed_package, generation)
        ):
            return unverified
        builder = pinned_builder_manifest_preflight(
            manifest, wheel, independently_pinned_manifest_sha256
        )
        if builder["state"] != "offline_manifest_and_wheel_match":
            return unverified
        modules = offline_artifact_receipt_preflight(
            receipt, wheel, installed_package
        )
        if modules["state"] != "offline_bytes_match":
            return unverified

        # Read one bounded snapshot per manifest; cross-check every claimed
        # identity. This does not eliminate races against mutable files:
        # caller must separately guarantee independent custody/sealing.
        if manifest.stat().st_size > 65536 or receipt.stat().st_size > 65536:
            return unverified
        manifest_bytes = manifest.read_bytes()
        receipt_bytes = receipt.read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != independently_pinned_manifest_sha256:
            return unverified
        build = json.loads(manifest_bytes)
        install = json.loads(receipt_bytes)
        if not isinstance(build, dict) or not isinstance(install, dict):
            return unverified
        revision = build.get("source_revision")
        wheel_sha = build.get("wheel_sha256")
        if not isinstance(revision, str) or not _REV.fullmatch(revision):
            return unverified
        if not isinstance(wheel_sha, str) or not _SHA.fullmatch(wheel_sha):
            return unverified
        if install.get("source_revision") != revision:
            return unverified
        if install.get("wheel_sha256") != wheel_sha:
            return unverified
        layout = offline_generation_layout_preflight(generation, revision, wheel_sha)
        if layout["state"] != "offline_layout_match":
            return unverified
        # An independently valid package tree outside this release generation
        # is not evidence of the generation's installed bytes.
        if installed_package == generation:
            return unverified
        if not installed_package.is_relative_to(generation):
            return unverified
        current = installed_package
        while current != generation:
            if current.is_symlink():
                return unverified
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
                return unverified
            if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                return unverified
            current = current.parent
        # Revalidate the exact pin at the end; a filesystem can still mutate
        # after this read and therefore active identity must remain unknown.
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != independently_pinned_manifest_sha256:
            return unverified
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return unverified
    return {**unverified, "state": "offline_candidate_chain_match"}
