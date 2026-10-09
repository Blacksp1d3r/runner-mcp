from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest

from runner_mcp.tunnel_health_evidence import (
    MAX_HEALTH_RESPONSE_BYTES,
    TunnelHealthEvidenceError,
    collect_control_plane_authenticated,
    collect_local_mcp_ready,
    collect_tunnel_runtime_instance_id,
)


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, limit: int) -> bytes:
        assert limit == MAX_HEALTH_RESPONSE_BYTES + 1
        return self.payload


def _write_health_url(config_dir: Path, value: str) -> Path:
    path = config_dir / "tunnel-health.url"
    path.write_text(value, encoding="utf-8")
    path.chmod(0o600)
    return path


def _payload(*, status: str = "ok", state: str = "initialized") -> bytes:
    return json.dumps(
        {
            "schema_version": 1,
            "snapshot_at": "2026-10-05T18:00:00Z",
            "component": "mcp",
            "status": status,
            "state": state,
        }
    ).encode("utf-8")


def test_missing_health_evidence_is_not_ready(tmp_path: Path) -> None:
    called: list[bool] = []

    assert collect_local_mcp_ready(
        tmp_path,
        opener=lambda *_args, **_kwargs: called.append(True),
    ) is False
    assert called == []


def test_collects_bounded_runtime_instance_id(tmp_path: Path) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    payload = json.dumps(
        {
            "schema_version": 1,
            "live": True,
            "ready": True,
            "runtime": {
                "instance_id": "a" * 32,
                "version": "0.0.15",
                "flavor": "full",
            },
        }
    ).encode("utf-8")
    requests = []

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(payload)

    assert collect_tunnel_runtime_instance_id(
        tmp_path,
        opener=opener,
    ) == "a" * 32
    request, timeout = requests[0]
    assert request.full_url == "http://127.0.0.1:48123/health?details=true"
    assert timeout == 2.0


