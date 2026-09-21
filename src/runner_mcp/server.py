from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver.utilities.func_metadata import ArgModelBase
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl, ConfigDict
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .adapters import AdapterError, get_adapter, inspect_project, list_adapters
from .approval_manager import ApprovalError, ApprovalManager
from .audit import AuditEvent, AuditLogger, utc_timestamp
from .config import ProjectRegistry, load_project_registry
from .database_manager import DatabaseManager, DatabaseManagerError
from .deployment_jobs import DeploymentJobError, DeploymentJobRunner
from .deployment_manager import DeploymentError, DeploymentManager
from .file_access import FileAccessError, FileAccessService
from .http_middleware import RateLimitMiddleware, RequestIdMiddleware, current_request_id
from .operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
    SafetyConfigurationError,
)
from .self_update import SelfUpdateError, SelfUpdateManager
from .service_manager import ServiceManager, ServiceManagerError
from .source_control import SourceControlError, SourceSynchronizer, clean_head
from .test_runner import TestRunner, TestRunnerError


@dataclass(frozen=True)
class Settings:
    bearer_token: str
    auth_issuer: str
    resource_url: str
    projects_config: Path
    audit_log: Path
    rate_limit_per_minute: int = 600
    retention_policy: RetentionPolicy = field(default_factory=RetentionPolicy)
    operator_stop_file: Path | None = None
    retention_confirmed: bool = True
    test_jobs_root: Path | None = None
    max_test_jobs: int = 2
    max_queued_tests: int = 64
    mailbox_workers: int = 4
    mailbox_max_inflight: int = 32
    database_backup_root: Path | None = None
    deployment_jobs_root: Path | None = None
    approval_root: Path | None = None
    approval_ttl_seconds: int = 600

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> Settings:
        token = values.get("RUNNER_MCP_BEARER_TOKEN", "")
        if len(token) < 32:
            raise RuntimeError("RUNNER_MCP_BEARER_TOKEN must contain at least 32 characters")
        issuer = values.get("RUNNER_MCP_AUTH_ISSUER", "")
        resource = values.get("RUNNER_MCP_RESOURCE_URL", "")
        if not issuer or not resource:
            raise RuntimeError("Authentication issuer and MCP resource URL are required")

        try:
            rate_limit = int(values.get("RUNNER_MCP_RATE_LIMIT_PER_MINUTE", "600"))
        except ValueError as exc:
            raise RuntimeError("RUNNER_MCP_RATE_LIMIT_PER_MINUTE must be an integer") from exc
        if not 1 <= rate_limit <= 6000:
            raise RuntimeError("RUNNER_MCP_RATE_LIMIT_PER_MINUTE must be between 1 and 6000")

        stop_file_raw = values.get("RUNNER_MCP_OPERATOR_STOP_FILE", "").strip()
        if stop_file_raw and not Path(stop_file_raw).is_absolute():
            raise RuntimeError("RUNNER_MCP_OPERATOR_STOP_FILE must be an absolute path")

        retention_confirmed_raw = values.get(
            "RUNNER_MCP_RETENTION_CONFIRMED",
            "false",
        ).strip().lower()
        if retention_confirmed_raw not in {"true", "false"}:
            raise RuntimeError("RUNNER_MCP_RETENTION_CONFIRMED must be true or false")

        test_jobs_root_raw = values.get("RUNNER_MCP_TEST_JOBS_ROOT", "").strip()
        if test_jobs_root_raw and not Path(test_jobs_root_raw).is_absolute():
            raise RuntimeError("RUNNER_MCP_TEST_JOBS_ROOT must be an absolute path")

        database_backup_root_raw = values.get(
            "RUNNER_MCP_DATABASE_BACKUP_ROOT",
            "",
        ).strip()
        if database_backup_root_raw and not Path(database_backup_root_raw).is_absolute():
            raise RuntimeError(
                "RUNNER_MCP_DATABASE_BACKUP_ROOT must be an absolute path"
            )

        deployment_jobs_root_raw = values.get(
            "RUNNER_MCP_DEPLOY_JOBS_ROOT",
            "",
        ).strip()
        if deployment_jobs_root_raw and not Path(deployment_jobs_root_raw).is_absolute():
            raise RuntimeError("RUNNER_MCP_DEPLOY_JOBS_ROOT must be an absolute path")

        approval_root_raw = values.get("RUNNER_MCP_APPROVAL_ROOT", "").strip()
        if approval_root_raw and not Path(approval_root_raw).is_absolute():
            raise RuntimeError("RUNNER_MCP_APPROVAL_ROOT must be an absolute path")

        try:
            max_test_jobs = int(values.get("RUNNER_MCP_MAX_TEST_JOBS", "2"))
        except ValueError as exc:
            raise RuntimeError("RUNNER_MCP_MAX_TEST_JOBS must be an integer") from exc
        try:
            max_queued_tests = int(values.get("RUNNER_MCP_MAX_QUEUED_TESTS", "64"))
        except ValueError as exc:
            raise RuntimeError("RUNNER_MCP_MAX_QUEUED_TESTS must be an integer") from exc

        try:
            mailbox_workers = int(values.get("RUNNER_MCP_MAILBOX_WORKERS", "4"))
        except ValueError as exc:
            raise RuntimeError("RUNNER_MCP_MAILBOX_WORKERS must be an integer") from exc
        try:
            mailbox_max_inflight = int(
                values.get("RUNNER_MCP_MAILBOX_MAX_INFLIGHT", "32")
            )
        except ValueError as exc:
            raise RuntimeError(
                "RUNNER_MCP_MAILBOX_MAX_INFLIGHT must be an integer"
            ) from exc

        try:
            approval_ttl_seconds = int(
                values.get("RUNNER_MCP_APPROVAL_TTL_SECONDS", "600")
            )
        except ValueError as exc:
            raise RuntimeError(
                "RUNNER_MCP_APPROVAL_TTL_SECONDS must be an integer"
            ) from exc
        if approval_ttl_seconds < 60 or approval_ttl_seconds > 1800:
            raise RuntimeError(
                "RUNNER_MCP_APPROVAL_TTL_SECONDS must be between 60 and 1800"
            )
        if not 1 <= max_test_jobs <= 16:
            raise RuntimeError("RUNNER_MCP_MAX_TEST_JOBS must be between 1 and 16")
        if not 1 <= max_queued_tests <= 1024:
            raise RuntimeError(
                "RUNNER_MCP_MAX_QUEUED_TESTS must be between 1 and 1024"
            )
        if not 1 <= mailbox_workers <= 16:
            raise RuntimeError(
                "RUNNER_MCP_MAILBOX_WORKERS must be between 1 and 16"
            )
        if not mailbox_workers <= mailbox_max_inflight <= 256:
            raise RuntimeError(
                "RUNNER_MCP_MAILBOX_MAX_INFLIGHT must be between "
                "RUNNER_MCP_MAILBOX_WORKERS and 256"
            )

        return cls(
            bearer_token=token,
            auth_issuer=issuer,
            resource_url=resource,
            projects_config=Path(
                values.get("RUNNER_MCP_PROJECTS_CONFIG", "config/projects.yml")
            ),
            audit_log=Path(values.get("RUNNER_MCP_AUDIT_LOG", "var/audit.jsonl")),
            rate_limit_per_minute=rate_limit,
            retention_policy=RetentionPolicy.from_mapping(values),
            operator_stop_file=Path(stop_file_raw) if stop_file_raw else None,
            retention_confirmed=retention_confirmed_raw == "true",
            test_jobs_root=Path(test_jobs_root_raw) if test_jobs_root_raw else None,
            max_test_jobs=max_test_jobs,
            max_queued_tests=max_queued_tests,
            mailbox_workers=mailbox_workers,
            mailbox_max_inflight=mailbox_max_inflight,
            database_backup_root=(
                Path(database_backup_root_raw) if database_backup_root_raw else None
            ),
            deployment_jobs_root=(
                Path(deployment_jobs_root_raw) if deployment_jobs_root_raw else None
            ),
            approval_root=Path(approval_root_raw) if approval_root_raw else None,
            approval_ttl_seconds=approval_ttl_seconds,
        )

    @classmethod
    def from_env(cls) -> Settings:
        return cls.from_mapping(os.environ)


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


