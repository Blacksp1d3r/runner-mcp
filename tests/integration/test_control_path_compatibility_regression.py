from __future__ import annotations

import json
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app

EXPECTED_PROTOCOL = "2025-11-25"
STALE_CLIENT_REQUIRED_TOOL = "fabric_run_work_unit"


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer " + ("x" * 32),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def _initialize_message() -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": EXPECTED_PROTOCOL,
            "capabilities": {},
            "clientInfo": {
                "name": "fleet-update-a1-stale-client",
                "version": "0.1.3",
            },
        },
    }


def _event(response) -> dict[str, object]:
    line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _connect_and_list(client: TestClient) -> tuple[dict[str, object], set[str]]:
    headers = _headers()
    initialized = client.post("/mcp", headers=headers, json=_initialize_message())
    assert initialized.status_code == 200
    init_event = _event(initialized)
    session_id = initialized.headers.get("mcp-session-id")
    assert session_id

    headers["Mcp-Session-Id"] = session_id
    notified = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        },
    )
    assert notified.status_code == 202

    listed = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        },
    )
    assert listed.status_code == 200
    listed_event = _event(listed)
    tools = listed_event["result"]["tools"]
    return init_event, {tool["name"] for tool in tools}


def _app(tmp_path: Path, *, fabric_enabled: bool):
    project_root = tmp_path / ("project-new" if fabric_enabled else "project-old")
    project_root.mkdir()
    kwargs: dict[str, object] = {}
    if fabric_enabled:
        kwargs.update(
            fabric_resource_url="http://127.0.0.1:9010/mcp",
            fabric_bearer_token="f" * 32,
        )
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / ("audit-new.jsonl" if fabric_enabled else "audit-old.jsonl"),
        rate_limit_per_minute=60,
        **kwargs,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=project_root,
            )
        }
    )
    return create_app(settings=settings, registry=registry)


def test_historical_stale_tool_catalog_is_an_interface_schema_break(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A1 characterization: MCP negotiation can stay green while a cached tool surface is stale.

    This reproduces the already-observed failure class where a client session opened before a
    Runner-MCP/Fabric tool-surface change keeps an older tool catalogue. The transport and MCP
    protocol negotiation still succeed, but a tool required after the change is absent from the
    stale client's catalogue. The correct failure layer is therefore interface_schema, not
    transport or protocol_version.

    No production component is mutated by this test.
    """

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

    monkeypatch.setattr("runner_mcp.server.FabricBridgeClient", FakeFabricBridge)

    old_app = _app(tmp_path, fabric_enabled=False)
    with TestClient(old_app, base_url="https://mcp.example.invalid") as old_client:
        old_init, cached_tools = _connect_and_list(old_client)

    new_app = _app(tmp_path, fabric_enabled=True)
    with TestClient(new_app, base_url="https://mcp.example.invalid") as new_client:
        new_init, current_tools = _connect_and_list(new_client)

    assert old_init["result"]["protocolVersion"] == EXPECTED_PROTOCOL
    assert new_init["result"]["protocolVersion"] == EXPECTED_PROTOCOL

    assert STALE_CLIENT_REQUIRED_TOOL not in cached_tools
    assert STALE_CLIENT_REQUIRED_TOOL in current_tools

    failure_layer = (
        "interface_schema"
        if STALE_CLIENT_REQUIRED_TOOL not in cached_tools
        and STALE_CLIENT_REQUIRED_TOOL in current_tools
        else "unknown"
    )
    assert failure_layer == "interface_schema"

    # A1 deliberately records the current gap: successful MCP negotiation alone cannot tell the
    # stale peer that its cached tool surface is no longer sufficient. A4 will add explicit
    # interface compatibility/handshake evidence; this characterization remains as regression
    # coverage for the historical incident class.
    assert old_init["result"]["protocolVersion"] == new_init["result"]["protocolVersion"]