@pytest.mark.parametrize(
    "instance_id",
    [None, "", "A" * 32, "g" * 32, "a" * 31],
)
def test_invalid_runtime_instance_id_is_not_evidence(
    tmp_path: Path,
    instance_id,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    payload = json.dumps(
        {
            "schema_version": 1,
            "runtime": {"instance_id": instance_id},
        }
    ).encode("utf-8")

    assert collect_tunnel_runtime_instance_id(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(payload),
    ) is None


@pytest.mark.parametrize("state", ["initialized", "discovered"])
def test_fixed_loopback_mcp_ok_state_is_ready(
    tmp_path: Path,
    state: str,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    requests = []

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(_payload(state=state))

    assert collect_local_mcp_ready(tmp_path, opener=opener) is True
    assert len(requests) == 1
    request, timeout = requests[0]
    assert request.full_url == "http://127.0.0.1:48123/health/mcp"
    assert request.method == "GET"
    assert timeout == 2.0


@pytest.mark.parametrize("probe_state", ["succeeded", "auth_required"])
def test_http_startup_probe_proves_local_mcp_reachability(
    tmp_path: Path,
    probe_state: str,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    payload = json.dumps(
        {
            "schema_version": 1,
            "component": "mcp",
            "status": "unknown",
            "state": "not_observed",
            "details": {
                "transport": "http-streamable",
                "startup_probe": {
                    "state": probe_state,
                    "observed_at": "2026-10-05T18:00:00Z",
                },
            },
        }
    ).encode("utf-8")

    assert collect_local_mcp_ready(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(payload),
    ) is True


@pytest.mark.parametrize("probe_state", ["pending", "timed_out", "failed"])
def test_http_startup_nonproof_does_not_claim_local_mcp_ready(
    tmp_path: Path,
    probe_state: str,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    payload = json.dumps(
        {
            "schema_version": 1,
            "component": "mcp",
            "status": "unknown",
            "state": "not_observed",
            "details": {
                "transport": "http-streamable",
                "startup_probe": {
                    "state": probe_state,
                },
            },
        }
    ).encode("utf-8")

    assert collect_local_mcp_ready(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(payload),
    ) is False


@pytest.mark.parametrize(
    ("status", "state"),
    [
        ("unknown", "not_observed"),
        ("degraded", "initialized"),
        ("ok", "not_observed"),
        ("ok", "failed"),
    ],
)
def test_nonproven_mcp_health_never_claims_ready(
    tmp_path: Path,
    status: str,
    state: str,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")

    assert collect_local_mcp_ready(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(
            _payload(status=status, state=state)
        ),
    ) is False


def test_control_plane_successful_poll_is_authenticated(
    tmp_path: Path,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    requests = []
    payload = json.dumps(
        {
            "schema_version": 1,
            "component": "control-plane",
            "status": "ok",
            "state": "polling",
            "details": {
                "last_success": "2026-10-05T18:00:00Z",
                "consecutive_failures": 0,
            },
        }
    ).encode("utf-8")

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(payload)

    assert collect_control_plane_authenticated(
        tmp_path,
        opener=opener,
    ) is True
    request, timeout = requests[0]
    assert request.full_url == "http://127.0.0.1:48123/health/control-plane"
    assert timeout == 2.0


@pytest.mark.parametrize(
    "payload",
    [
        {
            "schema_version": 1,
            "component": "control-plane",
            "status": "unknown",
            "state": "starting",
            "details": {},
        },
        {
            "schema_version": 1,
            "component": "control-plane",
            "status": "degraded",
            "state": "backoff",
            "details": {
                "last_success": "2026-10-05T18:00:00Z",
            },
        },
        {
            "schema_version": 1,
            "component": "control-plane",
            "status": "ok",
            "state": "stopped",
            "details": {
                "last_success": "2026-10-05T18:00:00Z",
            },
        },
        {
            "schema_version": 1,
            "component": "control-plane",
            "status": "ok",
            "state": "idle",
            "details": {},
        },
    ],
)
def test_control_plane_nonproof_never_claims_authenticated(
    tmp_path: Path,
    payload: dict,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")

    assert collect_control_plane_authenticated(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(
            json.dumps(payload).encode("utf-8")
        ),
    ) is False


def test_network_failure_is_not_ready(tmp_path: Path) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")

    def opener(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    assert collect_local_mcp_ready(tmp_path, opener=opener) is False


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:48123",
        "http://example.com:48123",
        "http://localhost:48123",
        "http://[::1]:48123",
        "http://127.0.0.1:48123/private",
        "http://user:pass@127.0.0.1:48123",
        "http://127.0.0.1",
    ],
)
def test_health_evidence_url_must_be_fixed_loopback_base(
    tmp_path: Path,
    value: str,
) -> None:
    _write_health_url(tmp_path, value)
    called: list[bool] = []

    with pytest.raises(TunnelHealthEvidenceError):
        collect_local_mcp_ready(
            tmp_path,
            opener=lambda *_args, **_kwargs: called.append(True),
        )

    assert called == []


def test_symlink_health_evidence_is_rejected(tmp_path: Path) -> None:
    referent = tmp_path / "foreign"
    referent.write_text("http://127.0.0.1:48123", encoding="utf-8")
    (tmp_path / "tunnel-health.url").symlink_to(referent)

    with pytest.raises(TunnelHealthEvidenceError, match="unsafe"):
        collect_local_mcp_ready(tmp_path)


def test_health_evidence_requires_private_mode(tmp_path: Path) -> None:
    path = _write_health_url(tmp_path, "http://127.0.0.1:48123")
    path.chmod(0o644)

    with pytest.raises(TunnelHealthEvidenceError, match="permissions"):
        collect_local_mcp_ready(tmp_path)


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json",
        b'{"schema_version":1,"component":"mcp","status":"ok","state":"initialized","state":"discovered"}',
        b"[]",
    ],
)
def test_invalid_health_payload_fails_closed(
    tmp_path: Path,
    payload: bytes,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")

    with pytest.raises(TunnelHealthEvidenceError, match="response is invalid"):
        collect_local_mcp_ready(
            tmp_path,
            opener=lambda *_args, **_kwargs: FakeResponse(payload),
        )


@pytest.mark.parametrize("negative_status", ["degraded", "error", "failed", "stopped"])
@pytest.mark.parametrize("prior_probe", ["succeeded", "auth_required"])
def test_explicit_negative_mcp_health_overrides_historical_startup(
    tmp_path: Path, negative_status: str, prior_probe: str,
) -> None:
    _write_health_url(tmp_path, "http://127.0.0.1:48123")
    payload = json.dumps({
        "schema_version": 1,
        "component": "mcp",
        "status": negative_status,
        "state": "not_observed",
        "details": {
            "transport": "http-streamable",
            "startup_probe": {"state": prior_probe},
        },
    }).encode("utf-8")
    assert collect_local_mcp_ready(
        tmp_path,
        opener=lambda *_args, **_kwargs: FakeResponse(payload),
    ) is False
