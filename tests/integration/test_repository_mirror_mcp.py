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
            "clientInfo": {"name": "mirror-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_repository_mirror_tools_are_zero_argument_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeMirrorRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs

        def readiness(self):
            calls.append("readiness")
            return {
                "schemaVersion": (
                    "runner-mcp/fabric-repository-mirror-activation-readiness/v1"
                ),
                "ready": False,
                "storageReady": False,
                "desiredStateReady": False,
                "credentialBindingReady": False,
                "fabricRuntimeReady": True,
                "activationState": "unconfigured",
                "reasonCode": "storage-binding-unavailable",
                "mutationEnabled": False,
            }

        def preflight(self):
            calls.append("preflight")
            return {
                "schemaVersion": "runner.fabric/repository-mirror-preflight/v1",
                "ready": True,
                "managedRepositoryCount": 8,
                "mutationEnabled": False,
                "networkChecked": False,
            }

        def reconcile(self):
            calls.append("reconcile")
            return {
                "schemaVersion": "runner.fabric/repository-mirror-runtime-report/v1",
                "total": 8,
                "succeeded": 8,
                "failed": 0,
                "inventoryRevision": 12,
                "successful": True,
            }

    class FakeMirrorActivator:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs
            assert "github_token" in kwargs

        def activate(self):
            calls.append("activate")
            return {
                "schemaVersion": "runner-mcp/fabric-repository-mirror-activation/v1",
                "activated": True,
                "storageReady": True,
                "desiredStateBound": True,
                "credentialBindingPresent": True,
                "serviceBindingReady": True,
                "mutationScope": "repository-mirror-activation",
                "reconcileTriggered": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricRepositoryMirrorRunner",
        FakeMirrorRunner,
    )
    monkeypatch.setattr(
        "runner_mcp.server.FabricRepositoryMirrorActivator",
        FakeMirrorActivator,
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
        assert "fabric_repository_mirrors_activation_readiness" in listed.text
        assert "fabric_repository_mirrors_activate" in listed.text
        assert "fabric_repository_mirrors_preflight" in listed.text
        assert "fabric_repository_mirrors_reconcile" in listed.text

        readiness = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_repository_mirrors_activation_readiness",
                    "arguments": {},
                },
            },
        )
        readiness_payload = _tool_json(readiness)
        assert readiness_payload["ready"] is False
        assert readiness_payload["reasonCode"] == "storage-binding-unavailable"

        activate = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_repository_mirrors_activate",
                    "arguments": {},
                },
            },
        )
        activation_payload = _tool_json(activate)
        assert activation_payload["activated"] is True
        assert activation_payload["reconcileTriggered"] is False

        preflight = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "fabric_repository_mirrors_preflight",
                    "arguments": {},
                },
            },
        )
        assert _tool_json(preflight)["ready"] is True

        reconcile = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "fabric_repository_mirrors_reconcile",
                    "arguments": {},
                },
            },
        )
        assert _tool_json(reconcile)["successful"] is True

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "fabric_repository_mirrors_reconcile",
                    "arguments": {"repository": "example/private"},
                },
            },
        )
        assert _event(rejected)["result"]["isError"] is True

    assert calls == ["readiness", "activate", "preflight", "reconcile"]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_repository_mirrors_activation_readiness" in audit
    assert "fabric_repository_mirrors_activate" in audit
    assert "fabric_repository_mirrors_preflight" in audit
    assert "fabric_repository_mirrors_reconcile" in audit
    assert "example/private" not in audit
