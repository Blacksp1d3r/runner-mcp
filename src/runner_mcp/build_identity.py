from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS

_COMPONENT_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_TEXT = 128


class BuildIdentityError(ValueError):
    """Raised when Runner-MCP build identity is malformed or unsafe."""


@dataclass(frozen=True, slots=True)
class BuildIdentity:
    component_id: str
    build_version: str
    source_revision: str | None = None
    artifact_digest: str | None = None
    protocol_min: str | None = None
    protocol_max: str | None = None
    interface_schema_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.component_id, str) or _COMPONENT_RE.fullmatch(
            self.component_id
        ) is None:
            raise BuildIdentityError("component_id is invalid")
        _bounded_text(self.build_version, "build_version")
        if self.source_revision is not None and _REVISION_RE.fullmatch(
            self.source_revision
        ) is None:
            raise BuildIdentityError("source_revision is invalid")
        if self.artifact_digest is not None and _DIGEST_RE.fullmatch(
            self.artifact_digest
        ) is None:
            raise BuildIdentityError("artifact_digest is invalid")
        if self.protocol_min is not None:
            _bounded_text(self.protocol_min, "protocol_min")
        if self.protocol_max is not None:
            _bounded_text(self.protocol_max, "protocol_max")
        if (
            self.protocol_min is None
            and self.protocol_max is not None
            or self.protocol_min is not None
            and self.protocol_max is None
        ):
            raise BuildIdentityError("protocol range must be complete or unknown")
        if self.interface_schema_digest is not None and _DIGEST_RE.fullmatch(
            self.interface_schema_digest
        ) is None:
            raise BuildIdentityError("interface_schema_digest is invalid")

    def to_payload(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "build_version": self.build_version,
            "source_revision": self.source_revision,
            "artifact_digest": self.artifact_digest,
            "protocol_min": self.protocol_min,
            "protocol_max": self.protocol_max,
            "interface_schema_digest": self.interface_schema_digest,
        }


def runner_mcp_build_identity(
    build_version: str,
    *,
    config_dir: Path | None = None,
    interface_schema_digest: str | None = None,
) -> BuildIdentity:
    """Return only identity facts the installed runtime can currently prove."""

    source_revision, artifact_digest = _installed_provenance(config_dir)
    versions = tuple(HANDSHAKE_PROTOCOL_VERSIONS)
    protocol_min = versions[0] if versions else None
    protocol_max = versions[-1] if versions else None
    return BuildIdentity(
        component_id="runner-mcp",
        build_version=build_version,
        source_revision=source_revision,
        artifact_digest=artifact_digest,
        protocol_min=protocol_min,
        protocol_max=protocol_max,
        interface_schema_digest=interface_schema_digest,
    )


def _installed_provenance(config_dir: Path | None) -> tuple[str | None, str | None]:
    if config_dir is None:
        return None, None
    try:
        root = config_dir.expanduser().resolve(strict=True)
        metadata = root.stat()
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or metadata.st_mode & 0o077
        ):
            return None, None
        path = root / "self-update-state.json"
        if path.is_symlink():
            return None, None
        info = path.stat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or info.st_size > 8192
            or info.st_mode & 0o077
        ):
            return None, None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(payload, dict):
        return None, None
    if not set(payload) <= {"commit", "installed_at", "artifact_digest"}:
        return None, None
    commit = payload.get("commit")
    if not isinstance(commit, str) or _REVISION_RE.fullmatch(commit) is None:
        return None, None
    artifact = payload.get("artifact_digest")
    if artifact is None:
        return commit, None
    if not isinstance(artifact, str) or _DIGEST_RE.fullmatch(artifact) is None:
        return None, None
    return commit, artifact


def _bounded_text(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_TEXT
        or not value.isascii()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise BuildIdentityError(f"{field} is invalid")
    return value
