from __future__ import annotations

import hashlib
import json
import stat
import urllib.error
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.tunnel_topology_refresh import (
    TunnelTopologyRefreshError,
    refresh_tunnel_topology_attestation,
)

INSTANCE = "a" * 32
TUNNEL_ID = "tunnel_" + ("b" * 32)
BINDING = hashlib.sha256(TUNNEL_ID.encode()).hexdigest()
NOW = datetime(2026, 10, 6, 9, 50, tzinfo=UTC)


class FakeResponse:
    def __init__(self, payload: bytes, *, status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._payload


def private_config(tmp_path: Path) -> Path:
    tmp_path.chmod(0o700)
    env = tmp_path / "runner.env"
    env.write_text(
        "RUNNER_FABRIC_RELAY_ORIGIN=https://control.example.invalid\n"
        "RUNNER_FABRIC_RELAY_SUBJECT=runner:aifordable-lab\n"
        "RUNNER_FABRIC_RELAY_CREDENTIAL=" + ("r" * 48) + "\n",
        encoding="utf-8",
    )
    env.chmod(0o600)
    tunnel_env = tmp_path / "tunnel.env"
    tunnel_env.write_text(
        "CONTROL_PLANE_TUNNEL_ID=" + TUNNEL_ID + "\n"
        "CONTROL_PLANE_API_KEY=" + ("k" * 48) + "\n",
        encoding="utf-8",
    )
    tunnel_env.chmod(0o600)
    return tmp_path


def attestation(*, count: int = 1, role: str = "primary") -> bytes:
    return json.dumps(
        {
            "schema_version": 1,
            "authority": "aifordable-topology",
            "topology_revision": "topology:2026-10-06:1",
            "runtime_instance_id": INSTANCE,
            "tunnel_binding_sha256": BINDING,
            "role": role,
            "active_client_count": count,
            "observed_at": "2026-10-06T09:50:00Z",
            "expires_at": "2026-10-06T09:50:30Z",
        }
    ).encode()


def test_refresh_posts_private_binding_and_persists_only_valid_attestation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = private_config(tmp_path)
    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._read_private_runtime",
        lambda path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(),
            object(),
        ),
    )
    captured = {}

    def opener(request, *, timeout):
        captured["url"] = request.full_url
        captured["credential"] = request.get_header(
            "X-aifordable-runner-credential"
        )
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(attestation())

    result = refresh_tunnel_topology_attestation(
        root,
        opener=opener,
        runtime_instance_collector=lambda _path: INSTANCE,
        now=NOW,
    )

    assert result == {
        "state": "qualified",
        "reason": "topology_unique_primary",
        "qualified": True,
    }
    assert captured == {
        "url": "https://control.example.invalid/internal/topology/heartbeat",
        "credential": "r" * 48,
        "body": {
            "runtime_instance_id": INSTANCE,
            "tunnel_binding_sha256": BINDING,
        },
        "timeout": 10.0,
    }
    path = root / "tunnel-topology-attestation.json"
    assert path.is_file()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(
        attestation()
    )


def test_refresh_returns_not_unique_without_exposing_private_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = private_config(tmp_path)
    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._read_private_runtime",
        lambda path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(),
            object(),
        ),
    )

    result = refresh_tunnel_topology_attestation(
        root,
        opener=lambda request, timeout: FakeResponse(attestation(count=2)),
        runtime_instance_collector=lambda _path: INSTANCE,
        now=NOW,
    )

    rendered = json.dumps(result)
    assert result == {
        "state": "not_unique",
        "reason": "topology_not_unique_primary",
        "qualified": False,
    }
    assert INSTANCE not in rendered
    assert BINDING not in rendered
    assert TUNNEL_ID not in rendered
    assert "control.example.invalid" not in rendered


@pytest.mark.parametrize(
    "payload",
    [
        b"{}",
        attestation(role="standby").replace(b'"standby"', b'"invalid"'),
        attestation().replace(INSTANCE.encode(), ("c" * 32).encode()),
        attestation().replace(BINDING.encode(), ("d" * 64).encode()),
        attestation().replace(
            b'"expires_at": "2026-10-06T09:50:30Z"',
            b'"expires_at": "2026-10-06T10:00:00Z"',
        ),
    ],
)
def test_invalid_response_never_replaces_existing_evidence(
    tmp_path: Path,
    monkeypatch,
    payload: bytes,
) -> None:
    root = private_config(tmp_path)
    existing = root / "tunnel-topology-attestation.json"
    existing.write_bytes(attestation())
    existing.chmod(0o600)
    before = existing.read_bytes()
    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._read_private_runtime",
        lambda path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(),
            object(),
        ),
    )

    with pytest.raises(TunnelTopologyRefreshError):
        refresh_tunnel_topology_attestation(
            root,
            opener=lambda request, timeout: FakeResponse(payload),
            runtime_instance_collector=lambda _path: INSTANCE,
            now=NOW,
        )

    assert existing.read_bytes() == before


def test_authority_http_error_is_secret_free(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = private_config(tmp_path)
    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._read_private_runtime",
        lambda path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(),
            object(),
        ),
    )

    def opener(request, *, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            503,
            "unavailable",
            {},
            None,
        )

    with pytest.raises(
        TunnelTopologyRefreshError,
        match="rejected the refresh",
    ) as caught:
        refresh_tunnel_topology_attestation(
            root,
            opener=opener,
            runtime_instance_collector=lambda _path: INSTANCE,
            now=NOW,
        )

    rendered = str(caught.value)
    assert INSTANCE not in rendered
    assert BINDING not in rendered
    assert TUNNEL_ID not in rendered
    assert "control.example.invalid" not in rendered
