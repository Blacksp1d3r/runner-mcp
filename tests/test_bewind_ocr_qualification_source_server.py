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
            "clientInfo": {"name": "bewind-source-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_bewind_source_provision_tool_is_zero_argument_and_secret_free(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeAuthorityConfigurator:
        def __init__(self, **kwargs) -> None:
            assert "safety" in kwargs
            assert "environment" in kwargs
            assert "config_dir" in kwargs

        def configure(self):
            calls.append("authority")
            return {
                "state": "configured",
                "normalActivationEnabled": False,
            }

    class FakeProvisioner:
        def __init__(self, **kwargs) -> None:
            assert "safety" in kwargs
            assert "config_dir" in kwargs
            assert "custody" in kwargs

        def provision(self):
            calls.append("provision")
            return {
                "schemaVersion": (
                    "runner-mcp/bewind-ocr-qualification-source-provision/v1"
                ),
                "state": "ready",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "sourceId": "2026/02/03_1.pdf",
                "sourceSha256": "a" * 64,
                "sizeBytes": 2811759,
                "cache": "hit",
                "bindingReady": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.BewindOcrQualificationSourceProvisioner",
        FakeProvisioner,
    )
    monkeypatch.setattr(
        "runner_mcp.server."
        "BewindOcrQualificationExecutionAuthorityConfigurator",
        FakeAuthorityConfigurator,
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
    app = create_app(settings=settings, registry=registry, secret_values={})
    headers = _headers()

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
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        assert "bewind_ocr_qualification_source_provision" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_source_provision",
                    "arguments": {},
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "ready"
        assert result["bindingReady"] is True
        assert result["executionAuthorityReady"] is True
        assert result["normalActivationEnabled"] is False
        assert calls == ["provision", "authority"]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_source_provision",
                    "arguments": {"url": "https://example.invalid/private.pdf"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == ["provision", "authority"]

    rendered = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "bewind_ocr_qualification_source_provision" in rendered
    assert "example.invalid" not in rendered
