from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .audit import AuditEvent, AuditLogger, utc_timestamp
from .config import ProjectRegistry, load_project_registry


@dataclass(frozen=True)
class Settings:
    bearer_token: str
    auth_issuer: str
    resource_url: str
    projects_config: Path
    audit_log: Path

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("RUNNER_MCP_BEARER_TOKEN", "")
        if len(token) < 32:
            raise RuntimeError("RUNNER_MCP_BEARER_TOKEN must contain at least 32 characters")
        issuer = os.getenv("RUNNER_MCP_AUTH_ISSUER", "")
        resource = os.getenv("RUNNER_MCP_RESOURCE_URL", "")
        if not issuer or not resource:
            raise RuntimeError("Authentication issuer and MCP resource URL are required")
        return cls(
            bearer_token=token,
            auth_issuer=issuer,
            resource_url=resource,
            projects_config=Path(os.getenv("RUNNER_MCP_PROJECTS_CONFIG", "config/projects.yml")),
            audit_log=Path(os.getenv("RUNNER_MCP_AUDIT_LOG", "var/audit.jsonl")),
        )


class StaticBearerVerifier(TokenVerifier):
    def __init__(self, expected_token: str, resource_url: str) -> None:
        self.expected_token = expected_token
        self.resource_url = resource_url
    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, self.expected_token):
            return None
        return AccessToken(
            token=token,
            client_id="runner-mcp-operator",
            scopes=["runner:read"],
            resource=self.resource_url,
        )


def build_mcp(settings: Settings, registry: ProjectRegistry, audit: AuditLogger) -> MCPServer:
    mcp = MCPServer(
        "Runner MCP",
        token_verifier=StaticBearerVerifier(settings.bearer_token, settings.resource_url),
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(settings.auth_issuer),
            resource_server_url=AnyHttpUrl(settings.resource_url),
            required_scopes=["runner:read"],
            validate_token_resource=True,
        ),
    )

    @mcp.tool()
    def list_projects() -> list[dict[str, str]]:
        """List only the projects explicitly configured for Runner MCP."""
        request_id = str(uuid4())
        result = [cfg.public_summary(code) for code, cfg in sorted(registry.projects.items())]
        audit.append(
            AuditEvent(request_id, "list_projects", None, "authenticated-client", "ok", utc_timestamp())
        )
        return result

    @mcp.tool()
    def project_status(project: str) -> dict[str, str]:
        """Return a safe registration-level status for one allow-listed project."""
        request_id = str(uuid4())
        cfg = registry.projects.get(project)
        if cfg is None:
            audit.append(
                AuditEvent(
                    request_id,
                    "project_status",
                    project,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("Unknown or disabled project")

        result = cfg.public_summary(project)
        result["status"] = "registered"
        audit.append(
            AuditEvent(
                request_id,
                "project_status",
                project,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    return mcp


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_app() -> Starlette:
    settings = Settings.from_env()
    registry = load_project_registry(settings.projects_config)
    audit = AuditLogger(settings.audit_log)
    mcp = build_mcp(settings, registry, audit)

    @asynccontextmanager
    async def lifespan(_: Starlette):
        async with mcp.session_manager.run():
            yield
    return Starlette(
        routes=[
            Route("/healthz", health, methods=["GET"]),
            Mount("/", app=mcp.streamable_http_app()),
        ],
        lifespan=lifespan,
    )
