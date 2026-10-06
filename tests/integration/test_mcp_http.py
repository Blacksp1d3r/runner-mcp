import json
import sys
import time
from pathlib import Path

from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS
from starlette.testclient import TestClient

from runner_mcp.approval_manager import ApprovalManager
from runner_mcp.config import (
    DatabaseConfig,
    DeploymentConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
    ServiceConfig,
)
from runner_mcp.config import TestProfile as RunnerTestProfile
from runner_mcp.fabric_bridge import FabricBridgeError
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
            "known_project_preflight",
            "prepare_known_project",
            "register_known_project",
            "safety_status",
            "runtime_status",
            "runtime_doctor",
            "build_identity",
            "project_status",
            "read_project_file",
            "list_project_files",
            "file_metadata",
        ):
            assert tool_name in listed.text

        for tool_name in (
            "fabric_host_inspect",
            "fabric_run_work_unit",
            "fabric_get_work_unit",
            "fabric_cancel_work_unit",
        ):
            assert tool_name not in listed.text

        identity = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 29,
                "method": "tools/call",
                "params": {
                    "name": "build_identity",
                    "arguments": {},
                },
            },
        )
        assert identity.status_code == 200
        identity_payload = parse_tool_json(identity)
        assert set(identity_payload) == {
            "component_id",
            "build_version",
            "source_revision",
            "artifact_digest",
            "protocol_min",
            "protocol_max",
            "interface_schema_digest",
        }
        assert identity_payload["component_id"] == "runner-mcp"
        assert isinstance(identity_payload["build_version"], str)
        assert identity_payload["build_version"]
        assert identity_payload["source_revision"] is None
        assert identity_payload["artifact_digest"] is None
        assert identity_payload["protocol_min"] == HANDSHAKE_PROTOCOL_VERSIONS[0]
        assert identity_payload["protocol_max"] == HANDSHAKE_PROTOCOL_VERSIONS[-1]
        digest = identity_payload["interface_schema_digest"]
        assert isinstance(digest, str)
        assert len(digest) == 64
        assert all(char in "0123456789abcdef" for char in digest)
        assert ("x" * 32) not in identity.text
        assert str(tmp_path) not in identity.text
        assert "mcp.example.invalid" not in identity.text

        rejected_identity = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 28,
                "method": "tools/call",
                "params": {
                    "name": "build_identity",
                    "arguments": {"path": "/tmp/private"},
                },
            },
        )
        assert rejected_identity.status_code == 200
        assert '"isError":true' in rejected_identity.text
        assert "/tmp/private" not in rejected_identity.text

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

        runtime = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "runtime_status",
                    "arguments": {},
                },
            },
        )
        assert runtime.status_code == 200
        runtime_event_line = next(
            line for line in runtime.text.splitlines() if line.startswith("data: ")
        )
        runtime_event = json.loads(runtime_event_line.removeprefix("data: "))
        runtime_payload = json.loads(runtime_event["result"]["content"][0]["text"])
        assert runtime_payload["projects"] == 1
        assert runtime_payload["retention_confirmed"] is True
        assert str(tmp_path) not in runtime.text
        assert "https://" not in runtime.text

        doctor = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 32,
                "method": "tools/call",
                "params": {
                    "name": "runtime_doctor",
                    "arguments": {},
                },
            },
        )
        assert doctor.status_code == 200
        doctor_event_line = next(
            line for line in doctor.text.splitlines() if line.startswith("data: ")
        )
        doctor_event = json.loads(doctor_event_line.removeprefix("data: "))
        doctor_payload = json.loads(doctor_event["result"]["content"][0]["text"])
        assert doctor_payload["failed_checks"] == 0
        assert str(tmp_path) not in doctor.text
        assert "mcp.example.invalid" not in doctor.text

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
                "runtime": "default",
                "parallel_safe": False,
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
            if status_payload["status"] not in {"queued", "claimed", "running"}:
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

    monkeypatch.setattr(
        "runner_mcp.migration_planning.clean_head",
        lambda root: {"commit": "c" * 40, "clean": True},
    )

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
        approval_root=tmp_path / "approvals",
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

        approval_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 62,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {"project": "demo", "action": "migration"},
                },
            },
        )
        approval_id = parse_tool_json(approval_request)["approval_id"]
        ApprovalManager(root=settings.approval_root).approve(approval_id)

        applied = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 63,
                "method": "tools/call",
                "params": {
                    "name": "apply_migrations",
                    "arguments": {"project": "demo", "approval_id": approval_id},
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




def test_mcp_explicit_async_migration_flow_preserves_sync_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from runner_mcp.migration_jobs import MigrationJobError
    from runner_mcp.migration_planning import migration_binding_fingerprint

    commit = "c" * 40
    monkeypatch.setattr(
        "runner_mcp.migration_planning.clean_head",
        lambda _root: {"commit": commit, "clean": True},
    )

    project_root = tmp_path / "async-migration-project"
    project_root.mkdir()
    approval_root = tmp_path / "async-migration-approvals"
    migration_jobs_root = tmp_path / "async-migration-jobs"
    holder: dict[str, object] = {}

    class FakeMigrationJobRunner:
        def __init__(self, **kwargs) -> None:
            assert kwargs["jobs_root"] == migration_jobs_root
            self.starts: list[tuple[str, str, str]] = []
            self.fail_next = False
            self.jobs: dict[str, dict] = {}
            holder["runner"] = self

        def start(
            self,
            project: str,
            *,
            expected_binding_fingerprint: str,
            expected_commit: str,
        ) -> dict:
            approval_id = holder["approval_id"]
            assert isinstance(approval_id, str)
            approval = ApprovalManager(root=approval_root).status(approval_id)
            assert approval["state"] == "consumed"
            assert expected_commit == commit
            assert len(expected_binding_fingerprint) == 64
            self.starts.append(
                (project, expected_binding_fingerprint, expected_commit)
            )
            if self.fail_next:
                self.fail_next = False
                raise MigrationJobError("simulated durable enqueue failure")

            job_id = "f" * 32
            payload = {
                "job_id": job_id,
                "project": project,
                "operation": "migration",
                "state": "queued",
                "created_at": "2026-09-28T20:00:00+00:00",
                "started_at": None,
                "finished_at": None,
                "migration_state": None,
                "error_category": None,
                "pre_migration_backup_created": False,
                "output_truncated": False,
            }
            self.jobs[job_id] = {
                **payload,
                "state": "running",
                "started_at": "2026-09-28T20:00:01+00:00",
            }
            return payload

        def status(self, job_id: str) -> dict:
            return self.jobs[job_id]

    monkeypatch.setattr(
        "runner_mcp.server.MigrationJobRunner",
        FakeMigrationJobRunner,
    )

    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused-async-migration.yml",
        audit_log=tmp_path / "async-migration-audit.jsonl",
        operator_stop_file=tmp_path / "async-migration-operator.stop",
        retention_confirmed=True,
        database_backup_root=tmp_path / "async-migration-backups",
        migration_jobs_root=migration_jobs_root,
        approval_root=approval_root,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment="staging",
                root=project_root,
                database=DatabaseConfig(
                    dsn_env="RUNNER_MCP_DB_DEMO",
                    migrations=MigrationConfig(
                        status_argv=["/bin/true"],
                        apply_argv=["/bin/true"],
                        dsn_target_env="DATABASE_URL",
                    ),
                ),
            )
        }
    )
    app = create_app(
        settings=settings,
        registry=registry,
        secret_values={
            "RUNNER_MCP_DB_DEMO": "postgresql://user:private@example.invalid/app"
        },
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

        async_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 160,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {
                        "project": "demo",
                        "action": "migration_async",
                    },
                },
            },
        )
        async_plan = parse_tool_json(async_request)
        assert async_plan["action"] == "migration_async"
        assert async_plan["summary"]["execution_mode"] == "durable_async_v1"
        assert async_plan["summary"]["asynchronous"] is True
        assert async_plan["summary"]["commit"] == commit
        ApprovalManager(root=approval_root).approve(async_plan["approval_id"])
        holder["approval_id"] = async_plan["approval_id"]

        rejected_private_evidence = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 161,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": async_plan["approval_id"],
                        "expected_commit": commit,
                    },
                },
            },
        )
        assert '"isError":true' in rejected_private_evidence.text
        assert (
            ApprovalManager(root=approval_root)
            .status(async_plan["approval_id"])["state"]
            == "approved"
        )

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 162,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": async_plan["approval_id"],
                    },
                },
            },
        )
        started_payload = parse_tool_json(started)
        assert started_payload["job_id"] == "f" * 32
        assert started_payload["state"] == "queued"
        assert "expected_binding_fingerprint" not in started_payload
        assert "expected_commit" not in started_payload

        base_binding = {
            "environment": "staging",
            "repository": "example/demo",
            "database": registry.projects["demo"].database.model_dump(mode="json"),
            "source": {"commit": commit, "clean": True},
        }
        fake_runner = holder["runner"]
        assert isinstance(fake_runner, FakeMigrationJobRunner)
        assert fake_runner.starts == [
            (
                "demo",
                migration_binding_fingerprint(base_binding),
                commit,
            )
        ]

        status = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 163,
                "method": "tools/call",
                "params": {
                    "name": "migration_job_status",
                    "arguments": {"job_id": "f" * 32},
                },
            },
        )
        status_payload = parse_tool_json(status)
        assert status_payload["state"] == "running"
        assert status_payload["project"] == "demo"

        sync_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 164,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {"project": "demo", "action": "migration"},
                },
            },
        )
        sync_plan = parse_tool_json(sync_request)
        ApprovalManager(root=approval_root).approve(sync_plan["approval_id"])
        holder["approval_id"] = sync_plan["approval_id"]
        sync_cannot_start_async = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 165,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": sync_plan["approval_id"],
                    },
                },
            },
        )
        assert '"isError":true' in sync_cannot_start_async.text
        assert len(fake_runner.starts) == 1

        async_for_sync = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 166,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {
                        "project": "demo",
                        "action": "migration_async",
                    },
                },
            },
        )
        async_for_sync_plan = parse_tool_json(async_for_sync)
        ApprovalManager(root=approval_root).approve(
            async_for_sync_plan["approval_id"]
        )
        async_cannot_apply_sync = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 167,
                "method": "tools/call",
                "params": {
                    "name": "apply_migrations",
                    "arguments": {
                        "project": "demo",
                        "approval_id": async_for_sync_plan["approval_id"],
                    },
                },
            },
        )
        assert '"isError":true' in async_cannot_apply_sync.text

        stopped_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1671,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {
                        "project": "demo",
                        "action": "migration_async",
                    },
                },
            },
        )
        stopped_plan = parse_tool_json(stopped_request)
        ApprovalManager(root=approval_root).approve(stopped_plan["approval_id"])
        holder["approval_id"] = stopped_plan["approval_id"]
        settings.operator_stop_file.write_text("stop\n", encoding="utf-8")
        starts_before_stop = len(fake_runner.starts)
        blocked_by_stop = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1672,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": stopped_plan["approval_id"],
                    },
                },
            },
        )
        assert '"isError":true' in blocked_by_stop.text
        assert len(fake_runner.starts) == starts_before_stop
        assert (
            ApprovalManager(root=approval_root)
            .status(stopped_plan["approval_id"])["state"]
            == "approved"
        )
        settings.operator_stop_file.unlink()

        failing_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 168,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {
                        "project": "demo",
                        "action": "migration_async",
                    },
                },
            },
        )
        failing_plan = parse_tool_json(failing_request)
        ApprovalManager(root=approval_root).approve(failing_plan["approval_id"])
        holder["approval_id"] = failing_plan["approval_id"]
        fake_runner.fail_next = True
        failed_start = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 169,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": failing_plan["approval_id"],
                    },
                },
            },
        )
        assert '"isError":true' in failed_start.text
        assert (
            ApprovalManager(root=approval_root)
            .status(failing_plan["approval_id"])["state"]
            == "consumed"
        )
        starts_after_failure = len(fake_runner.starts)

        retry_consumed = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 170,
                "method": "tools/call",
                "params": {
                    "name": "start_migration_job",
                    "arguments": {
                        "project": "demo",
                        "approval_id": failing_plan["approval_id"],
                    },
                },
            },
        )
        assert '"isError":true' in retry_consumed.text
        assert len(fake_runner.starts) == starts_after_failure

    audit_text = (tmp_path / "async-migration-audit.jsonl").read_text(
        encoding="utf-8"
    )
    assert "start_migration_job" in audit_text
    assert "migration_job_status" in audit_text
    assert "durable_async_v1" not in audit_text
    assert str(tmp_path) not in audit_text


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

        def deploy(
            self,
            project: str,
            *,
            expected_commit: str | None = None,
        ) -> dict:
            assert expected_commit in {None, "a" * 40}
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
        approval_root=tmp_path / "approvals",
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment="staging",
                root=project_root,
                services={
                    "web": ServiceConfig(
                        unit="private-web.service",
                        health_url="http://127.0.0.1:9999/health",
                        allow_restart=True,
                    )
                },
                deployment=DeploymentConfig(
                    release_root=tmp_path / "staging",
                    service="web",
                ),
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

        approval_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 71,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {"project": "demo", "action": "deploy"},
                },
            },
        )
        approval_id = parse_tool_json(approval_request)["approval_id"]
        ApprovalManager(root=settings.approval_root).approve(approval_id)

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 72,
                "method": "tools/call",
                "params": {
                    "name": "deploy_staging",
                    "arguments": {"project": "demo", "approval_id": approval_id},
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


def test_mcp_one_step_rollback_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeRollbackManager:
        def __init__(self, **kwargs) -> None:
            pass

        def plan(self, project: str) -> dict:
            return {"project": project, "environment": "staging", "commit": "b" * 40}

        def deploy(self, project: str) -> dict:
            return {"project": project, "status": "deployed"}

        def list_releases(self, project: str, *, limit: int = 100) -> list[dict]:
            return [
                {
                    "release_id": "new-release",
                    "commit": "b" * 40,
                    "created_at": "2026-09-20T08:00:00+00:00",
                    "previous_release": "old-release",
                    "current": True,
                    "migrations_applied": False,
                    "pre_migration_backup_id": None,
                    "retention_protected": True,
                    "rollback_eligible": True,
                },
                {
                    "release_id": "old-release",
                    "commit": "a" * 40,
                    "created_at": "2026-09-19T08:00:00+00:00",
                    "previous_release": None,
                    "current": False,
                    "migrations_applied": False,
                    "pre_migration_backup_id": None,
                    "retention_protected": True,
                    "rollback_eligible": False,
                },
            ][:limit]

        def rollback_plan(self, project: str) -> dict:
            return {
                "project": project,
                "current_release": "new-release",
                "current_commit": "b" * 40,
                "target_release": "old-release",
                "target_commit": "a" * 40,
                "one_step_only": True,
                "blocked_by_database_migration": False,
                "allowed": True,
                "database_restore_performed": False,
            }

        def rollback_one(
            self,
            project: str,
            *,
            expected_current_release: str | None = None,
            expected_target_release: str | None = None,
        ) -> dict:
            assert expected_current_release in {None, "new-release"}
            assert expected_target_release in {None, "old-release"}
            return {
                **self.rollback_plan(project),
                "status": "rolled_back",
                "current_release": "old-release",
                "health": {"active_state": "active", "health": "healthy"},
            }

    monkeypatch.setattr("runner_mcp.server.DeploymentManager", FakeRollbackManager)
    project_root = tmp_path / "project"
    project_root.mkdir()
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
        deployment_jobs_root=tmp_path / "deployment-jobs",
        approval_root=tmp_path / "approvals",
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

        releases = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 100,
                "method": "tools/call",
                "params": {
                    "name": "list_releases",
                    "arguments": {"project": "demo"},
                },
            },
        )
        release_payload = parse_tool_json(releases)
        assert release_payload[0]["current"] is True
        assert release_payload[0]["rollback_eligible"] is True
        assert str(tmp_path) not in releases.text

        plan = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 101,
                "method": "tools/call",
                "params": {
                    "name": "rollback_plan",
                    "arguments": {"project": "demo"},
                },
            },
        )
        plan_payload = parse_tool_json(plan)
        assert plan_payload["target_release"] == "old-release"
        assert plan_payload["one_step_only"] is True
        assert plan_payload["database_restore_performed"] is False

        arbitrary_target = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 102,
                "method": "tools/call",
                "params": {
                    "name": "rollback_release",
                    "arguments": {
                        "project": "demo",
                        "target_release": "attacker-selected-release",
                    },
                },
            },
        )
        assert '"isError":true' in arbitrary_target.text

        approval_request = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 103,
                "method": "tools/call",
                "params": {
                    "name": "request_action_approval",
                    "arguments": {"project": "demo", "action": "code_rollback"},
                },
            },
        )
        approval_id = parse_tool_json(approval_request)["approval_id"]
        ApprovalManager(root=settings.approval_root).approve(approval_id)

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 104,
                "method": "tools/call",
                "params": {
                    "name": "rollback_release",
                    "arguments": {"project": "demo", "approval_id": approval_id},
                },
            },
        )
        started_payload = parse_tool_json(started)
        assert started_payload["operation"] == "rollback"
        job_id = started_payload["job_id"]

        deadline = time.monotonic() + 3
        rollback_payload = None
        request_id = 103
        while time.monotonic() < deadline:
            status = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "rollback_status",
                        "arguments": {"job_id": job_id},
                    },
                },
            )
            rollback_payload = parse_tool_json(status)
            if rollback_payload["state"] not in {"queued", "running"}:
                break
            request_id += 1
            time.sleep(0.01)

        assert rollback_payload is not None
        assert rollback_payload["state"] == "completed"
        assert rollback_payload["operation"] == "rollback"
        assert rollback_payload["result"]["status"] == "rolled_back"
        assert rollback_payload["result"]["current_release"] == "old-release"

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "list_releases" in audit_text
    assert "rollback_plan" in audit_text
    assert "rollback_release" in audit_text
    assert "rollback_status" in audit_text
    assert str(tmp_path) not in audit_text


