import json
import sys
import time
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.config import TestProfile as RunnerTestProfile
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
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "hello.txt").write_text("hello runner\n", encoding="utf-8")
    (project_root / ".env").write_text("DO_NOT_EXPOSE=this-value\n", encoding="utf-8")

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
        for tool_name in (
            "list_projects",
            "safety_status",
            "project_status",
            "read_project_file",
            "list_project_files",
            "file_metadata",
        ):
            assert tool_name in listed.text

        safety = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "safety_status",
                    "arguments": {},
                },
            },
        )
        assert safety.status_code == 200
        event_line = next(
            line for line in safety.text.splitlines() if line.startswith("data: ")
        )
        event = json.loads(event_line.removeprefix("data: "))
        safety_payload = json.loads(event["result"]["content"][0]["text"])
        assert safety_payload["retention_confirmed"] is True
        assert safety_payload["max_automatic_code_rollback_steps"] == 1
        assert "operator.stop" not in safety.text
        assert str(tmp_path) not in safety.text

        allowed = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "read_project_file",
                    "arguments": {
                        "project": "demo",
                        "path": "hello.txt",
                        "offset": 0,
                        "length": 20,
                    },
                },
            },
        )
        assert allowed.status_code == 200
        assert "hello runner" in allowed.text
        assert str(project_root) not in allowed.text

        blocked = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "read_project_file",
                    "arguments": {
                        "project": "demo",
                        "path": ".env",
                    },
                },
            },
        )
        assert blocked.status_code == 200
        assert '"isError":true' in blocked.text
        assert "Error executing tool read_project_file" in blocked.text
        assert "blocked by policy" not in blocked.text
        assert "this-value" not in blocked.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "read_project_file" in audit_text
    assert str(project_root) not in audit_text
    assert "hello runner" not in audit_text
    assert "this-value" not in audit_text


def test_authenticated_request_with_unexpected_host_is_rejected(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with TestClient(app, base_url="https://unexpected.example.invalid") as client:
        response = client.post(
            "/mcp",
            headers=auth_headers(),
            json=initialize_message(),
        )

    assert response.status_code == 421


def parse_tool_json(response) -> object:
    event_line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    event = json.loads(event_line.removeprefix("data: "))
    result = event["result"]
    assert result["isError"] is False
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return json.loads(result["content"][0]["text"])


def test_mcp_controlled_test_job_lifecycle(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
        test_jobs_root=tmp_path / "jobs",
        max_test_jobs=1,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=project_root,
                test_profiles={
                    "quick": RunnerTestProfile(
                        argv=[
                            sys.executable,
                            "-c",
                            "print('phase3-ok')",
                        ],
                        timeout_seconds=5,
                        max_log_bytes=4096,
                    )
                },
            )
        }
    )
    app = create_app(settings=settings, registry=registry)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200
        session_id = initialized.headers["mcp-session-id"]
        headers["Mcp-Session-Id"] = session_id
        client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )

        profiles = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "list_test_profiles",
                    "arguments": {"project": "demo"},
                },
            },
        )
        profile_payload = parse_tool_json(profiles)
        assert profile_payload == [
            {
                "name": "quick",
                "timeout_seconds": 5,
                "max_log_bytes": 4096,
            }
        ]
        assert sys.executable not in profiles.text
        assert str(project_root) not in profiles.text

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "run_tests",
                    "arguments": {
                        "project": "demo",
                        "suite": "quick",
                    },
                },
            },
        )
        started_payload = parse_tool_json(started)
        job_id = started_payload["job_id"]
        assert started_payload["project"] == "demo"
        assert started_payload["suite"] == "quick"

        deadline = time.monotonic() + 5
        status_payload = None
        request_id = 20
        while time.monotonic() < deadline:
            status = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "test_status",
                        "arguments": {"job_id": job_id},
                    },
                },
            )
            status_payload = parse_tool_json(status)
            if status_payload["status"] not in {"queued", "running"}:
                break
            request_id += 1
            time.sleep(0.02)

        assert status_payload is not None
        assert status_payload["status"] == "passed"
        assert status_payload["exit_code"] == 0

        log_response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 40,
                "method": "tools/call",
                "params": {
                    "name": "get_test_log",
                    "arguments": {
                        "job_id": job_id,
                        "offset": 0,
                        "length": 20,
                    },
                },
            },
        )
        log_payload = parse_tool_json(log_response)
        assert log_payload["content"] == "phase3-ok\n"
        assert str(project_root) not in log_response.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "run_tests" in audit_text
    assert "test_status" in audit_text
    assert "get_test_log" in audit_text
    assert "phase3-ok" not in audit_text
    assert sys.executable not in audit_text
    assert str(project_root) not in audit_text
