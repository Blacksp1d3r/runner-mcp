import json
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer " + ("x" * 32),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def _initialize() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "coding-availability-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_coding_availability_tool_is_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeQualificationRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs

        def run(self, case: str, expected_revision: str):
            calls.append((case, expected_revision))
            return {
                "schemaVersion": (
                    "runner.fabric/coding-agent-availability-qualification/v1"
                ),
                "case": case,
                "state": "wait",
                "reason_code": "provider_temporarily_unavailable",
                "work_unit_reason_code": "coding_worker_wait",
                "expected_revision": expected_revision,
                "assignment_requests": 1,
                "workspace_clean": True,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricCodingAvailabilityQualificationRunner",
        FakeQualificationRunner,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
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
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values={
            "RUNNER_FABRIC_CODING_Q7_PROJECT_ID": "project:q7",
            "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER": "github",
            "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY": (
                "Blacksp1d3r/AIfordable"
            ),
            "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT": "/srv/private/source",
            "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT": "/srv/private/workspaces",
            "RUNNER_FABRIC_CODING_Q7_WORKER_URL": "http://127.0.0.1:9021/mcp",
            "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "s" * 48,
        },
    )
    headers = _headers()
    revision = "b" * 40

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=_initialize())
        headers["Mcp-Session-Id"] = initialized.headers["mcp-session-id"]
        client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )

        listed = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert "fabric_coding_availability_qualify" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "provider-temporarily-unavailable",
                        "expected_revision": revision,
                    },
                },
            },
        )
        result = _tool_json(response)
        assert result["case"] == "provider-temporarily-unavailable"
        assert result["assignment_requests"] == 1
        assert result["workspace_clean"] is True
        assert calls == [("provider-temporarily-unavailable", revision)]
        assert "/srv/private" not in response.text
        assert "s" * 48 not in response.text

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "provider-temporarily-unavailable",
                        "expected_revision": revision,
                        "path": "/tmp/private",
                        "prompt": "do more",
                        "provider": "claude",
                    },
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == [("provider-temporarily-unavailable", revision)]

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_coding_availability_qualify" in audit
    assert "/srv/private" not in audit
    assert "s" * 48 not in audit
