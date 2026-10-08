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
                "name": "worker-qualification-provision-test",
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


def test_worker_qualification_provision_tool_is_strict_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeProvisioner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs

        def provision(self, **kwargs):
            calls.append(kwargs)
            return {
                "schemaVersion": (
                    "runner.fabric/worker-qualification-provisioning-result/v1"
                ),
                "workerId": kwargs["worker_id"],
                "capabilityProfile": kwargs["capability_profile"],
                "state": "ready",
                "reasonCode": "qualification-state-ready",
                "observedGeneration": kwargs["generation"],
                "observedFabricRevision": kwargs["fabric_revision"],
                "requestFingerprint": kwargs["request_fingerprint"],
                "managedLauncherReady": True,
                "qualificationStateReady": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricWorkerQualificationProvisioner",
        FakeProvisioner,
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
        assert "fabric_worker_qualification_provision" in listed.text

        arguments = {
            "worker_id": "worker-lab-a",
            "capability_profile": "bewind-ocr-qualification-v1",
            "generation": 7,
            "plan_digest": "b" * 64,
            "policy_expires_at": "2026-10-06T23:00:00+00:00",
            "fabric_revision": "a" * 40,
            "request_fingerprint": "c" * 64,
        }
        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_worker_qualification_provision",
                    "arguments": arguments,
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "ready"
        assert result["normalActivationEnabled"] is False
        assert calls == [arguments]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_worker_qualification_provision",
                    "arguments": {**arguments, "path": "/tmp/private"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert len(calls) == 1

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_worker_qualification_provision" in audit
    assert "/tmp/private" not in audit


def test_worker_qualification_policy_configure_tool_is_zero_arg_and_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeRuntimeImagePreparer:
        def __init__(self, **kwargs) -> None:
            assert "safety" in kwargs

        def prepare(self):
            return {
                "state": "ready",
                "builderClean": True,
                "normalActivationEnabled": False,
            }

    class FakeBootstrapRestorer:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs

        def restore(self):
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

    class FakePolicyConfigurator:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs
            assert "config_dir" in kwargs

        def configure(self):
            calls.append(True)
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
        "runner_mcp.server.BewindOcrRuntimeImagePreparer",
        FakeRuntimeImagePreparer,
    )
    monkeypatch.setattr(
        "runner_mcp.server.BewindDisposableBootstrapRestorer",
        FakeBootstrapRestorer,
    )
    monkeypatch.setattr(
        "runner_mcp.server.BewindWorkerQualificationPolicyConfigurator",
        FakePolicyConfigurator,
    )

    project_root = tmp_path / "project-policy"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects-policy.yml",
        audit_log=tmp_path / "audit-policy.jsonl",
        rate_limit_per_minute=60,
        operator_stop_file=tmp_path / "operator-policy.stop",
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
                "id": 10,
                "method": "tools/list",
                "params": {},
            },
        )
        assert "fabric_worker_qualification_policy_configure" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "fabric_worker_qualification_policy_configure",
                    "arguments": {},
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "configured"
        assert result["generation"] == 1
        assert result["normalActivationEnabled"] is False
        assert calls == [True]

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "fabric_worker_qualification_policy_configure",
                    "arguments": {"path": "/tmp/private"},
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert "/tmp/private" not in rejected.text
        assert calls == [True]
