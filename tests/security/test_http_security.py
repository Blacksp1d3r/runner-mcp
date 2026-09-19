from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.http_middleware import RateLimitMiddleware, RequestIdMiddleware
from runner_mcp.server import Settings, create_app


async def ok(_):
    return JSONResponse({"ok": True})


def test_request_id_and_rate_limit() -> None:
    app = Starlette(
        routes=[
            Route("/healthz", ok),
            Route("/mcp", ok),
        ],
        middleware=[
            Middleware(RequestIdMiddleware),
            Middleware(
                RateLimitMiddleware,
                max_requests=2,
                window_seconds=60,
            ),
        ],
    )

    with TestClient(app) as client:
        first = client.get("/mcp")
        second = client.get("/mcp")
        limited = client.get("/mcp")
        health = client.get("/healthz")

    assert first.status_code == 200
    assert second.status_code == 200
    assert limited.status_code == 429
    assert limited.json() == {"error": "rate_limit_exceeded"}
    assert limited.headers["retry-after"] == "60"
    assert "x-request-id" in first.headers
    assert "x-request-id" in limited.headers
    assert health.status_code == 200


def test_mcp_requires_authentication(tmp_path: Path) -> None:
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
                root="runtime-root",
            )
        }
    )
    app = create_app(settings=settings, registry=registry)

    with TestClient(app) as client:
        health = client.get("/healthz")
        denied = client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1"},
                },
            },
        )

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert "x-request-id" in health.headers
    assert denied.status_code == 401
