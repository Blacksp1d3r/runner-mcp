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
        "RUNNER_MCP_GITHUB_TOKEN": token,
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
    assert "Blacksp1d3r/AIfordable" not in audit


def test_fabric_agent_restart_is_argumentless_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []
    repair_calls: list[dict[str, object]] = []
    state_root_calls: list[Path] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

        def preflight(self):
            return {
                "state": "ready",
                "source_revision": "e" * 40,
            }

    def fake_repair(**kwargs):
        repair_calls.append(kwargs)

    def fake_restart(**kwargs):
        calls.append(kwargs)
        return {
            "state": "restarted",
            "pid_changed": True,
            "healthy": True,
        }

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )
    monkeypatch.setattr(
        "runner_mcp.server.restart_fabric_qualification_agent",
        fake_restart,
    )
    monkeypatch.setattr(
        "runner_mcp.server.a6_state_requested",
        lambda state_root: state_root_calls.append(state_root) or True,
    )
    monkeypatch.setattr(
        "runner_mcp.server.repair_a6_qualification_binding",
        fake_repair,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit-restart.jsonl",
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
            json={"jsonrpc": "2.0", "id": 30, "method": "tools/list", "params": {}},
        )
        assert "fabric_agent_restart" in listed.text

        restarted = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "fabric_agent_restart",
                    "arguments": {},
                },
            },
        )
        payload = _tool_json(restarted)

    assert payload == {
        "state": "restarted",
        "pid_changed": True,
        "healthy": True,
    }
    assert len(calls) == 1
    assert len(repair_calls) == 1
    expected_state_root = (
        tmp_path.resolve().parent.parent / ".local" / "state" / "runner-fabric"
    )
    assert state_root_calls == [expected_state_root]
    assert repair_calls[0]["state_root"] == expected_state_root
    assert repair_calls[0]["config_dir"] == tmp_path
    assert repair_calls[0]["fabric_revision"] == "e" * 40
    assert isinstance(repair_calls[0]["environment"], dict)
    assert calls[0]["config_dir"] == tmp_path
    assert calls[0]["resource_url"] == "http://127.0.0.1:9010/mcp"
    assert calls[0]["bearer_token"] == "f" * 32
    assert "127.0.0.1" not in restarted.text
    assert "f" * 32 not in restarted.text
    audit = (tmp_path / "audit-restart.jsonl").read_text(encoding="utf-8")
    assert "fabric_agent_restart" in audit
    assert "127.0.0.1" not in audit
    assert "f" * 32 not in audit


def test_bewind_disposable_bootstrap_restore_is_fixed_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

    class FakeRestorer:
        def __init__(self, **kwargs) -> None:
            calls.append({"init": kwargs})

        def restore(self):
            calls.append({"restore": True})
            return {
                "schemaVersion": "runner-mcp/bewind-disposable-bootstrap/v1",
                "state": "restored",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "qualificationId": "bewind-ocr-lab-v1",
                "targetAllocationId": "11111111-1111-5111-8111-111111111111",
                "policyValid": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )
    monkeypatch.setattr(
        "runner_mcp.server.BewindDisposableBootstrapRestorer",
        FakeRestorer,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit-bewind-bootstrap.jsonl",
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
            json={"jsonrpc": "2.0", "id": 40, "method": "tools/list", "params": {}},
        )
        assert "bewind_disposable_bootstrap_restore" in listed.text

        restored = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 41,
                "method": "tools/call",
                "params": {
                    "name": "bewind_disposable_bootstrap_restore",
                    "arguments": {},
                },
            },
        )
        payload = _tool_json(restored)

    assert payload["state"] == "restored"
    assert payload["workerId"] == "aifordable-lab"
    assert payload["normalActivationEnabled"] is False
    assert len(calls) == 2
    assert "f" * 32 not in restored.text
    audit = (tmp_path / "audit-bewind-bootstrap.jsonl").read_text(encoding="utf-8")
    assert "bewind_disposable_bootstrap_restore" in audit
    assert "127.0.0.1" not in audit
    assert "f" * 32 not in audit


def test_worker_policy_configure_refreshes_bootstrap_first(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

    class FakeRestorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def restore(self):
            calls.append("restore")
            return {
                "schemaVersion": "runner-mcp/bewind-disposable-bootstrap/v1",
                "state": "restored",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "qualificationId": "bewind-ocr-lab-v1",
                "targetAllocationId": "11111111-1111-5111-8111-111111111111",
                "policyValid": True,
                "normalActivationEnabled": False,
            }

    class FakePolicy:
        def __init__(self, **_kwargs) -> None:
            pass

        def configure(self):
            calls.append("configure")
            return {
                "schemaVersion": "runner-mcp/bewind-worker-qualification-policy/v1",
                "state": "configured",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "policyValid": True,
                "sourceTargetReady": True,
                "agentRestartRequired": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricBridgeClient",
        FakeFabricBridge,
    )
    monkeypatch.setattr(
        "runner_mcp.server.BewindDisposableBootstrapRestorer",
        FakeRestorer,
    )
    monkeypatch.setattr(
        "runner_mcp.server.BewindWorkerQualificationPolicyConfigurator",
        FakePolicy,
    )

    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit-policy-refresh.jsonl",
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
        configured = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 42,
                "method": "tools/call",
                "params": {
                    "name": "fabric_worker_qualification_policy_configure",
                    "arguments": {},
                },
            },
        )
        payload = _tool_json(configured)

    assert calls == ["restore", "configure"]
    assert payload["state"] == "configured"
    assert payload["sourceTargetReady"] is True
    assert payload["normalActivationEnabled"] is False
