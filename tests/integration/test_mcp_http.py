import json
import sys
import time
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import (
    DatabaseConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
    ServiceConfig,
)
from runner_mcp.config import TestProfile as RunnerTestProfile
from runner_mcp.server import Settings, create_app
from runner_mcp.service_manager import ServiceState


def build_test_app(tmp_path: Path):
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=tmp_path / "project",
            )
        }
    )
    return create_app(settings=settings, registry=registry)


def auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer " + ("x" * 32),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def initialize_message() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "integration-test", "version": "1"},
        },
    }


def test_authenticated_mcp_handshake_and_tool_listing(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "hello.txt").write_text("hello runner\n", encoding="utf-8")
    (project_root / ".env").write_text("DO_NOT_EXPOSE=this-value\n", encoding="utf-8")

    app = build_test_app(tmp_path)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200

        session_id = initialized.headers.get("mcp-session-id")
        assert session_id
        headers["Mcp-Session-Id"] = session_id

        notification = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        assert notification.status_code == 202

        listed = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert listed.status_code == 200
        for tool_name in (
            "list_projects",
            "safety_status",
            "project_status",
            "read_project_file",
            "list_project_files",
            "file_metadata",
        ):
            assert tool_name in listed.text

        safety = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "safety_status",
                    "arguments": {},
                },
            },
        )
        assert safety.status_code == 200
        event_line = next(
            line for line in safety.text.splitlines() if line.startswith("data: ")
        )
        event = json.loads(event_line.removeprefix("data: "))
        safety_payload = json.loads(event["result"]["content"][0]["text"])
        assert safety_payload["retention_confirmed"] is True
        assert safety_payload["max_automatic_code_rollback_steps"] == 1
        assert "operator.stop" not in safety.text
        assert str(tmp_path) not in safety.text

        allowed = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "read_project_file",
                    "arguments": {
                        "project": "demo",
                        "path": "hello.txt",
                        "offset": 0,
                        "length": 20,
                    },
                },
            },
        )
        assert allowed.status_code == 200
        assert "hello runner" in allowed.text
        assert str(project_root) not in allowed.text

        blocked = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "read_project_file",
                    "arguments": {
                        "project": "demo",
                        "path": ".env",
                    },
                },
            },
        )
        assert blocked.status_code == 200
        assert '"isError":true' in blocked.text
        assert "Error executing tool read_project_file" in blocked.text
        assert "blocked by policy" not in blocked.text
        assert "this-value" not in blocked.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "read_project_file" in audit_text
    assert str(project_root) not in audit_text
    assert "hello runner" not in audit_text
    assert "this-value" not in audit_text


def test_authenticated_request_with_unexpected_host_is_rejected(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    with TestClient(app, base_url="https://unexpected.example.invalid") as client:
        response = client.post(
            "/mcp",
            headers=auth_headers(),
            json=initialize_message(),
        )

    assert response.status_code == 421


def parse_tool_json(response) -> object:
    event_line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    event = json.loads(event_line.removeprefix("data: "))
    result = event["result"]
    assert result["isError"] is False
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return json.loads(result["content"][0]["text"])


def test_mcp_controlled_test_job_lifecycle(tmp_path: Path) -> None:
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
        test_jobs_root=tmp_path / "jobs",
        max_test_jobs=1,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=project_root,
                test_profiles={
                    "quick": RunnerTestProfile(
                        argv=[
                            sys.executable,
                            "-c",
                            "print('phase3-ok')",
                        ],
                        timeout_seconds=5,
                        max_log_bytes=4096,
                    )
                },
            )
        }
    )
    app = create_app(settings=settings, registry=registry)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200
        session_id = initialized.headers["mcp-session-id"]
        headers["Mcp-Session-Id"] = session_id
        client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )

        profiles = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "list_test_profiles",
                    "arguments": {"project": "demo"},
                },
            },
        )
        profile_payload = parse_tool_json(profiles)
        assert profile_payload == [
            {
                "name": "quick",
                "timeout_seconds": 5,
                "max_log_bytes": 4096,
            }
        ]
        assert sys.executable not in profiles.text
        assert str(project_root) not in profiles.text

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "run_tests",
                    "arguments": {
                        "project": "demo",
                        "suite": "quick",
                    },
                },
            },
        )
        started_payload = parse_tool_json(started)
        job_id = started_payload["job_id"]
        assert started_payload["project"] == "demo"
        assert started_payload["suite"] == "quick"

        deadline = time.monotonic() + 5
        status_payload = None
        request_id = 20
        while time.monotonic() < deadline:
            status = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "test_status",
                        "arguments": {"job_id": job_id},
                    },
                },
            )
            status_payload = parse_tool_json(status)
            if status_payload["status"] not in {"queued", "running"}:
                break
            request_id += 1
            time.sleep(0.02)

        assert status_payload is not None
        assert status_payload["status"] == "passed"
        assert status_payload["exit_code"] == 0

        log_response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 40,
                "method": "tools/call",
                "params": {
                    "name": "get_test_log",
                    "arguments": {
                        "job_id": job_id,
                        "offset": 0,
                        "length": 20,
                    },
                },
            },
        )
        log_payload = parse_tool_json(log_response)
        assert log_payload["content"] == "phase3-ok\n"
        assert str(project_root) not in log_response.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "run_tests" in audit_text
    assert "test_status" in audit_text
    assert "get_test_log" in audit_text
    assert "phase3-ok" not in audit_text
    assert sys.executable not in audit_text
    assert str(project_root) not in audit_text


