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
            "clientInfo": {"name": "disposable-target-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_disposable_target_tool_is_zero_argument_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = 0

    class FakeQualificationRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs

        def run(self):
            nonlocal calls
            calls += 1
            return {
                "schemaVersion": "runner.fabric/disposable-target-qualification/v1",
                "qualificationId": "af14-lab-v1",
                "targetAllocationId": "11111111-1111-4111-8111-111111111111",
                "runtimeProfile": "disposable-incus-vm-podman-v1",
                "createdReady": True,
                "resourceLimitsVerified": True,
                "guestRuntimeVerified": True,
                "managementAuthorityBlocked": True,
                "noDefaultRoute": True,
                "networkPolicyVerified": True,
                "destroyVerified": True,
                "recreateVerified": True,
                "recreateIsolationVerified": True,
                "finalDestroyVerified": True,
                "imageFingerprint": "a" * 64,
                "bootstrapSha256": "b" * 64,
                "qualificationPassed": True,
                "normalActivationEnabled": False,
                "finalState": "destroyed",
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricDisposableTargetQualificationRunner",
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
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": (
                str(tmp_path / "private-qualification.json")
            )
        },
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
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert "fabric_disposable_target_qualify" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_disposable_target_qualify",
                    "arguments": {},
                },
            },
        )
        result = _tool_json(response)
        assert result["qualificationPassed"] is True
        assert result["normalActivationEnabled"] is False
        assert "private" not in response.text.casefold()

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_disposable_target_qualify",
                    "arguments": {"path": "/tmp/private"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == 1

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_disposable_target_qualify" in audit
    assert "private-qualification" not in audit
