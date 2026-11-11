"""#540: announced MCP tools/list schema must match active build identity digest.

Only a locally isolated authenticated ASGI client; not live fleet/catalogue proof.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app

_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _mcp_event(response, *, request_id: int):
    matches = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert len(matches) == 1
    event = matches[0]
    assert event["jsonrpc"] == "2.0"
    assert type(event["id"]) is int
    assert event["id"] == request_id
    assert "error" not in event
    return event["result"]


def test_installed_build_identity_schema_digest_matches_advertised_tool_catalogue(
    tmp_path: Path,
) -> None:
    source = tmp_path / "project"
    source.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
    )
    registry = ProjectRegistry(projects={
        "demo": ProjectConfig(
            display_name="Demo", repository="example/demo", root=source,
        ),
    })
    app = create_app(settings=settings, registry=registry)
    headers = {
        "Authorization": "Bearer " + "x" * 32,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        init = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "catalogue-digest-test", "version": "1"},
            },
        })
        assert init.status_code == 200
        headers["Mcp-Session-Id"] = init.headers["mcp-session-id"]
        ready = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "method": "notifications/initialized",
            "params": {},
        })
        assert ready.status_code == 202
        listed = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {},
        })
        assert listed.status_code == 200
        advertised = _mcp_event(listed, request_id=2)["tools"]
        assert 1 <= len(advertised) <= 512
        names = [tool["name"] for tool in advertised]
        assert len(names) == len(set(names))
        assert {"build_identity", "runtime_status", "runtime_doctor",
                "fabric_coding_availability_preflight"}.issubset(set(names))
        identity_response = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "build_identity", "arguments": {}},
        })
        assert identity_response.status_code == 200
        result = _mcp_event(identity_response, request_id=3)
        assert result["isError"] is False
        identity = json.loads(result["content"][0]["text"])

    digest = identity["interface_schema_digest"]
    assert isinstance(digest, str)
    assert _DIGEST.fullmatch(digest)
    canonical = [
        {
            "name": tool["name"],
            "input_schema": tool["inputSchema"],
            "output_schema": tool.get("outputSchema"),
        }
        for tool in sorted(advertised, key=lambda x: x["name"])
    ]
    calculated = hashlib.sha256(json.dumps(
        canonical, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()
    assert digest == calculated
    assert "x" * 32 not in repr(identity)
    assert str(tmp_path) not in repr(identity)