def test_mcp_service_alias_status_restart_and_emergency_stop(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    stop_file = tmp_path / "operator.stop"
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=stop_file,
        retention_confirmed=True,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=project_root,
                services={
                    "web": ServiceConfig(
                        unit="private-web.service",
                        allow_restart=True,
                    )
                },
            )
        }
    )

    class FakeSystemd:
        def __init__(self) -> None:
            self.actions = []

        def status(self, unit: str) -> ServiceState:
            assert unit == "private-web.service"
            return ServiceState("loaded", "active", "running")

        def action(self, unit: str, action: str) -> None:
            self.actions.append((unit, action))

    fake = FakeSystemd()
    monkeypatch.setattr(
        "runner_mcp.service_manager.SystemdUserBackend",
        lambda: fake,
    )
    app = create_app(settings=settings, registry=registry)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
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
                "id": 50,
                "method": "tools/call",
                "params": {
                    "name": "list_services",
                    "arguments": {"project": "demo"},
                },
            },
        )
        listed_payload = parse_tool_json(listed)
        assert listed_payload[0]["name"] == "web"
        assert "private-web.service" not in listed.text

        status = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 51,
                "method": "tools/call",
                "params": {
                    "name": "service_status",
                    "arguments": {"project": "demo", "service": "web"},
                },
            },
        )
        status_payload = parse_tool_json(status)
        assert status_payload["active_state"] == "active"
        assert "private-web.service" not in status.text

        restarted = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 52,
                "method": "tools/call",
                "params": {
                    "name": "restart_service",
                    "arguments": {"project": "demo", "service": "web"},
                },
            },
        )
        restart_payload = parse_tool_json(restarted)
        assert restart_payload["action"] == "restart"
        assert fake.actions == [("private-web.service", "restart")]
        assert "private-web.service" not in restarted.text

        stop_file.write_text("stop\n", encoding="utf-8")
        blocked = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 53,
                "method": "tools/call",
                "params": {
                    "name": "restart_service",
                    "arguments": {"project": "demo", "service": "web"},
                },
            },
        )
        assert '"isError":true' in blocked.text
        assert fake.actions == [("private-web.service", "restart")]

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "restart_service" in audit_text
    assert "private-web.service" not in audit_text


def test_mcp_database_backup_and_migration_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import subprocess

    secret = "postgresql://user:mcp-private@example.invalid/app"
    project_root = tmp_path / "project"
    project_root.mkdir()
    status_script = tmp_path / "migration-status"
    apply_script = tmp_path / "migration-apply"
    status_script.write_text(
        '#!/bin/sh\nprintf "%s\n" "$DATABASE_URL"\n',
        encoding="utf-8",
    )
    apply_script.write_text(
        '#!/bin/sh\nprintf "migration-applied\n"\n',
        encoding="utf-8",
    )
    status_script.chmod(0o755)
    apply_script.chmod(0o755)
    fake_pg_dump = tmp_path / "pg_dump"
    fake_pg_dump.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_pg_dump.chmod(0o755)

    def fake_dump_run(arguments, **kwargs):
        assert secret not in " ".join(arguments)
        assert kwargs["env"]["PGDATABASE"] == secret
        kwargs["stdout"].write(b"mcp-backup")
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(
        "runner_mcp.database_manager._known_executable",
        lambda names: fake_pg_dump,
    )
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        fake_dump_run,
    )

    stop_file = tmp_path / "operator.stop"
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=stop_file,
        retention_confirmed=True,
        database_backup_root=tmp_path / "backups",
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=project_root,
                database=DatabaseConfig(
                    dsn_env="RUNNER_MCP_DB_DEMO",
                    migrations=MigrationConfig(
                        status_argv=[str(status_script)],
                        apply_argv=[str(apply_script)],
                        dsn_target_env="DATABASE_URL",
                        timeout_seconds=5,
                        max_output_bytes=4096,
                    ),
                ),
            )
        }
    )
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values={"RUNNER_MCP_DB_DEMO": secret},
    )
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
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

        backup = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 60,
                "method": "tools/call",
                "params": {
                    "name": "backup_database",
                    "arguments": {"project": "demo"},
                },
            },
        )
        backup_payload = parse_tool_json(backup)
        assert backup_payload["kind"] == "manual"
        assert secret not in backup.text
        assert str(tmp_path) not in backup.text

        status = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 61,
                "method": "tools/call",
                "params": {
                    "name": "migration_status",
                    "arguments": {"project": "demo"},
                },
            },
        )
        status_payload = parse_tool_json(status)
        assert status_payload["status"] == "ok"
        assert secret not in status_payload["output"]
        assert "[REDACTED]" in status_payload["output"]

        applied = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 62,
                "method": "tools/call",
                "params": {
                    "name": "apply_migrations",
                    "arguments": {"project": "demo"},
                },
            },
        )
        applied_payload = parse_tool_json(applied)
        assert applied_payload["status"] == "applied"
        assert applied_payload["pre_migration_backup"]["kind"] == "pre_migration"
        assert applied_payload["database_restore_performed"] is False
        assert secret not in applied.text

        listed = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 63,
                "method": "tools/call",
                "params": {
                    "name": "list_backups",
                    "arguments": {"project": "demo"},
                },
            },
        )
        listed_payload = parse_tool_json(listed)
        assert len(listed_payload) == 2
        assert secret not in listed.text
        assert str(tmp_path) not in listed.text

        stop_file.write_text("stop\n", encoding="utf-8")
        blocked = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 64,
                "method": "tools/call",
                "params": {
                    "name": "apply_migrations",
                    "arguments": {"project": "demo"},
                },
            },
        )
        assert '"isError":true' in blocked.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert secret not in audit_text
    assert str(tmp_path) not in audit_text
    assert "backup_database" in audit_text
    assert "apply_migrations" in audit_text


