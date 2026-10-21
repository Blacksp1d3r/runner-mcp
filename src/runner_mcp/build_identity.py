from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_COMPONENT_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_EPOCH_RE = re.compile(r"^[0-9a-f]{32}$")
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


def last_self_update_revision(config_dir: Path) -> str | None:
    """Return the historical self-update commit, NOT the active package revision."""

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


def installed_source_revision(config_dir: Path) -> str | None:
    """Fail closed until the serving artifact has independent provenance.

    The self-update transaction file records the LAST self-update, not the
    currently executing wheel. A manual install, rollback or in-place upgrade
    can leave that marker unchanged. Returning it here misidentifies a live
    process. Verified artifact/loaded-module receipts are separately tracked
    under issue #669 and must be integrated before a revision can be emitted.
    """
    if not isinstance(config_dir, Path):
        raise BuildIdentityError("installed source revision config is invalid")
    return None


def fail_closed_runtime_provenance(
    status: dict[str, object], *,
    loaded_version: str,
    installed_distribution_version: str,
    serving_instance_epoch: str | None = None,
) -> dict[str, object]:
    """Separate historical self-update markers from active build identity.

    Manager status dictionaries are merged after runtime_status initialises its
    own version. Their version and self-update revisions are NOT evidence of
    the imported server's current source. Make it impossible for a later
    manager merge to silently turn historical markers into active identity.
    """
    _bounded_text(loaded_version, "loaded_version")
    _bounded_text(installed_distribution_version, "installed_distribution_version")
    if serving_instance_epoch is not None and (
        type(serving_instance_epoch) is not str
        or _EPOCH_RE.fullmatch(serving_instance_epoch) is None
    ):
        raise BuildIdentityError("serving instance epoch is invalid")
    result = dict(status)
    for field in ("last_installed_commit", "source_commit", "active_runtime_revision"):
        result[f"self_update_history_{field}"] = result.pop(field, None)
        result[field] = None
    for field in ("source_baseline_aligned", "runtime_activation_aligned"):
        result[f"self_update_history_{field}"] = result.pop(field, None)
        result[field] = None
    result.update(
        {
            "version": loaded_version,
            "installed_distribution_version": installed_distribution_version,
            "active_build_provenance_verified": False,
            "active_artifact_revision": None,
            "active_artifact_digest": None,
            # A manager's self-update transaction readiness is NOT sufficient
            # while the loaded wheel/source and current process are unknown.
            # Never forward a stale True into release/fleet admission.
            "self_update_ready": False,
            # This authenticated reply observes only the currently connected
            # serving process. Equal distribution versions across hosts (or
            # a CLI on the same host) cannot attest route, wheel or role identity.
            "reply_identity_scope": "this_connected_process_only",
            "reply_source_host_verified": False,
            "loaded_module_wheel_identity_verified": False,
            "six_role_process_roster_verified": False,
            "loaded_installed_versions_equal": (
                loaded_version == installed_distribution_version
            ),
            # A manager may return stale/injected epoch fields after status
            # aggregation. Only this MCP server's in-memory epoch is allowed
            # to survive in the authenticated local response, never as proof
            # of the authenticated host or another process.
            "serving_instance_epoch": serving_instance_epoch,
            "serving_instance_epoch_authenticated": False,
        }
    )
    return result


def candidate_revision_with_wheel_identity(
    identity: object, *, loaded_version: str
) -> str | None:
    """Read revision from a qualified identity provider, never from history.

    This is a structural gate, NOT a signature or serving-process verifier.
    The caller must first qualify the provider against independent current
    process, signer and wheel evidence. Mere offline RECORD matching is not
    enough to supply such a provider.
    """
    if not isinstance(identity, BuildIdentity):
        return None
    if (
        identity.component_id != "runner-mcp"
        or identity.build_version != loaded_version
        or identity.source_revision is None
        or identity.artifact_digest is None
    ):
        return None
    return identity.source_revision


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

def bounded_build_identity_payload(
    provider: Callable[[], BuildIdentity] | None,
) -> dict[str, object]:
    """Return an explicit unverified result when build identity cannot be proved.

    A provider failure must never become a raw MCP tool exception or a guessed
    build/source revision. The normal proven identity schema is unchanged.
    """

    unavailable: dict[str, object] = {
        "schemaVersion": "runner-mcp/build-identity-unavailable/v1",
        "state": "unavailable",
        "reasonCode": "build-identity-unavailable",
        "identityEvidenceComplete": False,
    }
    if provider is None:
        return unavailable
    try:
        identity = provider()
        if not isinstance(identity, BuildIdentity):
            return unavailable
        payload = identity.to_payload()
        if not isinstance(payload, dict) or set(payload) != {
            "component_id",
            "build_version",
            "source_revision",
            "artifact_digest",
            "protocol_min",
            "protocol_max",
            "interface_schema_digest",
        }:
            return unavailable
        return payload
    except (OSError, RuntimeError, TypeError, ValueError):
        return unavailable
