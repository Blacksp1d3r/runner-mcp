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
            "clientInfo": {"name": "coding-availability-test", "version": "1"},
        },
    }


def _event(response) -> dict:
    line = next(
        item for item in response.text.splitlines() if item.startswith("data: ")
    )
    return json.loads(line.removeprefix("data: "))


def _tool_json(response) -> dict:
    return json.loads(_event(response)["result"]["content"][0]["text"])


def test_coding_availability_tool_is_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = []

    class FakeQualificationRunner:
        def __init__(self, **kwargs) -> None:
            assert "environment" in kwargs
            assert "safety" in kwargs

        def run(self, case: str, expected_revision: str):
            calls.append((case, expected_revision))
            return {
                "schemaVersion": (
                    "runner.fabric/coding-agent-availability-qualification/v1"
                ),
                "case": case,
                "state": "wait",
                "reason_code": "provider_temporarily_unavailable",
                "work_unit_reason_code": "coding_worker_wait",
                "expected_revision": expected_revision,
                "assignment_requests": 1,
                "workspace_clean": True,
            }

    monkeypatch.setattr(
        "runner_mcp.server.FabricCodingAvailabilityQualificationRunner",
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
            "RUNNER_FABRIC_CODING_Q7_PROJECT_ID": "project:q7",
            "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER": "github",
            "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY": (
                "Blacksp1d3r/AIfordable"
            ),
            "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT": "/srv/private/source",
            "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT": "/srv/private/workspaces",
            "RUNNER_FABRIC_CODING_Q7_WORKER_URL": "http://127.0.0.1:9021/mcp",
            "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "s" * 48,
        },
    )
    headers = _headers()
    revision = "b" * 40

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
        assert "fabric_coding_availability_qualify" in listed.text

        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "provider-temporarily-unavailable",
                        "expected_revision": revision,
                    },
                },
            },
        )
        result = _tool_json(response)
        assert result["case"] == "provider-temporarily-unavailable"
        assert result["assignment_requests"] == 1
        assert result["workspace_clean"] is True
        assert calls == [("provider-temporarily-unavailable", revision)]
        assert "/srv/private" not in response.text
        assert "s" * 48 not in response.text

        rejected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "provider-temporarily-unavailable",
                        "expected_revision": revision,
                        "path": "/tmp/private",
                        "prompt": "do more",
                        "provider": "claude",
                    },
                },
            },
        )
        event = _event(rejected)
        assert event["result"]["isError"] is True
        assert calls == [("provider-temporarily-unavailable", revision)]

    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_coding_availability_qualify" in audit
    assert "/srv/private" not in audit
    assert "s" * 48 not in audit


def test_q7_preflight_returns_safe_reason_without_running_any_assignment(
    tmp_path: Path, monkeypatch,
) -> None:
    calls = []

    class ReadOnlyQualificationRunner:
        def __init__(self, **kwargs):
            assert "environment" in kwargs
            assert "safety" in kwargs

        def preflight(self):
            calls.append("preflight")
            return {
                "schemaVersion": "runner-mcp/coding-availability-preflight/v1",
                "state": "wait",
                "reason_code": "q7_private_configuration_incomplete",
                "qualification_executed": False,
                "provider_session_checked": False,
                "dispatch_authorized": False,
            }

        def run(self, *_args, **_kwargs):
            raise AssertionError("read-only preflight may not execute Q7")

    monkeypatch.setattr(
        "runner_mcp.server.FabricCodingAvailabilityQualificationRunner",
        ReadOnlyQualificationRunner,
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
                display_name="Demo", repository="example/demo", root=project_root,
            )
        }
    )
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values={"RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "s" * 48},
    )
    headers = _headers()
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=_initialize())
        headers["Mcp-Session-Id"] = initialized.headers["mcp-session-id"]
        client.post(
            "/mcp", headers=headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )
        catalog = client.post(
            "/mcp", headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert "fabric_coding_availability_preflight" in catalog.text
        response = client.post(
            "/mcp", headers=headers,
            json={
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_preflight",
                    "arguments": {},
                },
            },
        )
        report = _tool_json(response)
        assert report["state"] == "wait"
        assert report["reason_code"] == "q7_private_configuration_incomplete"
        assert report["dispatch_authorized"] is False
        assert report["provider_session_checked"] is False
        assert "s" * 48 not in response.text
        assert "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN" not in response.text
        assert calls == ["preflight"]
        rejected = client.post(
            "/mcp", headers=headers,
            json={
                "jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_preflight",
                    "arguments": {"provider": "claude", "command": "run"},
                },
            },
        )
        assert _event(rejected)["result"]["isError"] is True
        assert calls == ["preflight"]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "q7_private_configuration_incomplete" in audit
    assert "s" * 48 not in audit


