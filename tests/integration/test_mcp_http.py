from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app


def build_test_app(tmp_path: Path):
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "project",
            )
        }
    )
    return create_app(settings=settings, registry=registry)


def auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer " + ("x" * 32),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def initialize_message() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "integration-test", "version": "1"},
        },
    }


def test_authenticated_mcp_handshake_and_tool_listing(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200

        session_id = initialized.headers.get("mcp-session-id")
        assert session_id
        headers["Mcp-Session-Id"] = session_id

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
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert listed.status_code == 200
        assert "list_projects" in listed.text
        assert "project_status" in listed.text


def test_authenticated_request_with_unexpected_host_is_rejected(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with TestClient(app, base_url="https://unexpected.example.invalid") as client:
        response = client.post(
            "/mcp",
            headers=auth_headers(),
            json=initialize_message(),
        )

    assert response.status_code == 421
