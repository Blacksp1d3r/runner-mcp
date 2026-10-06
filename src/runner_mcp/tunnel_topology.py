from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from .onboarding import load_env_file

_MAX_BYTES = 4096
_INSTANCE_RE = re.compile(r"^[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REVISION_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,63}$")
_AUTHORITY = "aifordable-topology"
_MAX_TTL_SECONDS = 300
_FUTURE_SKEW_SECONDS = 30


class TunnelTopologyEvidenceError(RuntimeError):
    """Bounded topology-attestation failure without private identity detail."""


class TunnelTopologyState(StrEnum):
    ABSENT = "absent"
    QUALIFIED = "qualified"
    STALE = "stale"
    MISMATCH = "mismatch"
    NOT_UNIQUE = "not_unique"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class TunnelTopologyEvidence:
    state: TunnelTopologyState
    reason: str

    @property
    def qualified(self) -> bool:
        return self.state is TunnelTopologyState.QUALIFIED

    def public_dict(self) -> dict[str, str | bool]:
        return {
            "state": self.state.value,
            "reason": self.reason,
            "qualified": self.qualified,
        }


def collect_tunnel_topology_evidence(
    config_dir: Path,
    *,
    runtime_instance_id: str,
    now: datetime | None = None,
) -> TunnelTopologyEvidence:
    """Consume one external topology attestation and fail closed when it is stale."""

    _runtime_instance_id(runtime_instance_id)
    observed_now = datetime.now(UTC) if now is None else _utc(now)
    path = config_dir.expanduser().resolve() / "tunnel-topology-attestation.json"
    if not path.exists() and not path.is_symlink():
        return TunnelTopologyEvidence(
            TunnelTopologyState.ABSENT,
            "topology_attestation_absent",
        )

    try:
        payload = _read_private_json(path)
        _validate_shape(payload)
        observed_at = _timestamp(payload["observed_at"])
        expires_at = _timestamp(payload["expires_at"])
        if expires_at <= observed_at:
            raise TunnelTopologyEvidenceError("topology attestation is invalid")
        if (expires_at - observed_at).total_seconds() > _MAX_TTL_SECONDS:
            raise TunnelTopologyEvidenceError("topology attestation is invalid")
        if (observed_at - observed_now).total_seconds() > _FUTURE_SKEW_SECONDS:
            raise TunnelTopologyEvidenceError("topology attestation is invalid")
        if observed_now > expires_at:
            return TunnelTopologyEvidence(
                TunnelTopologyState.STALE,
                "topology_attestation_stale",
            )
        if payload["runtime_instance_id"] != runtime_instance_id:
            return TunnelTopologyEvidence(
                TunnelTopologyState.MISMATCH,
                "topology_runtime_mismatch",
            )
        if payload["tunnel_binding_sha256"] != _tunnel_binding(config_dir):
            return TunnelTopologyEvidence(
                TunnelTopologyState.MISMATCH,
                "topology_tunnel_mismatch",
            )
        if payload["active_client_count"] != 1 or payload["role"] != "primary":
            return TunnelTopologyEvidence(
                TunnelTopologyState.NOT_UNIQUE,
                "topology_not_unique_primary",
            )
        return TunnelTopologyEvidence(
            TunnelTopologyState.QUALIFIED,
            "topology_unique_primary",
        )
    except TunnelTopologyEvidenceError:
        return TunnelTopologyEvidence(
            TunnelTopologyState.INVALID,
            "topology_attestation_invalid",
        )


def _read_private_json(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise TunnelTopologyEvidenceError("topology attestation is unsafe")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TunnelTopologyEvidenceError("topology attestation is unavailable") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise TunnelTopologyEvidenceError("topology attestation is unsafe")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise TunnelTopologyEvidenceError("topology attestation is unsafe")
        if hasattr(os, "geteuid") and metadata.st_uid != os.geteuid():
            raise TunnelTopologyEvidenceError("topology attestation is unsafe")
        if metadata.st_size <= 0 or metadata.st_size > _MAX_BYTES:
            raise TunnelTopologyEvidenceError("topology attestation is invalid")
        raw = os.read(fd, _MAX_BYTES + 1)
    finally:
        os.close(fd)
    if len(raw) > _MAX_BYTES:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TunnelTopologyEvidenceError("topology attestation is invalid") from exc
    if not isinstance(value, dict):
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    return value


def _validate_shape(payload: dict[str, object]) -> None:
    expected = {
        "schema_version",
        "authority",
        "topology_revision",
        "runtime_instance_id",
        "tunnel_binding_sha256",
        "role",
        "active_client_count",
        "observed_at",
        "expires_at",
    }
    if set(payload) != expected:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    if payload["schema_version"] != 1 or payload["authority"] != _AUTHORITY:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    revision = payload["topology_revision"]
    if not isinstance(revision, str) or _REVISION_RE.fullmatch(revision) is None:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    _runtime_instance_id(payload["runtime_instance_id"])
    digest = payload["tunnel_binding_sha256"]
    if not isinstance(digest, str) or _DIGEST_RE.fullmatch(digest) is None:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    if payload["role"] not in {"primary", "standby"}:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    count = payload["active_client_count"]
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 16:
        raise TunnelTopologyEvidenceError("topology attestation is invalid")


def _tunnel_binding(config_dir: Path) -> str:
    try:
        values = load_env_file(config_dir.expanduser().resolve() / "tunnel.env")
        tunnel_id = values["CONTROL_PLANE_TUNNEL_ID"].strip()
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise TunnelTopologyEvidenceError("topology tunnel binding is unavailable") from exc
    if not re.fullmatch(r"tunnel_[0-9a-f]{32}", tunnel_id):
        raise TunnelTopologyEvidenceError("topology tunnel binding is unavailable")
    return hashlib.sha256(tunnel_id.encode("utf-8")).hexdigest()


def _runtime_instance_id(value: object) -> str:
    if not isinstance(value, str) or _INSTANCE_RE.fullmatch(value) is None:
        raise TunnelTopologyEvidenceError("runtime instance identity is invalid")
    return value


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TunnelTopologyEvidenceError("topology attestation is invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise TunnelTopologyEvidenceError("topology attestation is invalid") from exc
    return _utc(parsed)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TunnelTopologyEvidenceError("topology attestation time is invalid")
    return value.astimezone(UTC)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")