def test_mcp_adapter_capabilities_are_path_safe(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        retention_confirmed=True,
    )
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                adapter="python",
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
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )
        adapters = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 120,
                "method": "tools/call",
                "params": {"name": "list_project_adapters", "arguments": {}},
            },
        )
        assert [item["id"] for item in parse_tool_json(adapters)] == ["generic", "python"]

        capabilities = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 121,
                "method": "tools/call",
                "params": {
                    "name": "project_capabilities",
                    "arguments": {"project": "demo"},
                },
            },
        )
        payload = parse_tool_json(capabilities)
        assert payload["adapter"] == "python"
        assert payload["inspection"]["pyproject_present"] is True
        assert str(project_root) not in capabilities.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "list_project_adapters" in audit_text
    assert "project_capabilities" in audit_text
    assert str(project_root) not in audit_text


def test_configured_fabric_bridge_exposes_only_coarse_work_unit_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    calls: list[tuple[str, dict]] = []

    class FakeFabricBridge:
        def __init__(self, _config) -> None:
            pass

        def external_target_preflight(self):
            calls.append(("external_target_preflight", {}))
            return {
                "schemaVersion": "runner.fabric/external-target-preflight/v1",
                "ready": True,
                "targetAllocationId": "11111111-1111-4111-8111-111111111111",
                "environmentId": "22222222-2222-4222-8222-222222222222",
                "mutationEnabled": False,
                "networkChecked": False,
            }

        def external_target_inspect(self):
            calls.append(("external_target_inspect", {}))
            return {
                "schemaVersion": "runner.fabric/external-target-live-qualification/v1",
                "contractVersion": "runner.fabric/external-target-inspection/v1alpha1",
                "targetAllocationId": "11111111-1111-4111-8111-111111111111",
                "environmentId": "22222222-2222-4222-8222-222222222222",
                "reachability": "reachable",
                "readiness": "ready",
                "observedAt": "2026-10-04T17:30:00+00:00",
                "reasonCode": "healthy",
                "releaseRevision": "a" * 40,
                "evidenceRefs": ["external-target:fixed-readonly-adapter"],
                "liveMutationEnabled": False,
            }

        def host_inspect(self):
            calls.append(("inspect", {}))
            return {
                "schema_version": "runner.fabric/host-inspection/v1",
                "mutation_enabled": False,
                "host": {
                    "id": "host:local",
                    "display_name": "Runner Fabric host",
                    "freshness": {
                        "state": "fresh",
                        "observed_at": "2026-10-04T00:00:00+00:00",
                        "age_seconds": 0,
                    },
                    "cpu": {},
                    "memory": {},
                    "swap": {},
                    "pressure": {},
                    "filesystems": [],
                    "disks": [],
                    "network": [],
                    "uptime_seconds": {
                        "state": "available",
                        "value": 1,
                        "unit": "seconds",
                    },
                    "oom_kills": {
                        "state": "available",
                        "value": 0,
                        "unit": "count",
                    },
                    "process_count": {
                        "state": "available",
                        "value": 1,
                        "unit": "count",
                    },
                    "collector": {},
                },
                "browsers": [
                    {
                        "runtime": "chromium",
                        "state": "unavailable",
                        "cache_ready": False,
                    },
                    {
                        "runtime": "chrome",
                        "state": "unavailable",
                        "cache_ready": False,
                    },
                    {
                        "runtime": "firefox",
                        "state": "unavailable",
                        "cache_ready": False,
                    },
                    {
                        "runtime": "webkit",
                        "state": "unavailable",
                        "cache_ready": False,
                    },
                ],
            }

        def run_work_unit(self, **kwargs):
            calls.append(("run", kwargs))
            return {
                "state": "complete",
                "expected_revision": "a" * 40,
                "commit_revision": "b" * 40,
                "pushed_revision": "b" * 40,
                "change_reference": "change:109",
                "report_reference": "report:109",
                "corrections_used": 0,
                "reported": True,
                "evidence": [],
            }

        def get_work_unit(self, work_unit_id: str):
            calls.append(("get", {"work_unit_id": work_unit_id}))
            return {
                "work_unit_id": work_unit_id,
                "project_id": "project:runner-fabric",
                "work_item_id": "issue:109",
                "status": "complete",
                "result": {
                    "state": "complete",
                    "expected_revision": "a" * 40,
                    "commit_revision": "b" * 40,
                    "pushed_revision": "b" * 40,
                    "change_reference": "change:109",
                    "report_reference": "report:109",
                    "corrections_used": 0,
                    "reported": True,
                    "evidence": [],
                },
            }

        def cancel_work_unit(self, work_unit_id: str):
            calls.append(("cancel", {"work_unit_id": work_unit_id}))
            return {
                "work_unit_id": work_unit_id,
                "project_id": "project:runner-fabric",
                "work_item_id": "issue:109",
                "status": "complete",
                "result": {
                    "state": "complete",
                    "expected_revision": "a" * 40,
                    "commit_revision": "b" * 40,
                    "pushed_revision": "b" * 40,
                    "change_reference": "change:109",
                    "report_reference": "report:109",
                    "corrections_used": 0,
                    "reported": True,
                    "evidence": [],
                },
            }

    monkeypatch.setattr("runner_mcp.server.FabricBridgeClient", FakeFabricBridge)

    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
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
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200
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
        assert listed.status_code == 200
        for tool_name in (
            "fabric_external_target_preflight",
            "fabric_external_target_inspect",
            "fabric_run_work_unit",
            "fabric_get_work_unit",
            "fabric_cancel_work_unit",
        ):
            assert tool_name in listed.text

        inspected = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fabric_host_inspect",
                    "arguments": {},
                },
            },
        )
        inspection = parse_tool_json(inspected)
        assert inspection["schema_version"] == "runner.fabric/host-inspection/v1"
        assert inspection["mutation_enabled"] is False

        preflight = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "fabric_external_target_preflight",
                    "arguments": {},
                },
            },
        )
        preflight_payload = parse_tool_json(preflight)
        assert preflight_payload["ready"] is True
        assert preflight_payload["mutationEnabled"] is False
        assert "hostname" not in preflight.text.casefold()

        external_inspection = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 32,
                "method": "tools/call",
                "params": {
                    "name": "fabric_external_target_inspect",
                    "arguments": {},
                },
            },
        )
        external_payload = parse_tool_json(external_inspection)
        assert external_payload["readiness"] == "ready"
        assert external_payload["liveMutationEnabled"] is False
        assert "hostname" not in external_inspection.text.casefold()
        assert "private_path" not in external_inspection.text.casefold()

        started = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fabric_run_work_unit",
                    "arguments": {
                        "work_unit_id": "wu:109",
                        "project_id": "project:runner-fabric",
                        "work_item_id": "issue:109",
                        "expected_revision": "a" * 40,
                        "change_plan_id": "plan:109",
                    },
                },
            },
        )
        payload = parse_tool_json(started)
        assert payload["state"] == "complete"
        assert payload["commit_revision"] == "b" * 40

    assert calls == [
        ("inspect", {}),
        ("external_target_preflight", {}),
        ("external_target_inspect", {}),
        (
            "run",
            {
                "work_unit_id": "wu:109",
                "project_id": "project:runner-fabric",
                "work_item_id": "issue:109",
                "expected_revision": "a" * 40,
                "change_plan_id": "plan:109",
                "validation_profile": "foundation",
                "correction_budget": 1,
                "landing_mode": "managed_branch_push",
            },
        )
    ]
    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_host_inspect" in audit_text
    assert "fabric_run_work_unit" in audit_text
    assert "wu:109" in audit_text
    assert "127.0.0.1" not in audit_text
    assert "f" * 32 not in audit_text


def test_fabric_host_inspect_failure_returns_bounded_diagnostic(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    class FailingFabricBridge:
        def __init__(self, _config) -> None:
            pass

        def host_inspect(self):
            raise FabricBridgeError("Runner Fabric host inspection failed")

    monkeypatch.setattr("runner_mcp.server.FabricBridgeClient", FailingFabricBridge)

    settings = Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
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
    headers = auth_headers()

    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        initialized = client.post("/mcp", headers=headers, json=initialize_message())
        assert initialized.status_code == 200
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
                "id": 300,
                "method": "tools/call",
                "params": {
                    "name": "fabric_host_inspect",
                    "arguments": {},
                },
            },
        )

    payload = parse_tool_json(response)
    assert payload == {
        "schema_version": "runner-mcp/fabric-host-inspection-error/v1",
        "state": "unavailable",
        "error_category": "fabric_inspection_unavailable",
        "mutation_enabled": False,
    }
    assert "127.0.0.1" not in response.text
    assert "f" * 32 not in response.text

    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "fabric_host_inspect" in audit_text
