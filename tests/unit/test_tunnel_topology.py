from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.tunnel_topology import (
    TunnelTopologyState,
    collect_tunnel_topology_evidence,
)

INSTANCE = "a" * 32
TUNNEL_ID = "tunnel_" + "b" * 32
NOW = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)


def private_config(tmp_path: Path) -> Path:
    tmp_path.chmod(0o700)
    env = tmp_path / "tunnel.env"
    env.write_text(
        "CONTROL_PLANE_TUNNEL_ID=" + TUNNEL_ID + "\n"
        "CONTROL_PLANE_API_KEY=" + ("k" * 48) + "\n",
        encoding="utf-8",
    )
    env.chmod(0o600)
    return tmp_path


def write_attestation(
    root: Path,
    *,
    instance_id: str = INSTANCE,
    active_clients: int = 1,
    role: str = "primary",
    observed_at: str = "2026-10-06T07:59:00Z",
    expires_at: str = "2026-10-06T08:03:00Z",
) -> Path:
    payload = {
        "schema_version": 1,
        "authority": "aifordable-topology",
        "topology_revision": "topology:2026-10-06:1",
        "runtime_instance_id": instance_id,
        "tunnel_binding_sha256": hashlib.sha256(TUNNEL_ID.encode()).hexdigest(),
        "role": role,
        "active_client_count": active_clients,
        "observed_at": observed_at,
        "expires_at": expires_at,
    }
    path = root / "tunnel-topology-attestation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path


def test_absent_attestation_is_not_qualified(tmp_path: Path) -> None:
    root = private_config(tmp_path)

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is TunnelTopologyState.ABSENT
    assert result.qualified is False


def test_fresh_unique_primary_attestation_is_qualified(tmp_path: Path) -> None:
    root = private_config(tmp_path)
    write_attestation(root)

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is TunnelTopologyState.QUALIFIED
    assert result.public_dict() == {
        "state": "qualified",
        "reason": "topology_unique_primary",
        "qualified": True,
    }


@pytest.mark.parametrize(
    ("kwargs", "state", "reason"),
    [
        (
            {"expires_at": "2026-10-06T07:59:30Z"},
            TunnelTopologyState.STALE,
            "topology_attestation_stale",
        ),
        (
            {"instance_id": "c" * 32},
            TunnelTopologyState.MISMATCH,
            "topology_runtime_mismatch",
        ),
        (
            {"active_clients": 2},
            TunnelTopologyState.NOT_UNIQUE,
            "topology_not_unique_primary",
        ),
        (
            {"role": "standby"},
            TunnelTopologyState.NOT_UNIQUE,
            "topology_not_unique_primary",
        ),
    ],
)
def test_attestation_fails_closed_by_reason(
    tmp_path: Path,
    kwargs: dict,
    state: TunnelTopologyState,
    reason: str,
) -> None:
    root = private_config(tmp_path)
    write_attestation(root, **kwargs)

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is state
    assert result.reason == reason
    assert result.qualified is False


def test_tunnel_binding_mismatch_is_not_qualified(tmp_path: Path) -> None:
    root = private_config(tmp_path)
    path = write_attestation(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["tunnel_binding_sha256"] = "d" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is TunnelTopologyState.MISMATCH
    assert result.reason == "topology_tunnel_mismatch"


def test_overlong_validity_window_is_invalid(tmp_path: Path) -> None:
    root = private_config(tmp_path)
    write_attestation(
        root,
        observed_at="2026-10-06T07:55:00Z",
        expires_at="2026-10-06T08:05:01Z",
    )

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is TunnelTopologyState.INVALID


@pytest.mark.parametrize("mode", [0o644, 0o666])
def test_attestation_requires_private_permissions(
    tmp_path: Path,
    mode: int,
) -> None:
    root = private_config(tmp_path)
    path = write_attestation(root)
    path.chmod(mode)

    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    assert result.state is TunnelTopologyState.INVALID


def test_attestation_never_renders_private_ids(tmp_path: Path) -> None:
    root = private_config(tmp_path)
    write_attestation(root)
    result = collect_tunnel_topology_evidence(
        root,
        runtime_instance_id=INSTANCE,
        now=NOW,
    )

    rendered = json.dumps(result.public_dict())
    assert INSTANCE not in rendered
    assert TUNNEL_ID not in rendered
    assert hashlib.sha256(TUNNEL_ID.encode()).hexdigest() not in rendered
    assert "CONTROL_PLANE_API_KEY" not in rendered