def test_mcp_async_staging_deployment_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeDeploymentManager:
        def __init__(self, **kwargs) -> None:
            self.plans: list[str] = []
            self.deploys: list[str] = []

        def plan(self, project: str) -> dict:
            self.plans.append(project)
            return {
                "project": project,
                "environment": "staging",
                "commit": "a" * 40,
                "short_commit": "a" * 12,
                "current_release": None,
                "service": "web",
                "required_tests": [],
                "run_migrations": False,
                "automatic_code_rollback": True,
            }

        def deploy(self, project: str) -> dict:
            self.deploys.append(project)
            return {
                "project": project,
                "status": "deployed",
                "release_id": "safe-release-id",
                "commit": "a" * 40,
                "previous_release": None,
                "tests": [],
                "migration": None,
                "health": {"active_state": "active", "health": "healthy"},
                "automatic_code_rollback_performed": False,
            }

    monkeypatch.setattr("runner_mcp.server.DeploymentManager", FakeDeploymentManager)
    project_root = tmp_path / "project"
    project_root.mkdir()
    stop_file = tmp_path / "operator.stop"
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=stop_file,
        retention_confirmed=True,
        deployment_jobs_root=tmp_path / "deployment-jobs",
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment="staging",
                root=project_root,
            )
        }
    )
    app = create_app(settings=settings, registry=registry)
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
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

        plan = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 70,
                "method": "tools/call",
                "params": {
                    "name": "plan_deploy",
                    "arguments": {"project": "demo"},
                },
            },
        )
        plan_payload = parse_tool_json(plan)
        assert plan_payload["environment"] == "staging"
        assert plan_payload["automatic_code_rollback"] is True
        assert str(tmp_path) not in plan.text

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 71,
                "method": "tools/call",
                "params": {
                    "name": "deploy_staging",
                    "arguments": {"project": "demo"},
                },
            },
        )
        started_payload = parse_tool_json(started)
        job_id = started_payload["job_id"]
        assert started_payload["project"] == "demo"

        deadline = time.monotonic() + 3
        deployment_payload = None
        request_id = 72
        while time.monotonic() < deadline:
            status = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "deployment_status",
                        "arguments": {"job_id": job_id},
                    },
                },
            )
            deployment_payload = parse_tool_json(status)
            if deployment_payload["state"] not in {"queued", "running"}:
                break
            request_id += 1
            time.sleep(0.01)

        assert deployment_payload is not None
        assert deployment_payload["state"] == "completed"
        assert deployment_payload["result"]["status"] == "deployed"
        assert str(tmp_path) not in repr(deployment_payload)

        stop_file.write_text("stop\n", encoding="utf-8")
        blocked = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 90,
                "method": "tools/call",
                "params": {
                    "name": "deploy_staging",
                    "arguments": {"project": "demo"},
                },
            },
        )
        assert '"isError":true' in blocked.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "plan_deploy" in audit_text
    assert "deploy_staging" in audit_text
    assert "deployment_status" in audit_text
    assert str(tmp_path) not in audit_text
