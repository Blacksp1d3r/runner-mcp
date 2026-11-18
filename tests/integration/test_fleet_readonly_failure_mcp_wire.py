"""#590: verify actual MCP response shapes for read-only Fleet diagnostics.

This is an in-process authenticated HTTP/MCP test. It does not prove the
24/7 host's installed wheel, Fabric peer, rollback watchdog or transport ACK.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.fabric_bridge import FabricBridgeError
from runner_mcp.fabric_update import FabricUpdateError
from runner_mcp.server import Settings, create_app


def _app(tmp_path: Path, *, with_fabric: bool):
    source = tmp_path / "synthetic-project"
    source.mkdir()
    extra: dict[str, object] = {}
    if with_fabric:
        extra.update(
            fabric_resource_url="http://127.0.0.1:9010/mcp",
            fabric_bearer_token="f" * 32,
        )
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
        **extra,
    )
    registry = ProjectRegistry(projects={
        "demo": ProjectConfig(
            display_name="Demo", repository="example/demo", root=source,
        ),
    })
    return create_app(settings=settings, registry=registry)


def _headers(client: TestClient) -> dict[str, str]:
    headers = {
        "Authorization": "Bearer " + "x" * 32,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    initial = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "readiness-wire-regression", "version": "1"},
        },
    })
    assert initial.status_code == 200
    headers["Mcp-Session-Id"] = initial.headers["mcp-session-id"]
    notified = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
    })
    assert notified.status_code == 202
    return headers


def _tool(client: TestClient, headers: dict[str, str], name: str, **args):
    response = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 17, "method": "tools/call",
        "params": {"name": name, "arguments": args},
    })
    assert response.status_code == 200
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert len(events) == 1
    event = events[0]
    assert event["id"] == 17
    assert "error" not in event
    result = event["result"]
    assert result["isError"] is False
    assert len(result["content"]) >= 1
    return json.loads(result["content"][0]["text"]), response.text


@pytest.mark.parametrize(
    ("method", "source"),
    [
        ("fabric_update_readiness", "github-actions"),
        ("fabric_local_update_readiness", "local-custody"),
    ],
)
@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        ("fabric_launcher_unmanaged", "fabric_launcher_unmanaged"),
        ("artifact_metadata_unavailable", "artifact_metadata_unavailable"),
        ("internal /private/path bearer-secret", "fabric_update_readiness_unavailable"),
    ],
)
def test_update_preflight_failure_is_mcp_blocked_not_an_exception(
    tmp_path: Path, monkeypatch, method: str, source: str,
    failure: str, expected: str,
) -> None:
    class ReadOnlyManager:
        def __init__(self, **_kwargs) -> None:
            pass

        def readiness(self, _commit: str):
            raise FabricUpdateError(failure)

        def local_readiness(self, _commit: str):
            raise FabricUpdateError(failure)

        def start(self, _commit: str):
            raise AssertionError("read-only preflight must never start an update")

        def start_local(self, _commit: str):
            raise AssertionError("read-only preflight must never start an update")

    monkeypatch.setattr("runner_mcp.server.FabricUpdateManager", ReadOnlyManager)
    app = _app(tmp_path, with_fabric=False)
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        payload, wire = _tool(
            client, _headers(client), method, commit="a" * 40,
        )
    assert payload == {
        "state": "blocked",
        "reasonCode": expected,
        "artifact_ready": False,
        "source": source,
    }
    assert "bearer-secret" not in wire
    assert "/private/path" not in wire
    assert "a" * 40 not in repr(payload)


@pytest.mark.parametrize(
    ("method", "source"),
    [
        ("fabric_update_readiness", "github-actions"),
        ("fabric_local_update_readiness", "local-custody"),
    ],
)
def test_update_preflight_success_is_not_changed(
    tmp_path: Path, monkeypatch, method: str, source: str,
) -> None:
    class ReadOnlyManager:
        def __init__(self, **_kwargs) -> None:
            pass

        def readiness(self, commit: str):
            return {"commit": commit, "artifact_ready": True}

        def local_readiness(self, commit: str):
            return {"commit": commit, "artifact_ready": True, "source": "local-custody"}

        def start(self, _commit: str):
            raise AssertionError("readiness must never call start")

        def start_local(self, _commit: str):
            raise AssertionError("readiness must never call start_local")

    monkeypatch.setattr("runner_mcp.server.FabricUpdateManager", ReadOnlyManager)
    app = _app(tmp_path, with_fabric=False)
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        payload, _wire = _tool(
            client, _headers(client), method, commit="a" * 40,
        )
    assert payload == {
        "commit": "a" * 40,
        "artifact_ready": True,
        **({"source": source} if source == "local-custody" else {}),
    }


@pytest.mark.parametrize(
    ("reason", "code"),
    [
        ("Runner Fabric CI guest request failed", "ci_guest_status_unavailable"),
        ("Runner Fabric returned invalid CI guest result", "ci_guest_status_invalid_payload"),
        ("/private/key should never be displayed", "ci_guest_status_unavailable"),
    ],
)
def test_optional_ci_guest_status_is_unknown_on_mcp_wire(
    tmp_path: Path, monkeypatch, reason: str, code: str,
) -> None:
    class MissingOptionalFabricCapability:
        def __init__(self, _config) -> None:
            pass

        def ci_runner_guest_status(self):
            raise FabricBridgeError(reason)

        def ci_runner_guest_start(self):
            raise AssertionError("status must not start the guest")

        def ci_runner_guest_enroll(self, _handoff_id):
            raise AssertionError("status must not enroll the guest")

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient", MissingOptionalFabricCapability,
    )
    app = _app(tmp_path, with_fabric=True)
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        payload, wire = _tool(
            client, _headers(client), "fabric_ci_runner_guest_status",
        )
    assert payload == {
        "schema_version": "runner-mcp/fabric-ci-guest-status-error/v1",
        "state": "unavailable",
        "reason_code": code,
        "guest_registered": None,
        "guest_running": None,
        "mutation_enabled": False,
        "execution_enabled": False,
    }
    assert "/private" not in wire
    assert "should never be displayed" not in wire
