"""Real authenticated HTTP tools/call qualification for the PRIVATE #642 gate.

No signed policy, live service credential, real host or deployment is used.
The only evidence provider here returns an unqualified synthetic record,
so every guarded tool call must be denied before its handler is invoked.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from time import time

import pytest
from starlette.testclient import TestClient

from runner_mcp.audit import AuditLogger
from runner_mcp.build_identity import BuildIdentity
from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.file_access import FileAccessService
from runner_mcp.host_tool_admission import QualifiedHostToolPolicy
from runner_mcp.host_tool_dispatch import HostDispatchEvidence
from runner_mcp.server import (
    BewindOcrQualificationExecutionAuthorityConfigurator,
    BewindOcrQualificationRunner,
    BewindOcrQualificationSourceProvisioner,
    BewindOcrQualificationStager,
    BewindOcrRuntimeImagePreparer,
    Settings,
    build_mcp,
    create_app,
    runner_mcp_interface_schema_digest,
)

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


def _synthetic_real_server_schema(tmp_path: Path) -> str:
    """Measure the actual SDK catalogue, not a hand-entered policy digest."""
    project_root = tmp_path / "schema-reference"
    project_root.mkdir()
    settings = Settings(
        bearer_token=TOKEN,
        auth_issuer="https://auth.example.invalid/",
        resource_url=ENDPOINT + "/mcp",
        projects_config=tmp_path / "reference.yml",
        audit_log=tmp_path / "schema-audit.jsonl",
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
    mcp = build_mcp(
        settings,
        registry,
        AuditLogger(settings.audit_log),
        # The real create_app also registers its build_identity tool.
        build_identity_provider=lambda: BuildIdentity("runner-mcp", "synthetic"),
    )
    return asyncio.run(runner_mcp_interface_schema_digest(mcp))


def _synthetic_host_permit(*, host: str, schema: str, allow_read: bool):
    return QualifiedHostToolPolicy(
        service_asset_id=host,
        release_source_revision="a" * 40,
        interface_schema_sha256=schema,
        permitted_tool_names=(
            frozenset({"read_project_file"}) if allow_read else frozenset()
        ),
        expires_at_epoch=int(time()) + 1800,
    )


def _private_host_app(tmp_path: Path, *, observed_asset: str, policy):
    tmp_path.mkdir()
    return _app(
        tmp_path,
        evidence_provider=lambda: HostDispatchEvidence(
            verified_service_asset_id=observed_asset,
            runtime_source_revision="a" * 40,
            policy=policy,
        ),
    )


def _listed(client: TestClient, headers: dict[str, str]):
    return client.post(
        "/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}},
    )


def test_synthetic_primary_and_lab_publish_same_tools_but_deny_or_allow_locally(
    tmp_path: Path,
):
    schema = _synthetic_real_server_schema(tmp_path)
    assert len(schema) == 64
    primary = _synthetic_host_permit(
        host="service:primary", schema=schema, allow_read=False
    )
    lab = _synthetic_host_permit(
        host="service:lab", schema=schema, allow_read=True
    )
    # The permits and independently observed service names are synthetic.
    # This proves SDK HTTP policy mechanics, NEVER a real qualified identity.
    primary_app = _private_host_app(
        tmp_path / "primary", observed_asset="service:primary", policy=primary
    )
    lab_app = _private_host_app(
        tmp_path / "lab", observed_asset="service:lab", policy=lab
    )
    with (
        TestClient(primary_app, base_url=ENDPOINT) as primary_client,
        TestClient(lab_app, base_url=ENDPOINT) as lab_client,
    ):
        primary_headers = _session(primary_client)
        lab_headers = _session(lab_client)
        primary_tools = _listed(primary_client, primary_headers)
        lab_tools = _listed(lab_client, lab_headers)
        assert primary_tools.status_code == lab_tools.status_code == 200
        assert primary_tools.text == lab_tools.text
        assert "read_project_file" in primary_tools.text

        denied = _read(primary_client, primary_headers)
        assert denied.status_code == 200
        assert "HOST_TOOL_NOT_PERMITTED" in denied.text
        assert "PRIVATE_DISPOSABLE_FILE_MARKER" not in denied.text

        accepted = _read(lab_client, lab_headers)
        assert accepted.status_code == 200
        assert "PRIVATE_DISPOSABLE_FILE_MARKER" in accepted.text
        assert "HOST_TOOL_NOT_PERMITTED" not in accepted.text

    audit = [
        json.loads(line)
        for line in (tmp_path / "primary" / "audit.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len([
        row for row in audit if row.get("result") == "denied:tool_not_granted_on_host"
    ]) == 1


def test_lab_permit_replay_on_primary_is_denied_at_actual_http_tool_dispatch(
    tmp_path: Path,
):
    schema = _synthetic_real_server_schema(tmp_path)
    foreign = _synthetic_host_permit(
        host="service:lab", schema=schema, allow_read=True
    )
    app = _private_host_app(
        tmp_path / "foreign-replay",
        observed_asset="service:primary",
        policy=foreign,
    )
    with TestClient(app, base_url=ENDPOINT) as client:
        headers = _session(client)
        denied = _read(client, headers)
        assert denied.status_code == 200
        assert "HOST_TOOL_NOT_PERMITTED" in denied.text
        assert "PRIVATE_DISPOSABLE_FILE_MARKER" not in denied.text

    audit = [
        json.loads(line)
        for line in (tmp_path / "foreign-replay" / "audit.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len([
        row for row in audit if row.get("result") == "denied:host_identity_mismatch"
    ]) == 1

OCR_HOST_RESTRICTED_TOOLS = (
    "bewind_ocr_qualification_run",
    "bewind_ocr_qualification_stage",
    "bewind_ocr_runtime_image_prepare",
    "bewind_ocr_qualification_source_provision",
    "bewind_ocr_qualification_execution_authority_configure",
)


def test_all_five_real_ocr_tools_are_denied_over_authenticated_http_before_handlers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Same live catalogue; deny five lab-only names before any real OCR code."""
    schema = _synthetic_real_server_schema(tmp_path)
    executed = {"count": 0}

    def forbidden_ocr(*_args: object, **_kwargs: object):
        executed["count"] += 1
        raise AssertionError("OCR action must not reach its handler")

    # Patch the actual five mutation-capable implementations, NOT the SDK
    # call_tool method. A failed pre-dispatch gate must leave them untouched.
    for cls, method in (
        (BewindOcrQualificationRunner, "run"),
        (BewindOcrQualificationStager, "stage"),
        (BewindOcrRuntimeImagePreparer, "prepare"),
        (BewindOcrQualificationSourceProvisioner, "provision"),
        (BewindOcrQualificationExecutionAuthorityConfigurator, "configure"),
    ):
        monkeypatch.setattr(cls, method, forbidden_ocr)

    primary_permit = _synthetic_host_permit(
        host="service:primary", schema=schema, allow_read=True,
    )
    app = _private_host_app(
        tmp_path / "ocr-primary",
        observed_asset="service:primary",
        policy=primary_permit,
    )
    with TestClient(app, base_url=ENDPOINT) as client:
        headers = _session(client)
        catalogue = _listed(client, headers)
        assert catalogue.status_code == 200
        for name in OCR_HOST_RESTRICTED_TOOLS:
            assert name in catalogue.text
        for n, name in enumerate(OCR_HOST_RESTRICTED_TOOLS, start=100):
            refused = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": n,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {}},
                },
            )
            assert refused.status_code == 200
            assert "HOST_TOOL_NOT_PERMITTED" in refused.text
            assert "isError" in refused.text
            assert "OCR action must not reach its handler" not in refused.text
    assert executed["count"] == 0
    records = [
        json.loads(line)
        for line in (tmp_path / "ocr-primary" / "audit.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    refused_events = [
        row for row in records
        if row.get("result") == "denied:tool_not_granted_on_host"
    ]
    assert len(refused_events) == len(OCR_HOST_RESTRICTED_TOOLS)
    assert {record["tool"] for record in refused_events} == set(
        OCR_HOST_RESTRICTED_TOOLS
    )


def test_unknown_client_tool_name_never_leaks_into_durable_http_audit(
    tmp_path: Path,
):
    marker = "synthetic_client_credential_not_a_registered_tool_31415"
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
        refusal = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {"name": marker, "arguments": {}},
            },
        )
        assert refusal.status_code == 200
        assert "HOST_TOOL_NOT_PERMITTED" in refusal.text
        assert marker not in refusal.text
    audit_content = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert marker not in audit_content
    audit_rows = [json.loads(line) for line in audit_content.splitlines()]
    unknowns = [row for row in audit_rows if row.get("tool") == "unknown_tool"]
    assert len(unknowns) == 1
    assert unknowns[0]["result"].startswith("denied:")
