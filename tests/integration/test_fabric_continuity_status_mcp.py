import json
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.fabric_continuity_status import FabricContinuityStatusError
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
            "clientInfo": {"name": "continuity-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_fabric_continuity_status_is_zero_argument_and_read_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeContinuityRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs

        def status(self):
            calls.append("status")
            return {
                "schemaVersion": "runner.fabric/continuity-status/v1",
                "projectId": "project:runner-fabric",
                "candidateRevision": "a" * 40,
                "mode": "local-continuity",
                "reasonCode": "external-unavailable",
                "localWorkAllowed": True,
                "externalSubmissionAllowed": False,
                "reconciliationRequired": False,
                "sourceAuthorityState": "local_primary_fenced",
                "mirrorState": "in-sync",
                "pendingExternalCount": 2,
                "oldestPendingAgeSeconds": 30,
                "localMirrorAgeSeconds": None,
                "providerOutageDrillAgeSeconds": None,
                "localOutageDrillAgeSeconds": None,
                "providerMutationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricContinuityStatusRunner",
        FakeContinuityRunner,
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
        assert "fabric_continuity_status" in listed.text

        status = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_continuity_status",
                    "arguments": {},
                },
            },
        )
        assert _tool_json(status)["mode"] == "local-continuity"

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_continuity_status",
                    "arguments": {"project": "example/private"},
                },
            },
        )
        assert _event(rejected)["result"]["isError"] is True

    assert calls == ["status"]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_continuity_status" in audit
    assert "local-continuity" in audit
    assert "example/private" not in audit


def test_runtime_doctor_exposes_only_bounded_continuity_failure_category(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FailingContinuityRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs

        def status(self):
            raise FabricContinuityStatusError(
                "fabric_continuity_status_configuration_unavailable"
            )

    monkeypatch.setattr(
        "runner_mcp.server.FabricContinuityStatusRunner",
        FailingContinuityRunner,
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
        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "runtime_doctor",
                    "arguments": {},
                },
            },
        )

    payload = _tool_json(response)
    check = next(
        item
        for item in payload["checks"]
        if item["name"] == "fabric_continuity_status"
    )
    assert check == {
        "name": "fabric_continuity_status",
        "state": "warn",
        "detail": "fabric_continuity_status_configuration_unavailable",
    }
    rendered = json.dumps(payload)
    assert "/private" not in rendered
    assert "token" not in rendered
