"""FASTER-13: meet het echte MCP-ASGI-pad zonder externe netwerkverbinding.

De bestaande Runner-MCP create_app verwerkt MCP-handshake en read-only tools via
Starlette TestClient. Een tijdelijke projectmap en testtoken voorkomen contact
met de actieve dienst, Fabric of providers. Tijden zijn alleen ASGI-in-process
indicaties: geen TCP/HTTP-loopback-RTT, productiebenchmark of prestatiedrempel.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.server import Settings, create_app


def _settings(tmp_path: Path) -> Settings:
    """Maak een volledig geïsoleerde serverconfiguratie met vaste testidentiteit."""
    return Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "missing.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
    )


def _headers() -> dict[str, str]:
    """Houd token en content negotiation uitsluitend binnen het testproces."""
    return {
        "Authorization": "Bearer " + "x" * 32,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }


def _message(identifier: int, name: str) -> dict[str, object]:
    """Roep uitsluitend een bestaande read-only tool aan."""
    return {
        "jsonrpc": "2.0",
        "id": identifier,
        "method": "tools/call",
        "params": {"name": name, "arguments": {}},
    }


def test_authenticated_mcp_asgi_latency_and_session_fail_closed(tmp_path: Path) -> None:
    """Meet een klein read-only monster en toets auth/sessiebinding.

    Elke respons moet dezelfde request-id teruggeven. We stellen bewust geen
    maximumduur: variërende CI-belasting mag een geldige build niet afkeuren.
    """
    project = tmp_path / "project"
    project.mkdir()
    app = create_app(
        settings=_settings(tmp_path),
        registry=ProjectRegistry(
            projects={
                "demo": ProjectConfig(
                    display_name="Demo", repository="example/demo", root=project
                )
            }
        ),
    )
    headers = _headers()
    measurements_ns: list[int] = []
    with TestClient(app, base_url="https://mcp.example.invalid") as client:
        unauthorized = client.post(
            "/mcp",
            headers={key: value for key, value in headers.items() if key != "Authorization"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert unauthorized.status_code == 401

        initialized = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "faster13-isolated", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200
        session = initialized.headers["mcp-session-id"]
        headers["Mcp-Session-Id"] = session

        notified = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )
        assert notified.status_code == 202

        for request_id in range(10, 16):
            started = time.perf_counter_ns()
            reply = client.post("/mcp", headers=headers, json=_message(request_id, "safety_status"))
            measurements_ns.append(time.perf_counter_ns() - started)
            assert reply.status_code == 200
            event = next(line for line in reply.text.splitlines() if line.startswith("data: "))
            payload = json.loads(event.removeprefix("data: "))
            assert payload["id"] == request_id
            assert payload["result"]["isError"] is False

        stale_headers = {**headers, "Mcp-Session-Id": "unknown-session-faster13"}
        stale = client.post(
            "/mcp", headers=stale_headers, json=_message(20, "safety_status")
        )
        assert 400 <= stale.status_code < 500

        # Een foute sessie mag de geldige bestaande sessie niet ongeldig maken.
        surviving = client.post(
            "/mcp", headers=headers, json=_message(21, "safety_status")
        )
        assert surviving.status_code == 200

    # Alleen lokale samples controleren; publiceer geen ongegronde RTT-claims.
    assert len(measurements_ns) == 6
    assert min(measurements_ns) > 0
    assert statistics.median(measurements_ns) > 0
