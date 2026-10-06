from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from .tunnel_health_evidence import collect_tunnel_runtime_instance_id

_MAX_RESPONSE_BYTES = 4096
_INSTANCE_RE = re.compile(r"^[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REVISION_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,63}$")
_TUNNEL_ID_RE = re.compile(r"^tunnel_[0-9a-f]{32}$")


class TunnelTopologyRefreshError(RuntimeError):
    """Safe refresh failure without endpoint, credential or binding detail."""


def refresh_tunnel_topology_attestation(
    config_dir: Path,
    *,
    opener=urllib.request.urlopen,
    runtime_instance_collector=collect_tunnel_runtime_instance_id,
    now: datetime | None = None,
) -> dict[str, str | bool]:
    """Refresh private topology evidence through the existing AIfordable runner channel."""

    paths, _settings, _registry = _read_private_runtime(config_dir)
    values = _load_env_file(paths.env_file)
    try:
        origin, _subject, credential = _validate_agent_bus_relay_config(
            origin=values.get("RUNNER_FABRIC_RELAY_ORIGIN", ""),
            subject=values.get("RUNNER_FABRIC_RELAY_SUBJECT", ""),
            credential=values.get("RUNNER_FABRIC_RELAY_CREDENTIAL", ""),
        )
    except (RuntimeError, TypeError, ValueError) as exc:
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority configuration is unavailable"
        ) from exc

    instance_id = runtime_instance_collector(paths.config_dir)
    if not isinstance(instance_id, str) or _INSTANCE_RE.fullmatch(instance_id) is None:
        raise TunnelTopologyRefreshError(
            "tunnel runtime identity is unavailable"
        )
    tunnel_binding = _tunnel_binding(paths.config_dir)

    body = json.dumps(
        {
            "runtime_instance_id": instance_id,
            "tunnel_binding_sha256": tunnel_binding,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        origin + "/internal/topology/heartbeat",
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "runner-mcp-topology-refresh",
            "X-AIfordable-Runner-Credential": credential,
        },
        method="POST",
    )
    try:
        with opener(request, timeout=10.0) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read(_MAX_RESPONSE_BYTES + 1)
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority rejected the refresh"
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority is unavailable"
        ) from exc

    if status != 200 or len(raw) > _MAX_RESPONSE_BYTES:
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        )
    payload = _decode_attestation(
        raw,
        expected_instance_id=instance_id,
        expected_tunnel_binding=tunnel_binding,
        now=datetime.now(UTC) if now is None else _utc(now),
    )
    _persist_attestation(paths.config_dir, payload)

    result = _collect_tunnel_topology_evidence(
        paths.config_dir,
        runtime_instance_id=instance_id,
        now=now,
    )
    return result.public_dict()


def _decode_attestation(
    raw: bytes,
    *,
    expected_instance_id: str,
    expected_tunnel_binding: str,
    now: datetime,
) -> dict[str, object]:
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        ) from exc
    if not isinstance(payload, dict):
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        )
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
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        )
    revision = payload.get("topology_revision")
    count = payload.get("active_client_count")
    if (
        payload.get("schema_version") != 1
        or payload.get("authority") != "aifordable-topology"
        or not isinstance(revision, str)
        or _REVISION_RE.fullmatch(revision) is None
        or payload.get("runtime_instance_id") != expected_instance_id
        or payload.get("tunnel_binding_sha256") != expected_tunnel_binding
        or payload.get("role") not in {"primary", "standby"}
        or isinstance(count, bool)
        or not isinstance(count, int)
        or not 0 <= count <= 16
    ):
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        )
    observed_at = _timestamp(payload.get("observed_at"))
    expires_at = _timestamp(payload.get("expires_at"))
    if (
        expires_at <= observed_at
        or (expires_at - observed_at).total_seconds() > 300
        or (observed_at - now).total_seconds() > 30
        or now > expires_at
    ):
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned stale evidence"
        )
    return payload


def _persist_attestation(config_dir: Path, payload: dict[str, object]) -> None:
    path = config_dir.expanduser().resolve() / "tunnel-topology-attestation.json"
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if not raw or len(raw) > _MAX_RESPONSE_BYTES:
        raise TunnelTopologyRefreshError("topology evidence exceeds supported bounds")
    fd = -1
    temporary: Path | None = None
    try:
        fd, name = tempfile.mkstemp(
            prefix=".tunnel-topology-attestation-",
            dir=path.parent,
        )
        temporary = Path(name)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        _fsync_directory(path.parent)
    except OSError as exc:
        raise TunnelTopologyRefreshError(
            "topology evidence could not be persisted"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _tunnel_binding(config_dir: Path) -> str:
    try:
        values = _load_env_file(
            config_dir.expanduser().resolve() / "tunnel.env"
        )
        tunnel_id = values["CONTROL_PLANE_TUNNEL_ID"].strip()
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise TunnelTopologyRefreshError(
            "tunnel binding is unavailable"
        ) from exc
    if _TUNNEL_ID_RE.fullmatch(tunnel_id) is None:
        raise TunnelTopologyRefreshError("tunnel binding is unavailable")
    return hashlib.sha256(tunnel_id.encode("utf-8")).hexdigest()


def _read_private_runtime(config_dir: Path):
    from .onboarding import read_private_runtime

    return read_private_runtime(config_dir)


def _load_env_file(path: Path) -> dict[str, str]:
    from .onboarding import load_env_file

    return load_env_file(path)


def _validate_agent_bus_relay_config(
    *,
    origin: object,
    subject: object,
    credential: object,
) -> tuple[str, str, str]:
    from .agent_bus_worker import validate_agent_bus_relay_config

    return validate_agent_bus_relay_config(
        origin=origin,
        subject=subject,
        credential=credential,
    )


def _collect_tunnel_topology_evidence(
    config_dir: Path,
    *,
    runtime_instance_id: str,
    now: datetime | None,
):
    from .tunnel_topology import collect_tunnel_topology_evidence

    return collect_tunnel_topology_evidence(
        config_dir,
        runtime_instance_id=runtime_instance_id,
        now=now,
    )


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise TunnelTopologyRefreshError(
            "AIfordable topology authority returned invalid evidence"
        ) from exc
    return _utc(parsed)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TunnelTopologyRefreshError("topology timestamp is invalid")
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


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
