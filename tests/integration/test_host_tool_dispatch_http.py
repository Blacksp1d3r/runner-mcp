"""Real authenticated HTTP tools/call qualification for the PRIVATE #642 gate.

No signed policy, live service credential, real host or deployment is used.
The only evidence provider here returns an unqualified synthetic record,
so every guarded tool call must be denied before its handler is invoked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.file_access import FileAccessService
from runner_mcp.host_tool_dispatch import HostDispatchEvidence
from runner_mcp.server import Settings, create_app

TOKEN = "x" * 32
ENDPOINT = "https://mcp.example.invalid"


def _app(tmp_path: Path, *, evidence_provider=None):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "sentinel.txt").write_text(
        "PRIVATE_DISPOSABLE_FILE_MARKER", encoding="utf-8"
    )
    settings = Settings(
        bearer_token=TOKEN,
        auth_issuer="https://auth.example.invalid/",
        resource_url=ENDPOINT + "/mcp",
        projects_config=tmp_path / "unused.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
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
    return create_app(
        settings=settings,
        registry=registry,
        host_dispatch_evidence_provider=evidence_provider,
    )


def _session(client: TestClient):
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    handshake = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "private-gate-test", "version": "1"},
            },
        },
    )
    assert handshake.status_code == 200
    session = handshake.headers["mcp-session-id"]
    headers["Mcp-Session-Id"] = session
    ready = client.post(
        "/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    )
    assert ready.status_code == 202
    return headers


def _read(client: TestClient, headers: dict[str, str]):
    return client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "read_project_file",
                "arguments": {"project": "demo", "path": "sentinel.txt"},
            },
        },
    )


def test_authenticated_wire_denial_cannot_reach_registered_handler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    invoked = {"count": 0}

    def forbidden_handler(*_args: object, **_kwargs: object):
        invoked["count"] += 1
        raise AssertionError("never execute the registered file handler")

    monkeypatch.setattr(FileAccessService, "read_file", forbidden_handler)
    app = _app(
        tmp_path,
        evidence_provider=lambda: HostDispatchEvidence(
            verified_service_asset_id="service:synthetic",
            runtime_source_revision="a" * 40,
            policy=None,
        ),
    )
    with TestClient(app, base_url=ENDPOINT) as client:
        headers = _session(client)
        names = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}},
        )
        assert names.status_code == 200
        assert "read_project_file" in names.text
        refused = _read(client, headers)
        assert refused.status_code == 200
        assert "HOST_TOOL_NOT_PERMITTED" in refused.text
        assert "isError" in refused.text
        assert "PRIVATE_DISPOSABLE_FILE_MARKER" not in refused.text
    assert invoked["count"] == 0
    lines = [
        json.loads(line)
        for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    denies = [row for row in lines if row.get("result") == "denied:host_policy_unavailable"]
    assert len(denies) == 1
    assert denies[0]["tool"] == "read_project_file"
    assert "PRIVATE_DISPOSABLE_FILE_MARKER" not in json.dumps(lines)


def test_authenticated_wire_provider_failure_is_fixed_denial(tmp_path: Path):
    def unavailable():
        raise OSError("private/key/material/must/not/leak")

    app = _app(tmp_path, evidence_provider=unavailable)
    with TestClient(app, base_url=ENDPOINT) as client:
        headers = _session(client)
        refused = _read(client, headers)
        assert refused.status_code == 200
        assert "HOST_TOOL_NOT_PERMITTED" in refused.text
        assert "private/key/material" not in refused.text
    rows = [
        json.loads(line)
        for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len([
        x for x in rows if x.get("result") == "denied:host_admission_evidence_unavailable"
    ]) == 1


def test_default_server_retains_existing_tool_dispatch_without_private_gate(tmp_path: Path):
    app = _app(tmp_path)
    with TestClient(app, base_url=ENDPOINT) as client:
        headers = _session(client)
        response = _read(client, headers)
        assert response.status_code == 200
        assert "PRIVATE_DISPOSABLE_FILE_MARKER" in response.text
        assert "HOST_TOOL_NOT_PERMITTED" not in response.text
