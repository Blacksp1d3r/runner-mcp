from __future__ import annotations

import hashlib
import json
import stat
import urllib.error
import urllib.request
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path

import pytest

from runner_mcp.tunnel_topology_refresh import (
    TunnelTopologyRefreshError,
    _NoTopologyRefreshRedirects,
    _open_topology_refresh_request,
    _topology_refresh_opener,
    bounded_tunnel_topology_refresh_reason,
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


@pytest.mark.parametrize(
    ("message", "reason"),
    [
        (
            "AIfordable topology authority configuration is unavailable",
            "authority_configuration_unavailable",
        ),
        ("tunnel runtime identity is unavailable", "runtime_identity_unavailable"),
        (
            "AIfordable topology authority rejected the refresh",
            "authority_rejected",
        ),
        (
            "AIfordable topology authority is unavailable",
            "authority_unavailable",
        ),
        (
            "AIfordable topology authority returned invalid evidence",
            "authority_invalid_evidence",
        ),
        (
            "AIfordable topology authority returned stale evidence",
            "authority_stale_evidence",
        ),
        ("topology evidence exceeds supported bounds", "evidence_oversized"),
        ("topology evidence could not be persisted", "evidence_persist_failed"),
        ("tunnel binding is unavailable", "tunnel_binding_unavailable"),
        ("topology timestamp is invalid", "timestamp_invalid"),
    ],
)
def test_bounded_refresh_reason_maps_only_known_safe_messages(
    message: str,
    reason: str,
) -> None:
    assert (
        bounded_tunnel_topology_refresh_reason(
            TunnelTopologyRefreshError(message)
        )
        == reason
    )

    assert (
        bounded_tunnel_topology_refresh_reason(
            TunnelTopologyRefreshError("private failure")
        )
        is None
    )


def test_topology_refresh_default_transport_bypasses_hostile_proxies(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.invalid:8888")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.invalid:8888")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.example.invalid:8888")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(
        urllib.request,
        "getproxies",
        lambda: pytest.fail("private topology refresh must not consult proxy environment"),
    )
    opener = _topology_refresh_opener()
    assert any(isinstance(h, _NoTopologyRefreshRedirects) for h in opener.handlers)
    assert not any(
        isinstance(h, urllib.request.HTTPRedirectHandler)
        and not isinstance(h, _NoTopologyRefreshRedirects)
        for h in opener.handlers
    )
    assert all(
        h.proxies == {} for h in opener.handlers
        if isinstance(h, urllib.request.ProxyHandler)
    )


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "destination",
    [
        "https://other.example.invalid/leak",
        "http://other.example.invalid/leak",
        "https://control.example.invalid/other-path",
    ],
)
def test_topology_refresh_redirect_never_forwards_private_header(
    status: int, destination: str
) -> None:
    request = urllib.request.Request(
        "https://control.example.invalid/internal/topology/heartbeat",
        data=b'{"synthetic":true}',
        headers={"X-AIfordable-Runner-Credential": "synthetic-credential"},
        method="POST",
    )
    assert _NoTopologyRefreshRedirects().redirect_request(
        request, None, status, "redirect", Message(), destination
    ) is None
    assert request.get_header("X-aifordable-runner-credential") == "synthetic-credential"
    assert request.full_url == (
        "https://control.example.invalid/internal/topology/heartbeat"
    )


def test_fixed_topology_refresh_opens_only_private_opener(monkeypatch) -> None:
    calls = []

    class TrackingOpener:
        def open(self, request, *, timeout):
            calls.append((request, timeout))
            return "synthetic-result"

    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._topology_refresh_opener",
        lambda: TrackingOpener(),
    )
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: pytest.fail("urlopen must not be used"),
    )
    request = urllib.request.Request(
        "https://control.example.invalid/internal/topology/heartbeat",
        data=b'{}',
        method="POST",
    )
    assert _open_topology_refresh_request(request, timeout=10) == "synthetic-result"
    assert calls == [(request, 10)]


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_default_refresh_redirect_refusal_is_bounded_and_does_not_replace_evidence(
    tmp_path: Path, monkeypatch, code: int
) -> None:
    root = private_config(tmp_path)
    existing = root / "tunnel-topology-attestation.json"
    existing.write_bytes(attestation())
    existing.chmod(0o600)
    baseline = existing.read_bytes()
    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._read_private_runtime",
        lambda path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(),
            object(),
        ),
    )
    calls = []

    class RejectingOpener:
        def open(self, request, *, timeout):
            calls.append(request.full_url)
            raise urllib.error.HTTPError(
                request.full_url,
                code,
                "redirect",
                {"Location": "https://other.example.invalid/leak"},
                None,
            )

    monkeypatch.setattr(
        "runner_mcp.tunnel_topology_refresh._topology_refresh_opener",
        lambda: RejectingOpener(),
    )
    with pytest.raises(
        TunnelTopologyRefreshError, match="rejected the refresh"
    ) as caught:
        refresh_tunnel_topology_attestation(
            root,
            runtime_instance_collector=lambda _path: INSTANCE,
            now=NOW,
        )
    assert len(calls) == 1
    assert existing.read_bytes() == baseline
    assert "other.example.invalid" not in str(caught.value)
    assert "r" * 48 not in str(caught.value)


@pytest.mark.parametrize(
    ("reason", "message", "bounded"),
    [
        ("health_url_missing", "tunnel health URL is missing", "health_url_missing"),
        ("health_endpoint_unreachable", "tunnel health endpoint is unreachable", "health_endpoint_unreachable"),
        ("health_schema_incompatible", "tunnel health schema is incompatible", "health_schema_incompatible"),
        ("runtime_identity_invalid", "tunnel runtime identity is invalid", "runtime_identity_invalid"),
    ],
)
def test_default_topology_refresh_preserves_first_failed_local_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    message: str,
    bounded: str,
) -> None:
    import runner_mcp.tunnel_topology_refresh as module

    root = private_config(tmp_path)
    monkeypatch.setattr(
        module, "_read_private_runtime",
        lambda _path: (
            type("Paths", (), {"config_dir": root, "env_file": root / "runner.env"})(),
            object(), object(),
        ),
    )
    monkeypatch.setattr(
        module, "inspect_tunnel_runtime_instance_id",
        lambda _root: (None, reason),
    )
    with pytest.raises(TunnelTopologyRefreshError, match=message) as error:
        refresh_tunnel_topology_attestation(
            root,
            opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("missing local identity must not send credential")
            ),
        )
    assert bounded_tunnel_topology_refresh_reason(error.value) == bounded
