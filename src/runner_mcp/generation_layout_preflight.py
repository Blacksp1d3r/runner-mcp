"""Offline structural preflight for a versioned installation generation.

Owner/mode checks are not proof of immutability (root or owner can modify files).
Never use this preflight to attest a currently serving process or authorize a rollout.
"""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path

_GENERATION = re.compile(r"^generation-[0-9a-f]{40}-[0-9a-f]{64}$")


def offline_generation_layout_preflight(
    generation: Path, expected_source_revision: str, expected_wheel_sha256: str
) -> dict[str, object]:
    """Validate a standalone generation's lexical identity and structural safety."""
    result: dict[str, object] = {
        "schema_version": "runner-mcp/generation-layout-preflight/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    if not isinstance(generation, Path) or not generation.is_absolute():
        return result
    if not isinstance(expected_source_revision, str) or not isinstance(
        expected_wheel_sha256, str
    ):
        return result
    if len(expected_source_revision) != 40 or len(expected_wheel_sha256) != 64:
        return result
    if generation.name != (
        f"generation-{expected_source_revision}-{expected_wheel_sha256}"
    ) or not _GENERATION.fullmatch(generation.name):
        return result
    if ".." in generation.parts:
        return result
    try:
        for ancestor in (generation, *generation.parents):
            if ancestor.is_symlink():
                return result
        info = generation.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            return result
        if info.st_mode & 0o022:
            return result
        # We verify naming, ownership and directory mode only. A running
        # process can still use old imported modules or executable bytes.
        # No installed-file digest, file sealing or real process proof here.
    except OSError:
        return result
    return {**result, "state": "offline_layout_match"}
