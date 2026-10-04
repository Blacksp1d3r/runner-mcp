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
            "clientInfo": {"name": "ci-guest-test", "version": "1"},
        },
    }


def _tool_json(response) -> dict:
    event_line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    event = json.loads(event_line.removeprefix("data: "))
    return json.loads(event["result"]["content"][0]["text"])


def test_ci_guest_tools_are_bounded_fabric_proxies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

        def ci_runner_guest_status(self):
            calls.append("status")
            return {
                "contract_version": "runner.fabric/ci-runner-guest-execution/v1alpha1",
                "operation": "status",
                "state": "ready",
                "runner_name": "aifordable-lab-ci",
                "registered": False,
                "running": False,
                "isolation_green": True,
                "network_green": True,
                "mutation_enabled": True,
            }

        def ci_runner_guest_start(self):
            calls.append("start")
            return {
                "contract_version": "runner.fabric/ci-runner-guest-execution/v1alpha1",
                "operation": "start",
                "state": "running",
                "runner_name": "aifordable-lab-ci",
                "registered": True,
                "running": True,
                "isolation_green": True,
                "network_green": True,
                "mutation_enabled": True,
            }

        def ci_runner_guest_stop(self):
            calls.append("stop")
            return {
                "contract_version": "runner.fabric/ci-runner-guest-execution/v1alpha1",
                "operation": "stop",
                "state": "stopped",
                "runner_name": "aifordable-lab-ci",
                "registered": True,
                "running": False,
                "isolation_green": True,
                "network_green": True,
                "mutation_enabled": True,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )

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
        fabric_resource_url="http://127.0.0.1:9010/mcp",
        fabric_bearer_token="f" * 32,
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
        for name in (
            "fabric_ci_runner_guest_status",
            "fabric_ci_runner_guest_start",
            "fabric_ci_runner_guest_stop",
        ):
            assert name in listed.text

        for request_id, name in (
            (3, "fabric_ci_runner_guest_status"),
            (4, "fabric_ci_runner_guest_start"),
            (5, "fabric_ci_runner_guest_stop"),
        ):
            response = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {}},
                },
            )
            payload = _tool_json(response)
            assert payload["runner_name"] == "aifordable-lab-ci"
            assert "token" not in response.text.casefold()
            assert "path" not in response.text.casefold()

    assert calls == ["status", "start", "stop"]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_ci_runner_guest_status" in audit
    assert "fabric_ci_runner_guest_start" in audit
    assert "fabric_ci_runner_guest_stop" in audit
    assert "127.0.0.1" not in audit
    assert "f" * 32 not in audit

def test_ci_guest_enrollment_uses_private_allowlisted_spec(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured = {}
    token = "g" * 40
    runner_root = tmp_path / "guest-runner"
    work_root = runner_root / "_work"

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

    class FakeTransport:
        def __init__(self, **_kwargs) -> None:
            pass

    class Result:
        def to_payload(self):
            return {
                "state": "registered",
                "alias": "aifordable-lab-ci",
                "runner_name": "aifordable-lab-ci",
                "registered": True,
                "online": False,
                "busy": False,
                "custom_labels": ["aifordable-ci"],
            }

    class FakeGuestEnrollmentManager:
        def __init__(self, *, github, transport) -> None:
            captured["github"] = github
            captured["transport"] = transport

        def enroll(self, spec):
            captured["spec"] = spec
            return Result()

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )
    monkeypatch.setattr(
        "runner_mcp.server.CIRunnerGuestFabricTransport",
        FakeTransport,
    )
    monkeypatch.setattr(
        "runner_mcp.server.CIRunnerGuestEnrollmentManager",
        FakeGuestEnrollmentManager,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit-enroll.jsonl",
        rate_limit_per_minute=60,
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
        fabric_resource_url="http://127.0.0.1:9010/mcp",
        fabric_bearer_token="f" * 32,
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
    private = {
        "GITHUB_TOKEN": token,
        "RUNNER_MCP_CI_RUNNERS_JSON": json.dumps(
            [
                {
                    "alias": "aifordable-lab-ci",
                    "repository": "Blacksp1d3r/AIfordable",
                    "runner_name": "aifordable-lab-ci",
                    "runner_root": str(runner_root),
                    "work_root": str(work_root),
                    "labels": ["aifordable-ci"],
                }
            ]
        ),
    }
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values=private,
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
            json={"jsonrpc": "2.0", "id": 20, "method": "tools/list", "params": {}},
        )
        assert "ci_runner_guest_enroll" in listed.text

        enrolled = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {
                    "name": "ci_runner_guest_enroll",
                    "arguments": {"alias": "aifordable-lab-ci"},
                },
            },
        )
        payload = _tool_json(enrolled)

    assert payload["registered"] is True
    assert payload["runner_name"] == "aifordable-lab-ci"
    spec = captured["spec"]
    assert spec.repository == "Blacksp1d3r/AIfordable"
    assert spec.runner_name == "aifordable-lab-ci"
    assert spec.labels == ("aifordable-ci",)
    assert spec.transport_binding_key == "aifordable-lab-ci"
    assert token not in enrolled.text
    audit = (tmp_path / "audit-enroll.jsonl").read_text(encoding="utf-8")
    assert token not in audit
    assert str(runner_root) not in audit

