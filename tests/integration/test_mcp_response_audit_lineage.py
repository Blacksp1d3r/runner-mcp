"""#590: one real MCP session preserves HTTP, JSON-RPC and audit lineage.

Synthetic local ASGI only.  This proves no deployed tunnel, host or worker.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app

_REQUEST_ID = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
_TRACEPARENT = re.compile(r"^00-[0-9a-f]{32}-[0-9a-f]{16}-01$")
_SECRET = "never-expose-secret"
_SOURCE_TRACE = "4" * 32


def _payload(response) -> dict[str, object]:
    frames = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert len(frames) == 1
    result = frames[0]["result"]
    assert result.get("isError") is False
    return json.loads(result["content"][0]["text"])


def test_one_authenticated_session_correlates_success_and_degraded_response(
    tmp_path: Path, monkeypatch,
) -> None:
    # Corrupt the *local synthetic* status manager, not any installed worker.
    def synthetic_status_failure(_self):
        raise RuntimeError(f"/private/{_SECRET}/self-update")

    monkeypatch.setattr(
        "runner_mcp.server.SelfUpdateManager.runtime_status",
        synthetic_status_failure,
    )
    root = tmp_path / "project"
    root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
    )
    registry = ProjectRegistry(
        projects={"demo": ProjectConfig(
            display_name="Demo", repository="example/demo", root=root,
        )},
    )
    app = create_app(settings=settings, registry=registry)
    headers = {
        "Authorization": "Bearer " + "x" * 32,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "traceparent": f"00-{_SOURCE_TRACE}-{'5' * 16}-01",
    }
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        init = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "local-lineage", "version": "1"},
            },
        })
        assert init.status_code == 200
        headers["Mcp-Session-Id"] = init.headers["mcp-session-id"]
        notification = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "method": "notifications/initialized",
            "params": {},
        })
        assert notification.status_code == 202

        responses = []
        for rpc_id, name in ((3, "list_projects"), (4, "runtime_status")):
            response = client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "id": rpc_id, "method": "tools/call",
                "params": {"name": name, "arguments": {}},
            })
            assert response.status_code == 200
            request_id = response.headers["X-Request-ID"]
            traceparent = response.headers["traceparent"]
            assert _REQUEST_ID.fullmatch(request_id)
            assert _TRACEPARENT.fullmatch(traceparent)
            assert traceparent.split("-")[1] == _SOURCE_TRACE
            assert traceparent.split("-")[2] != "5" * 16
            result = _payload(response)
            responses.append((name, request_id, traceparent, result, response.text))

    assert len({x[1] for x in responses}) == 2
    assert len({x[2] for x in responses}) == 2
    assert isinstance(responses[0][3], list)
    assert responses[0][3][0]["code"] == "demo"
    assert responses[1][3] == {
        "schemaVersion": "runner-mcp/runtime-status-degraded/v1",
        "state": "degraded",
        "reasonCode": "self-update-state-unavailable",
        "runtimeEvidenceComplete": False,
    }
    audit_lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    audit = [json.loads(line) for line in audit_lines]
    assert len([row for row in audit if row["tool"] == "list_projects"]) == 1
    assert len([row for row in audit if row["tool"] == "runtime_status"]) == 1
    for name, request_id, _trace, _payload_value, text in responses:
        matched = [row for row in audit if row["request_id"] == request_id]
        assert len(matched) == 1
        assert matched[0]["tool"] == name
        assert matched[0]["result"] == ("denied" if name == "runtime_status" else "ok")
        assert _SECRET not in text
        assert str(tmp_path) not in text
    assert _SECRET not in repr(audit)
    assert "x" * 32 not in repr(audit)
