from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .audit import AuditEvent, AuditLogger, utc_timestamp
from .config import ProjectRegistry, load_project_registry
from .file_access import FileAccessError, FileAccessService
from .http_middleware import RateLimitMiddleware, RequestIdMiddleware, current_request_id
from .operational_safety import OperatorSafetyGuard, RetentionPolicy


@dataclass(frozen=True)
class Settings:
    bearer_token: str
    auth_issuer: str
    resource_url: str
    projects_config: Path
    audit_log: Path
    rate_limit_per_minute: int = 60
    retention_policy: RetentionPolicy = field(default_factory=RetentionPolicy)
    operator_stop_file: Path | None = None
    retention_confirmed: bool = True

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("RUNNER_MCP_BEARER_TOKEN", "")
        if len(token) < 32:
            raise RuntimeError("RUNNER_MCP_BEARER_TOKEN must contain at least 32 characters")
        issuer = os.getenv("RUNNER_MCP_AUTH_ISSUER", "")
        resource = os.getenv("RUNNER_MCP_RESOURCE_URL", "")
        if not issuer or not resource:
            raise RuntimeError("Authentication issuer and MCP resource URL are required")

        try:
            rate_limit = int(os.getenv("RUNNER_MCP_RATE_LIMIT_PER_MINUTE", "60"))
        except ValueError as exc:
            raise RuntimeError("RUNNER_MCP_RATE_LIMIT_PER_MINUTE must be an integer") from exc
        if not 1 <= rate_limit <= 6000:
            raise RuntimeError("RUNNER_MCP_RATE_LIMIT_PER_MINUTE must be between 1 and 6000")

        stop_file_raw = os.getenv("RUNNER_MCP_OPERATOR_STOP_FILE", "").strip()
        retention_confirmed_raw = os.getenv(
            "RUNNER_MCP_RETENTION_CONFIRMED",
            "false",
        ).strip().lower()
        if retention_confirmed_raw not in {"true", "false"}:
            raise RuntimeError("RUNNER_MCP_RETENTION_CONFIRMED must be true or false")

        return cls(
            bearer_token=token,
            auth_issuer=issuer,
            resource_url=resource,
            projects_config=Path(os.getenv("RUNNER_MCP_PROJECTS_CONFIG", "config/projects.yml")),
            audit_log=Path(os.getenv("RUNNER_MCP_AUDIT_LOG", "var/audit.jsonl")),
            rate_limit_per_minute=rate_limit,
            retention_policy=RetentionPolicy.from_env(),
            operator_stop_file=Path(stop_file_raw) if stop_file_raw else None,
            retention_confirmed=retention_confirmed_raw == "true",
        )


def transport_security_for(resource_url: str) -> TransportSecuritySettings:
    parsed = urlsplit(resource_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("RUNNER_MCP_RESOURCE_URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise RuntimeError("RUNNER_MCP_RESOURCE_URL must not contain credentials")

    origin = f"{parsed.scheme}://{parsed.netloc}"
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[parsed.netloc],
        allowed_origins=[origin],
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


def build_mcp(
    settings: Settings,
    registry: ProjectRegistry,
    audit: AuditLogger,
    safety_guard: OperatorSafetyGuard | None = None,
) -> MCPServer:
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
    files = FileAccessService(registry)
    safety = safety_guard or OperatorSafetyGuard(
        stop_file=settings.operator_stop_file,
        retention=settings.retention_policy,
        retention_confirmed=settings.retention_confirmed,
    )

    @mcp.tool()
    def list_projects() -> list[dict[str, str]]:
        """List only the projects explicitly configured for Runner MCP."""
        request_id = current_request_id()
        result = [cfg.public_summary(code) for code, cfg in sorted(registry.projects.items())]
        audit.append(
            AuditEvent(request_id, "list_projects", None, "authenticated-client", "ok", utc_timestamp())
        )
        return result

    @mcp.tool()
    def safety_status() -> dict:
        """Return operator-stop and rollback-retention safety status without private paths."""
        request_id = current_request_id()
        status = safety.status()
        result = {
            "operator_stop_configured": status.configured,
            "operator_stop_active": status.stop_active,
            "retention_confirmed": safety.retention_confirmed,
            "mode": status.mode,
            "min_releases_to_keep": safety.retention.min_releases_to_keep,
            "min_release_age_days": safety.retention.min_release_age_days,
            "pitr_retention_days": safety.retention.pitr_retention_days,
            "pre_migration_backup_days": safety.retention.pre_migration_backup_days,
            "max_automatic_code_rollback_steps": (
                safety.retention.max_automatic_code_rollback_steps
            ),
            "database_restore_requires_explicit_approval": (
                safety.retention.database_restore_requires_explicit_approval
            ),
            "automatic_production_database_restore": (
                safety.retention.automatic_production_database_restore
            ),
        }
        audit.append(
            AuditEvent(
                request_id,
                "safety_status",
                None,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def project_status(project: str) -> dict[str, str]:
        """Return a safe registration-level status for one allow-listed project."""
        request_id = current_request_id()
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

    def _run_file_tool(
        tool_name: str,
        project: str,
        operation,
    ):
        request_id = current_request_id()
        try:
            result = operation()
        except FileAccessError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    tool_name,
                    project,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None

        audit.append(
            AuditEvent(
                request_id,
                tool_name,
                project,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def read_project_file(
        project: str,
        path: str,
        offset: int = 0,
        length: int = 200,
    ) -> dict:
        """Read a bounded page from an allowed UTF-8 project text file."""
        return _run_file_tool(
            "read_project_file",
            project,
            lambda: files.read_file(project, path, offset=offset, length=length),
        )

    @mcp.tool()
    def list_project_files(
        project: str,
        path: str = "",
        offset: int = 0,
        limit: int = 100,
    ) -> dict:
        """List one allowed project directory without recursive traversal."""
        return _run_file_tool(
            "list_project_files",
            project,
            lambda: files.list_files(project, path, offset=offset, limit=limit),
        )

    @mcp.tool()
    def file_metadata(project: str, path: str) -> dict:
        """Return safe metadata for an allowed project file or directory."""
        return _run_file_tool(
            "file_metadata",
            project,
            lambda: files.file_metadata(project, path),
        )

    return mcp


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_app(
    settings: Settings | None = None,
    registry: ProjectRegistry | None = None,
) -> Starlette:
    settings = settings or Settings.from_env()
    registry = registry or load_project_registry(settings.projects_config)
    audit = AuditLogger(settings.audit_log)
    safety_guard = OperatorSafetyGuard(
        stop_file=settings.operator_stop_file,
        retention=settings.retention_policy,
        retention_confirmed=settings.retention_confirmed,
    )
    mcp = build_mcp(settings, registry, audit, safety_guard=safety_guard)
    transport_security = transport_security_for(settings.resource_url)

    @asynccontextmanager
    async def lifespan(_: Starlette):
        async with mcp.session_manager.run():
            yield
    return Starlette(
        routes=[
            Route("/healthz", health, methods=["GET"]),
            Mount(
                "/",
                app=mcp.streamable_http_app(
                    transport_security=transport_security,
                ),
            ),
        ],
        middleware=[
            Middleware(RequestIdMiddleware),
            Middleware(
                RateLimitMiddleware,
                max_requests=settings.rate_limit_per_minute,
            ),
        ],
        lifespan=lifespan,
    )
