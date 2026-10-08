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
                "name": "bewind-ocr-run-test",
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


def test_bewind_ocr_qualification_run_tool_is_zero_argument_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeExecutionRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs
            assert "stager" in kwargs
            assert "disposable_qualifier" in kwargs
            assert "readiness_provider" in kwargs

        def run(self):
            calls.append("run")
            return {
                "schemaVersion": (
                    "runner-mcp/bewind-ocr-qualification-result/v1"
                ),
                "state": "qualified",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "bewindRevision": "c" * 40,
                "fabricRevision": "b" * 40,
                "pipeline": "pre1997-ocrmypdf-sidecar-0.2.0",
                "languages": "nld+fra+deu",
                "sourceId": "2026/02/03_1.pdf",
                "sourceSha256": "a" * 64,
                "pageCount": 160,
                "pageSha256": ["d" * 64],
                "outputSha256": "e" * 64,
                "germanSentinelVerified": True,
                "elapsedWallSeconds": 1.5,
                "cpuSecondsPerPage": None,
                "loadSummary": {
                    "start": {"logicalCpus": 8, "load1m": 0.1, "load5m": 0.2, "load15m": 0.3},
                    "end": {"logicalCpus": 8, "load1m": 0.2, "load5m": 0.2, "load15m": 0.3},
                },
                "failureCategory": None,
                "cleanupReceipt": {
                    "targetDestroyed": True,
                    "stagedInputRemoved": True,
                },
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.BewindOcrQualificationRunner",
        FakeExecutionRunner,
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
        assert "bewind_ocr_qualification_run" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_run",
                    "arguments": {},
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "qualified"
        assert result["languages"] == "nld+fra+deu"
        assert result["normalActivationEnabled"] is False
        assert calls == ["run"]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "bewind_ocr_qualification_run",
                    "arguments": {"path": "/tmp/not-allowed"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == ["run"]

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "bewind_ocr_qualification_run" in audit
    assert "/tmp/not-allowed" not in audit