def harden_mcp_argument_validation() -> None:
    """Reject unknown MCP tool arguments instead of silently ignoring them."""
    ArgModelBase.model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )


def build_mcp(
    settings: Settings,
    registry: ProjectRegistry,
    audit: AuditLogger,
    safety_guard: OperatorSafetyGuard | None = None,
    secret_values: Mapping[str, str] | None = None,
) -> MCPServer:
    harden_mcp_argument_validation()
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
    tests = (
        TestRunner(
            registry=registry,
            safety=safety,
            jobs_root=settings.test_jobs_root,
            max_concurrent_jobs=settings.max_test_jobs,
            max_queued_jobs=settings.max_queued_tests,
        )
        if settings.test_jobs_root is not None
        else None
    )
    source_sync = SourceSynchronizer(
        registry=registry,
        safety=safety,
        tests=tests,
    )
    service_manager = ServiceManager(
        registry=registry,
        safety=safety,
    )
    database_manager = DatabaseManager(
        registry=registry,
        safety=safety,
        backup_root=settings.database_backup_root,
        secret_values=secret_values or os.environ,
    )
    deployment_manager = DeploymentManager(
        registry=registry,
        safety=safety,
        services=service_manager,
        tests=tests,
        database=database_manager,
    )
    deployment_jobs = (
        DeploymentJobRunner(
            manager=deployment_manager,
            safety=safety,
            jobs_root=settings.deployment_jobs_root,
        )
        if settings.deployment_jobs_root is not None
        else None
    )

    approval_manager = (
        ApprovalManager(
            root=settings.approval_root,
            ttl_seconds=settings.approval_ttl_seconds,
        )
        if settings.approval_root is not None
        else None
    )
    self_update_manager = SelfUpdateManager(
        config_dir=settings.projects_config.parent,
        registry=registry,
        safety=safety,
        tests=tests,
        source=source_sync,
        resource_url=settings.resource_url,
    )

    @mcp.tool()
    def runtime_status() -> dict:
        """Return safe Runner MCP runtime/self-update status."""
        try:
            result = self_update_manager.runtime_status()
        except SelfUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "runtime_status",
                    None,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "runtime_status",
                None,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def self_update(commit: str) -> dict:
        """Start a canonical main-only Runner MCP self-update job."""
        try:
            result = self_update_manager.start(commit)
        except (SelfUpdateError, OperatorStopActive, SafetyConfigurationError) as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "self_update",
                    "runner-mcp",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "self_update",
                "runner-mcp",
                "authenticated-client",
                "started",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def self_update_status(job_id: str) -> dict:
        """Return safe persisted status for one Runner MCP self-update job."""
        try:
            result = self_update_manager.status(job_id)
        except SelfUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "self_update_status",
                    None,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "self_update_status",
                "runner-mcp",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

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
    def list_project_adapters() -> list[dict]:
        """List built-in, allow-listed project adapters."""
        request_id = current_request_id()
        result = list_adapters()
        audit.append(
            AuditEvent(
                request_id,
                "list_project_adapters",
                None,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def project_capabilities(project: str) -> dict:
        """Inspect safe adapter capabilities without exposing the project path."""
        request_id = current_request_id()
        cfg = registry.projects.get(project)
        if cfg is None:
            audit.append(
                AuditEvent(
                    request_id,
                    "project_capabilities",
                    project,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("Unknown or disabled project")
        try:
            adapter = get_adapter(cfg.adapter)
            inspection = inspect_project(cfg.adapter, cfg.root)
        except AdapterError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "project_capabilities",
                    project,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        result = {
            "project": project,
            "adapter": adapter.info.adapter_id,
            "adapter_name": adapter.info.display_name,
            "test_presets": list(adapter.info.test_presets),
            "migration_presets": list(adapter.info.migration_presets),
            "supports_services": adapter.info.supports_services,
            "supports_deployment": adapter.info.supports_deployment,
            "inspection": inspection,
        }
        audit.append(
            AuditEvent(
                request_id,
                "project_capabilities",
                project,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
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

    def _require_test_runner() -> TestRunner:
        if tests is None:
            raise ValueError("Test execution is not configured")
        return tests

    def _audit_test_result(
        *,
        tool_name: str,
        project: str | None,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                project,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    @mcp.tool()
    def sync_project(project: str, commit: str) -> dict:
        """Synchronize one staging project to an exact commit from its configured origin."""
        request_id = current_request_id()
        try:
            result = source_sync.sync_project(project, commit)
        except (
            SourceControlError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "sync_project",
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
                "sync_project",
                project,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def list_test_profiles(project: str) -> list[dict]:
        """List configured and fixed safe adapter test profiles without private argv."""
        cfg = registry.projects.get(project)
        if cfg is None:
            _audit_test_result(
                tool_name="list_test_profiles",
                project=project,
                result="denied",
            )
            raise ValueError("Unknown or disabled project")
        if tests is not None:
            result = tests.list_profiles(project)
        else:
            result = [
                {
                    "name": name,
                    "timeout_seconds": profile.timeout_seconds,
                    "max_log_bytes": profile.max_log_bytes,
                    "parallel_safe": profile.parallel_safe,
                }
                for name, profile in sorted(cfg.test_profiles.items())
            ]
        _audit_test_result(
            tool_name="list_test_profiles",
            project=project,
            result="ok",
        )
        return result

    @mcp.tool()
    def run_tests(project: str, suite: str) -> dict:
        """Start one predefined test profile and return a job identifier."""
        try:
            result = _require_test_runner().start_test(project, suite)
        except (
            TestRunnerError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            _audit_test_result(tool_name="run_tests", project=project, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(tool_name="run_tests", project=project, result="started")
        return result

    @mcp.tool()
    def test_status(job_id: str) -> dict:
        """Return safe metadata for a test job."""
        try:
            result = _require_test_runner().status(job_id)
        except TestRunnerError as exc:
            _audit_test_result(tool_name="test_status", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(
            tool_name="test_status",
            project=result.get("project"),
            result="ok",
        )
        return result

    @mcp.tool()
    def queue_status() -> dict:
        """Return safe queue capacity and per-project scheduling state."""
        try:
            result = _require_test_runner().queue_status()
        except TestRunnerError as exc:
            _audit_test_result(tool_name="queue_status", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(tool_name="queue_status", project=None, result="ok")
        return result

    @mcp.tool()
    def worker_status() -> dict:
        """Return bounded worker-pool capacity without process details."""
        try:
            result = _require_test_runner().worker_status()
        except TestRunnerError as exc:
            _audit_test_result(tool_name="worker_status", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(tool_name="worker_status", project=None, result="ok")
        return result

    @mcp.tool()
    def job_status(job_id: str) -> dict:
        """Return safe status for one queued or active test job."""
        try:
            result = _require_test_runner().job_status(job_id)
        except TestRunnerError as exc:
            _audit_test_result(tool_name="job_status", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(
            tool_name="job_status",
            project=result.get("project"),
            result="ok",
        )
        return result

    @mcp.tool()
    def cancel_job(job_id: str) -> dict:
        """Cancel one queued or active test job by opaque job identifier."""
        try:
            result = _require_test_runner().cancel(job_id)
        except TestRunnerError as exc:
            _audit_test_result(tool_name="cancel_job", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(
            tool_name="cancel_job",
            project=result.get("project"),
            result="requested",
        )
        return result

    @mcp.tool()
    def get_test_log(job_id: str, offset: int = 0, length: int = 200) -> dict:
        """Return a bounded page from a scrubbed test-job log."""
        try:
            result = _require_test_runner().get_log(
                job_id,
                offset=offset,
                length=length,
            )
        except TestRunnerError as exc:
            _audit_test_result(tool_name="get_test_log", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(tool_name="get_test_log", project=None, result="ok")
        return result

    @mcp.tool()
    def cancel_test(job_id: str) -> dict:
        """Request cancellation of one running test job."""
        try:
            result = _require_test_runner().cancel(job_id)
        except TestRunnerError as exc:
            _audit_test_result(tool_name="cancel_test", project=None, result="denied")
            raise ValueError(str(exc)) from None
        _audit_test_result(
            tool_name="cancel_test",
            project=result.get("project"),
            result="requested",
        )
        return result

    def _audit_service_result(
        *,
        tool_name: str,
        project: str,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                project,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    @mcp.tool()
    def list_services(project: str) -> list[dict]:
        """List configured service aliases and allowed actions without private unit names."""
        try:
            result = service_manager.list_services(project)
        except ServiceManagerError as exc:
            _audit_service_result(
                tool_name="list_services",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_service_result(tool_name="list_services", project=project, result="ok")
        return result

    @mcp.tool()
    def service_status(project: str, service: str) -> dict:
        """Return safe status and health information for one service alias."""
        try:
            result = service_manager.status(project, service)
        except ServiceManagerError as exc:
            _audit_service_result(
                tool_name="service_status",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_service_result(tool_name="service_status", project=project, result="ok")
        return result

    def _service_action(project: str, service: str, action: str) -> dict:
        tool_name = f"{action}_service"
        try:
            result = service_manager.action(project, service, action)
        except (
            ServiceManagerError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_service_result(
                tool_name=tool_name,
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_service_result(tool_name=tool_name, project=project, result="ok")
        return result

    @mcp.tool()
    def start_service(project: str, service: str) -> dict:
        """Start one explicitly allow-listed service alias."""
        return _service_action(project, service, "start")

    @mcp.tool()
    def stop_service(project: str, service: str) -> dict:
        """Stop one explicitly allow-listed service alias."""
        return _service_action(project, service, "stop")

    @mcp.tool()
    def restart_service(project: str, service: str) -> dict:
        """Restart one explicitly allow-listed service alias."""
        return _service_action(project, service, "restart")

    def _audit_database_result(
        *,
        tool_name: str,
        project: str,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                project,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    @mcp.tool()
    def list_backups(project: str, limit: int = 100) -> list[dict]:
        """List safe database-backup metadata without paths or credentials."""
        try:
            result = database_manager.list_backups(project, limit=limit)
        except DatabaseManagerError as exc:
            _audit_database_result(
                tool_name="list_backups",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(tool_name="list_backups", project=project, result="ok")
        return result

    @mcp.tool()
    def backup_database(project: str) -> dict:
        """Create a private PostgreSQL backup for one configured project."""
        try:
            result = database_manager.backup_database(project)
        except (
            DatabaseManagerError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_database_result(
                tool_name="backup_database",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(
            tool_name="backup_database",
            project=project,
            result="ok",
        )
        return result

    def _require_approval_manager() -> ApprovalManager:
        if approval_manager is None:
            raise ValueError("Human approval storage is not configured")
        return approval_manager

    def _migration_approval_material(project: str) -> tuple[dict, dict]:
        cfg = registry.projects.get(project)
        if cfg is None:
            raise ValueError("Unknown or disabled project")
        if cfg.environment != "staging":
            raise ValueError("Mutating project actions are enabled only for staging environments")
        if cfg.database is None or cfg.database.migrations is None:
            raise ValueError("Migration profile is not configured")
        source = clean_head(cfg.root)
        binding = {
            "environment": cfg.environment,
            "repository": cfg.repository,
            "database": cfg.database.model_dump(mode="json"),
            "source": source,
        }
        summary = {
            "action": "migration",
            "environment": cfg.environment,
            "commit": source["commit"],
            "pre_migration_backup_required": True,
            "automatic_database_restore": False,
        }
        return binding, summary

    def _deploy_approval_material(project: str) -> tuple[dict, dict]:
        plan = deployment_manager.plan(project)
        cfg = registry.projects.get(project)
        if cfg is None or cfg.deployment is None:
            raise ValueError("Staging deployment is not configured")
        service = cfg.services.get(cfg.deployment.service)
        if service is None:
            raise ValueError("Deployment service alias is not configured")
        binding = {
            "plan": plan,
            "deployment": cfg.deployment.model_dump(mode="json"),
            "service": service.model_dump(mode="json"),
            "database": (
                cfg.database.model_dump(mode="json")
                if cfg.deployment.run_migrations and cfg.database is not None
                else None
            ),
        }
        summary = {"action": "deploy", **plan}
        return binding, summary

    def _rollback_approval_material(project: str) -> tuple[dict, dict]:
        plan = deployment_manager.rollback_plan(project)
        if not plan.get("allowed", False):
            raise ValueError("Code rollback is blocked across a database migration boundary")
        binding = {"plan": plan}
        summary = {"action": "code_rollback", **plan}
        return binding, summary

    def _approval_material(project: str, action: str) -> tuple[dict, dict]:
        if action == "migration":
            return _migration_approval_material(project)
        if action == "deploy":
            return _deploy_approval_material(project)
        if action == "code_rollback":
            return _rollback_approval_material(project)
        raise ValueError("Unsupported approval action")

    def _audit_approval_result(
        *,
        tool_name: str,
        project: str | None,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                project,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    @mcp.tool()
    def request_action_approval(project: str, action: str) -> dict:
        """Create a short-lived human approval plan for migration, deploy or rollback."""
        try:
            binding, summary = _approval_material(project, action)
            result = _require_approval_manager().request(
                action=action,
                project=project,
                binding=binding,
                summary=summary,
            )
        except (ApprovalError, DeploymentError, SourceControlError, ValueError) as exc:
            _audit_approval_result(
                tool_name="request_action_approval",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_approval_result(
            tool_name="request_action_approval",
            project=project,
            result="pending",
        )
        return result

    @mcp.tool()
    def approval_status(approval_id: str) -> dict:
        """Return safe status for a short-lived human approval plan."""
        try:
            result = _require_approval_manager().status(approval_id)
        except (ApprovalError, ValueError) as exc:
            _audit_approval_result(
                tool_name="approval_status",
                project=None,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_approval_result(
            tool_name="approval_status",
            project=result.get("project"),
            result=str(result.get("state", "unknown")),
        )
        return result

    @mcp.tool()
    def migration_status(project: str) -> dict:
        """Run the configured read-only migration status command."""
        try:
            result = database_manager.migration_status(project)
        except DatabaseManagerError as exc:
            _audit_database_result(
                tool_name="migration_status",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(
            tool_name="migration_status",
            project=project,
            result="ok",
        )
        return result

    @mcp.tool()
    def apply_migrations(project: str, approval_id: str) -> dict:
        """Apply migrations only after consuming a matching human approval."""
        try:
            binding, _ = _migration_approval_material(project)
            _require_approval_manager().consume(
                approval_id,
                action="migration",
                project=project,
                binding=binding,
            )
            result = database_manager.apply_migrations(project)
        except (
            ApprovalError,
            DatabaseManagerError,
            SourceControlError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            _audit_database_result(
                tool_name="apply_migrations",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(
            tool_name="apply_migrations",
            project=project,
            result=str(result.get("status", "unknown")),
        )
        return result

    def _audit_deploy_result(
        *,
        tool_name: str,
        project: str | None,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                project,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    @mcp.tool()
    def plan_deploy(project: str) -> dict:
        """Return a safe read-only staging deployment plan."""
        try:
            result = deployment_manager.plan(project)
        except DeploymentError as exc:
            _audit_deploy_result(
                tool_name="plan_deploy",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(tool_name="plan_deploy", project=project, result="ok")
        return result

    def _require_deployment_jobs() -> DeploymentJobRunner:
        if deployment_jobs is None:
            raise ValueError("Deployment jobs are not configured")
        return deployment_jobs

    @mcp.tool()
    def deploy_staging(project: str, approval_id: str) -> dict:
        """Start a staging deploy only after consuming a matching human approval."""
        try:
            jobs = _require_deployment_jobs()
            binding, summary = _deploy_approval_material(project)
            _require_approval_manager().consume(
                approval_id,
                action="deploy",
                project=project,
                binding=binding,
            )
            result = jobs.start(
                project,
                expected_commit=str(summary["commit"]),
            )
        except (
            ApprovalError,
            DeploymentJobError,
            DeploymentError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            _audit_deploy_result(
                tool_name="deploy_staging",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(
            tool_name="deploy_staging",
            project=project,
            result="started",
        )
        return result

    @mcp.tool()
    def deployment_status(job_id: str) -> dict:
        """Return safe persisted status for one deployment job."""
        try:
            result = _require_deployment_jobs().status(job_id)
        except (DeploymentJobError, ValueError) as exc:
            _audit_deploy_result(
                tool_name="deployment_status",
                project=None,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(
            tool_name="deployment_status",
            project=result.get("project"),
            result="ok",
        )
        return result

    @mcp.tool()
    def list_releases(project: str, limit: int = 100) -> list[dict]:
        """List safe staging release metadata and retention/rollback state."""
        try:
            result = deployment_manager.list_releases(project, limit=limit)
        except DeploymentError as exc:
            _audit_deploy_result(
                tool_name="list_releases",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(tool_name="list_releases", project=project, result="ok")
        return result

    @mcp.tool()
    def rollback_plan(project: str) -> dict:
        """Return the one-step rollback target and database-boundary safety state."""
        try:
            result = deployment_manager.rollback_plan(project)
        except DeploymentError as exc:
            _audit_deploy_result(
                tool_name="rollback_plan",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(tool_name="rollback_plan", project=project, result="ok")
        return result

    @mcp.tool()
    def rollback_release(project: str, approval_id: str) -> dict:
        """Start one rollback only after consuming a matching human approval."""
        try:
            jobs = _require_deployment_jobs()
            binding, summary = _rollback_approval_material(project)
            _require_approval_manager().consume(
                approval_id,
                action="code_rollback",
                project=project,
                binding=binding,
            )
            result = jobs.start_rollback(
                project,
                expected_current_release=str(summary["current_release"]),
                expected_target_release=str(summary["target_release"]),
            )
        except (
            ApprovalError,
            DeploymentJobError,
            DeploymentError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            _audit_deploy_result(
                tool_name="rollback_release",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_deploy_result(
            tool_name="rollback_release",
            project=project,
            result="started",
        )
        return result

    @mcp.tool()
    def rollback_status(job_id: str) -> dict:
        """Return safe status for an asynchronous rollback job."""
        try:
            result = _require_deployment_jobs().status(job_id)
        except (DeploymentJobError, ValueError) as exc:
            _audit_deploy_result(
                tool_name="rollback_status",
                project=None,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        if result.get("operation") != "rollback":
            _audit_deploy_result(
                tool_name="rollback_status",
                project=result.get("project"),
                result="denied",
            )
            raise ValueError("Job is not a rollback job")
        _audit_deploy_result(
            tool_name="rollback_status",
            project=result.get("project"),
            result="ok",
        )
        return result

    return mcp


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_app(
    settings: Settings | None = None,
    registry: ProjectRegistry | None = None,
    secret_values: Mapping[str, str] | None = None,
) -> Starlette:
    settings = settings or Settings.from_env()
    registry = registry or load_project_registry(settings.projects_config)
    audit = AuditLogger(settings.audit_log)
    safety_guard = OperatorSafetyGuard(
        stop_file=settings.operator_stop_file,
        retention=settings.retention_policy,
        retention_confirmed=settings.retention_confirmed,
    )
    mcp = build_mcp(
        settings,
        registry,
        audit,
        safety_guard=safety_guard,
        secret_values=secret_values,
    )
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
