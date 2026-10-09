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
            "clientInfo": {"name": "archive-mirror-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_release_archive_mirror_readiness_is_zero_argument_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeReadiness:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs

        def status(self):
            calls.append("status")
            return {
                "schemaVersion": (
                    "runner-mcp/fabric-release-archive-mirror-readiness/v1"
                ),
                "ready": True,
                "configurationState": "configured",
                "primaryCustodyReady": True,
                "mountReady": True,
                "mirrorRootReady": True,
                "distinctDeviceReady": True,
                "reasonCode": "ready",
                "mutationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricReleaseArchiveMirrorReadiness",
        FakeReadiness,
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
    app = create_app(settings=settings, registry=registry)
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
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert "fabric_release_archive_mirror_readiness" in listed.text

        readiness = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_release_archive_mirror_readiness",
                    "arguments": {},
                },
            },
        )
        payload = _tool_json(readiness)
        assert payload["ready"] is True
        assert payload["distinctDeviceReady"] is True
        assert payload["mutationEnabled"] is False

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_release_archive_mirror_readiness",
                    "arguments": {"path": "/not-allowed"},
                },
            },
        )
        assert _event(rejected)["result"]["isError"] is True

    assert calls == ["status"]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_release_archive_mirror_readiness" in audit
    assert "/not-allowed" not in audit
