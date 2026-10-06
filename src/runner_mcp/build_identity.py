from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

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


def installed_source_revision(config_dir: Path) -> str | None:
    """Return the exact installed revision from canonical private self-update state."""

    path = config_dir / "self-update-state.json"
    if path.is_symlink():
        raise BuildIdentityError("installed source revision state is unsafe")
    if not path.exists():
        return None
    if not path.is_file():
        raise BuildIdentityError("installed source revision state is unsafe")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildIdentityError("installed source revision state is unavailable") from exc
    candidate = raw.get("commit") if isinstance(raw, dict) else None
    if not isinstance(candidate, str) or _REVISION_RE.fullmatch(candidate) is None:
        raise BuildIdentityError("installed source revision state is invalid")
    return candidate


def runner_mcp_build_identity(
    build_version: str,
    *,
    source_revision: str | None = None,
) -> BuildIdentity:
    """Return only identity facts the installed runtime can currently prove."""

    return BuildIdentity(
        component_id="runner-mcp",
        build_version=build_version,
        source_revision=source_revision,
        artifact_digest=None,
        protocol_min=None,
        protocol_max=None,
        interface_schema_digest=None,
    )


def runner_mcp_mcp_build_identity(
    build_version: str,
    *,
    source_revision: str | None = None,
    interface_schema_digest: str | None = None,
) -> BuildIdentity:
    """Bind Runner-MCP identity to the installed MCP handshake protocol range."""

    protocol_min: str | None = None
    protocol_max: str | None = None
    try:
        from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS

        versions = tuple(HANDSHAKE_PROTOCOL_VERSIONS)
    except (ImportError, TypeError):
        versions = ()
    if (
        1 <= len(versions) <= 32
        and all(
            isinstance(version, str)
            and 1 <= len(version) <= _MAX_TEXT
            and version.isascii()
            and all(32 <= ord(char) < 127 for char in version)
            for version in versions
        )
    ):
        protocol_min = versions[0]
        protocol_max = versions[-1]
    return BuildIdentity(
        component_id="runner-mcp",
        build_version=build_version,
        source_revision=source_revision,
        artifact_digest=None,
        protocol_min=protocol_min,
        protocol_max=protocol_max,
        interface_schema_digest=interface_schema_digest,
    )


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
