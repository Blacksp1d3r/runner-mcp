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
            "clientInfo": {
                "name": "bewind-ocr-stage-test",
                "version": "1",
            },
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_bewind_ocr_qualification_stage_tool_is_zero_argument_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeStager:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs

        def stage(self):
            calls.append("stage")
            return {
                "schemaVersion": (
                    "runner-mcp/bewind-ocr-qualification-stage-result/v1"
                ),
                "state": "ready",
                "reasonCode": "qualification-source-staged",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "sourceId": "2026/02/03_1.pdf",
                "sourceSha256": "a" * 64,
                "sizeBytes": 1234,
                "singleUse": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.BewindOcrQualificationStager",
        FakeStager,
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
        secret_values={},
    )
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
        assert "bewind_ocr_qualification_stage" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_stage",
                    "arguments": {},
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "ready"
        assert result["sourceId"] == "2026/02/03_1.pdf"
        assert result["normalActivationEnabled"] is False
        assert calls == ["stage"]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_stage",
                    "arguments": {"path": "/tmp/not-allowed"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == ["stage"]

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "bewind_ocr_qualification_stage" in audit
    assert "/tmp/not-allowed" not in audit