def test_q7_failed_tool_returns_bounded_result_with_no_unsafe_retry(
    tmp_path: Path, monkeypatch,
) -> None:
    from runner_mcp.fabric_coding_availability import (
        FabricCodingAvailabilityQualificationError,
    )

    calls = []

    class FailedQualificationRunner:
        def __init__(self, **kwargs):
            assert "environment" in kwargs
            assert "safety" in kwargs

        def run(self, case: str, expected_revision: str):
            calls.append((case, expected_revision))
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_failed"
            )

    monkeypatch.setattr(
        "runner_mcp.server.FabricCodingAvailabilityQualificationRunner",
        FailedQualificationRunner,
    )
    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo", repository="example/demo", root=project_root,
            )
        }
    )
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values={"RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN": "s" * 48},
    )
    headers = _headers()
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=_initialize())
        headers["Mcp-Session-Id"] = initialized.headers["mcp-session-id"]
        client.post(
            "/mcp", headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized", "params": {},
            },
        )
        response = client.post(
            "/mcp", headers=headers,
            json={
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "subscription-auth-required",
                        "expected_revision": "a" * 40,
                    },
                },
            },
        )
        event = _event(response)
        assert event["result"]["isError"] is False
        result = _tool_json(response)
        assert result["schemaVersion"] == (
            "runner-mcp/coding-availability-qualification-unavailable/v1"
        )
        assert result["reason_code"] == "q7_execution_unverified"
        assert result["state"] == "unknown"
        assert result["result_verified"] is False
        assert result["qualification_effect"] == "unknown"
        assert result["dispatch_authorized"] is False
        assert result["retry_authorized"] is False
        assert "assignment_requests" not in result
        assert "s" * 48 not in response.text
        assert calls == [("subscription-auth-required", "a" * 40)]
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "q7_execution_unverified" in audit
    assert "s" * 48 not in audit


def test_q7_invalid_case_produces_non_started_safe_error_over_mcp(
    tmp_path: Path, monkeypatch,
) -> None:
    from runner_mcp.fabric_coding_availability import (
        FabricCodingAvailabilityQualificationError,
    )

    class PreRunError:
        def __init__(self, **_kwargs):
            pass

        def run(self, _case, _revision):
            raise FabricCodingAvailabilityQualificationError(
                "fabric_coding_availability_qualification_case_invalid"
            )

    monkeypatch.setattr(
        "runner_mcp.server.FabricCodingAvailabilityQualificationRunner",
        PreRunError,
    )
    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo", repository="example/demo", root=project_root,
            )
        }
    )
    app = create_app(settings=settings, registry=registry)
    headers = _headers()
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=_initialize())
        headers["Mcp-Session-Id"] = initialized.headers["mcp-session-id"]
        client.post(
            "/mcp", headers=headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )
        response = client.post(
            "/mcp", headers=headers,
            json={
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {
                    "name": "fabric_coding_availability_qualify",
                    "arguments": {
                        "case": "invalid",
                        "expected_revision": "a" * 40,
                    },
                },
            },
        )
        result = _tool_json(response)
        assert result["state"] == "blocked"
        assert result["reason_code"] == "invalid_fixed_case"
        assert result["qualification_effect"] == "not_started"
        assert result["retry_authorized"] is False
