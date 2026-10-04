from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer " + ("x" * 32),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def _initialize() -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "external-target-test", "version": "1"},
        },
    }


def _payload(response) -> dict[str, object]:
    event_line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    event = json.loads(event_line.removeprefix("data: "))
    result = event["result"]
    assert result["isError"] is False
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        if set(structured) == {"result"}:
            return structured["result"]
        return structured
    parsed = json.loads(result["content"][0]["text"])
    if isinstance(parsed, dict) and set(parsed) == {"result"}:
        return parsed["result"]
    return parsed


def test_runner_mcp_exposes_only_semantic_external_target_arguments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target_id = str(uuid4())
    environment_id = str(uuid4())
    calls: list[tuple[str, str]] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

        def inspect_external_target(
            self,
            *,
            target_allocation_id: str,
            environment_id: str,
        ) -> dict[str, object]:
            calls.append((target_allocation_id, environment_id))
            return {
                "contract_version": (
                    "runner.fabric/external-target-inspection/v1alpha1"
                ),
                "target_allocation_id": target_allocation_id,
                "environment_id": environment_id,
                "reachability": "reachable",
                "readiness": "ready",
                "observed_at": "2026-10-04T11:00:00+00:00",
                "reason_code": "healthy",
                "release_revision": "c" * 40,
                "evidence_refs": [
                    "external-target:fixed-readonly-adapter",
                ],
                "live_mutation_enabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        fabric_resource_url="http://127.0.0.1:9010/mcp",
        fabric_bearer_token="f" * 32,
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
    app = create_app(settings=settings, registry=registry)
    headers = _headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=_initialize())
        assert initialized.status_code == 200
        headers["Mcp-Session-Id"] = initialized.headers["mcp-session-id"]
        notification = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        assert notification.status_code == 202

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
        assert "fabric_inspect_external_target" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_inspect_external_target",
                    "arguments": {
                        "target_allocation_id": target_id,
                        "environment_id": environment_id,
                    },
                },
            },
        )
        result = _payload(response)
        assert result["release_revision"] == "c" * 40
        assert result["live_mutation_enabled"] is False
        assert calls == [(target_id, environment_id)]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_inspect_external_target",
                    "arguments": {
                        "target_allocation_id": target_id,
                        "environment_id": environment_id,
                        "host": "rasff.example.test",
                    },
                },
            },
        )
        assert rejected.status_code == 200
        assert '"isError":true' in rejected.text
        assert "rasff.example.test" not in rejected.text

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_inspect_external_target" in audit
    assert "rasff.example.test" not in audit
