from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
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
from .artifact_custody import ContentAddressedArtifactCustody
from .audit import AuditEvent, AuditLogger, utc_timestamp
from .bewind_disposable_bootstrap import (
    BewindDisposableBootstrapError,
    BewindDisposableBootstrapRestorer,
)
from .bewind_ocr_qualification_authority import (
    BewindOcrQualificationExecutionAuthorityConfigurator,
    BewindOcrQualificationExecutionAuthorityError,
)
from .bewind_ocr_qualification_execution import (
    BewindOcrQualificationExecutionError,
    BewindOcrQualificationRunner,
)
from .bewind_ocr_qualification_source import (
    BewindOcrQualificationSourceProvisioner,
    BewindOcrQualificationSourceProvisionError,
)
from .bewind_ocr_qualification_staging import (
    BewindOcrQualificationStager,
    BewindOcrQualificationStagingError,
)
from .bewind_worker_qualification_policy import (
    BewindWorkerQualificationPolicyConfigurator,
    BewindWorkerQualificationPolicyError,
)
from .build_identity import (
    BuildIdentity,
    installed_source_revision,
    runner_mcp_build_identity,
    runner_mcp_mcp_build_identity,
)
from .ci_runner_enrollment import (
    CIRunnerEnrollmentError,
    CIRunnerEnrollmentManager,
)
from .ci_runner_github import CIRunnerGitHubController
from .ci_runner_guest_enrollment import (
    CIRunnerGuestEnrollmentError,
    CIRunnerGuestEnrollmentManager,
    CIRunnerGuestSpec,
)
from .ci_runner_guest_fabric_transport import CIRunnerGuestFabricTransport
from .ci_runner_guest_github import CIRunnerGuestGitHubController
from .ci_runner_lifecycle import (
    CIRunnerLifecycleError,
    inspect_ci_runner,
    parse_ci_runner_specs,
    plan_ci_runner,
)
from .ci_runner_secret_handoff import CIRunnerSecretHandoffStore
from .config import ProjectRegistry, load_project_registry
from .database_manager import DatabaseManager, DatabaseManagerError
from .deployment_jobs import DeploymentJobError, DeploymentJobRunner
from .deployment_manager import DeploymentError, DeploymentManager
from .fabric_a6_binding_repair import (
    FabricA6BindingRepairError,
    a6_state_requested,
    repair_a6_qualification_binding,
)
from .fabric_agent_runtime import (
    FabricAgentRestartError,
    restart_fabric_qualification_agent,
)
from .fabric_bootstrap import FabricBootstrapError, FabricBootstrapManager
from .fabric_bridge import FabricBridgeClient, FabricBridgeConfig, FabricBridgeError
from .fabric_coding_availability import (
    FabricCodingAvailabilityQualificationError,
    FabricCodingAvailabilityQualificationRunner,
)
from .fabric_continuity_status import (
    FabricContinuityStatusError,
    FabricContinuityStatusRunner,
)
from .fabric_disposable_target import (
    FabricDisposableTargetQualificationError,
    FabricDisposableTargetQualificationRunner,
)
from .fabric_repository_mirror_activation import (
    FabricRepositoryMirrorActivationError,
    FabricRepositoryMirrorActivator,
)
from .fabric_repository_mirrors import (
    FabricRepositoryMirrorError,
    FabricRepositoryMirrorRunner,
)
from .fabric_update import FabricUpdateError, FabricUpdateManager
from .fabric_worker_qualification_provisioning import (
    FabricWorkerQualificationProvisioner,
    FabricWorkerQualificationProvisioningError,
)
from .file_access import FileAccessError, FileAccessService
from .github_mailbox import GITHUB_TOKEN_ENV, GitHubApiSession
from .http_middleware import RateLimitMiddleware, RequestIdMiddleware, current_request_id
from .known_project_catalog import (
    KnownProjectRegistrationError,
    resolve_known_project_github_token,
)
from .known_project_catalog import (
    preflight_known_project as preflight_known_project_binding,
)
from .known_project_catalog import (
    preflight_known_project_source as preflight_known_project_source_binding,
)
from .known_project_catalog import (
    prepare_known_project as prepare_known_project_binding,
)
from .known_project_catalog import (
    register_known_project as register_known_project_binding,
)
from .migration_jobs import MigrationJobError, MigrationJobRunner
from .migration_planning import (
    async_migration_approval_material,
    migration_binding_fingerprint,
    migration_plan_material,
)
from .operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
    SafetyConfigurationError,
)
from .self_update import SelfUpdateError, SelfUpdateManager
from .service_manager import ServiceManager, ServiceManagerError
from .source_control import SourceControlError, SourceSynchronizer
from .test_runner import TestRunner, TestRunnerError
from .tunnel_topology_refresh import (
    TunnelTopologyRefreshError,
    bounded_tunnel_topology_refresh_reason,
    refresh_tunnel_topology_attestation,
)


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
    playwright_browsers_path: Path | None = None
    max_test_jobs: int = 2
    max_queued_tests: int = 64
    mailbox_workers: int = 4
    mailbox_max_inflight: int = 32
    database_backup_root: Path | None = None
    deployment_jobs_root: Path | None = None
    migration_jobs_root: Path | None = None
    approval_root: Path | None = None
    approval_ttl_seconds: int = 600
    fabric_resource_url: str | None = None
    fabric_bearer_token: str | None = None

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

        playwright_browsers_path_raw = values.get(
            "RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH",
            "",
        ).strip()
        if playwright_browsers_path_raw and not Path(
            playwright_browsers_path_raw
        ).is_absolute():
            raise RuntimeError(
                "RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH must be an absolute path"
            )

        database_backup_root_raw = values.get(
            "RUNNER_MCP_DATABASE_BACKUP_ROOT",
            "",
        ).strip()
        if (
            database_backup_root_raw
            and not Path(database_backup_root_raw).is_absolute()
        ):
            raise RuntimeError(
                "RUNNER_MCP_DATABASE_BACKUP_ROOT must be an absolute path"
            )

        deployment_jobs_root_raw = values.get(
            "RUNNER_MCP_DEPLOY_JOBS_ROOT",
            "",
        ).strip()
        if (
            deployment_jobs_root_raw
            and not Path(deployment_jobs_root_raw).is_absolute()
        ):
            raise RuntimeError("RUNNER_MCP_DEPLOY_JOBS_ROOT must be an absolute path")

        migration_jobs_root_raw = values.get(
            "RUNNER_MCP_MIGRATION_JOBS_ROOT",
            "",
        ).strip()
        if (
            migration_jobs_root_raw
            and not Path(migration_jobs_root_raw).is_absolute()
        ):
            raise RuntimeError(
                "RUNNER_MCP_MIGRATION_JOBS_ROOT must be an absolute path"
            )

        approval_root_raw = values.get("RUNNER_MCP_APPROVAL_ROOT", "").strip()
        if approval_root_raw and not Path(approval_root_raw).is_absolute():
            raise RuntimeError("RUNNER_MCP_APPROVAL_ROOT must be an absolute path")

        fabric_resource_url = values.get(
            "RUNNER_MCP_FABRIC_RESOURCE_URL",
            "",
        ).strip()
        fabric_bearer_token = values.get(
            "RUNNER_MCP_FABRIC_BEARER_TOKEN",
            "",
        ).strip()
        if bool(fabric_resource_url) != bool(fabric_bearer_token):
            raise RuntimeError(
                "Runner Fabric resource URL and bearer token must be configured together"
            )
        if fabric_resource_url:
            try:
                FabricBridgeConfig(
                    endpoint=fabric_resource_url,
                    bearer_token=fabric_bearer_token,
                ).to_mcp_config()
            except ValueError as exc:
                raise RuntimeError("Runner Fabric bridge configuration is invalid") from exc

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
            playwright_browsers_path=(
                Path(playwright_browsers_path_raw)
                if playwright_browsers_path_raw
                else None
            ),
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
            migration_jobs_root=(
                Path(migration_jobs_root_raw) if migration_jobs_root_raw else None
            ),
            approval_root=Path(approval_root_raw) if approval_root_raw else None,
            approval_ttl_seconds=approval_ttl_seconds,
            fabric_resource_url=fabric_resource_url or None,
            fabric_bearer_token=fabric_bearer_token or None,
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
        hide_input_in_errors=True,
    )


def build_mcp(
    settings: Settings,
    registry: ProjectRegistry,
    audit: AuditLogger,
    safety_guard: OperatorSafetyGuard | None = None,
    secret_values: Mapping[str, str] | None = None,
    self_update_restart_components: frozenset[str] | None = None,
    server_bind_host: str | None = None,
    server_bind_port: int | None = None,
    build_identity_provider: Callable[[], BuildIdentity] | None = None,
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
            playwright_browsers_path=settings.playwright_browsers_path,
            max_concurrent_jobs=settings.max_test_jobs,
            max_queued_jobs=settings.max_queued_tests,
        )
        if settings.test_jobs_root is not None
        else None
    )
    private_values = secret_values or os.environ
    github_token = private_values.get(GITHUB_TOKEN_ENV, "").strip()
    known_project_local_sources = private_values.get(
        "RUNNER_MCP_KNOWN_PROJECT_LOCAL_SOURCES_JSON",
        "",
    )

    def known_project_github_token(project_id: str) -> str | None:
        return resolve_known_project_github_token(
            project_id=project_id,
            global_token=github_token or None,
            private_values=private_values,
        )
    source_sync = SourceSynchronizer(
        registry=registry,
        safety=safety,
        tests=tests,
        github_token=github_token or None,
    )
    service_manager = ServiceManager(
        registry=registry,
        safety=safety,
    )
    database_manager = DatabaseManager(
        registry=registry,
        safety=safety,
        backup_root=settings.database_backup_root,
        secret_values=private_values,
    )

    try:
        ci_runner_specs = parse_ci_runner_specs(
            private_values.get("RUNNER_MCP_CI_RUNNERS_JSON")
        )
    except CIRunnerLifecycleError as exc:
        raise RuntimeError("CI runner private configuration is invalid") from exc

    ci_runner_enrollment = None
    if ci_runner_specs and github_token:
        try:
            ci_runner_enrollment = CIRunnerEnrollmentManager(
                github=CIRunnerGitHubController(
                    GitHubApiSession(token=github_token)
                ),
                environment=private_values,
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "CI runner enrollment private configuration is invalid"
            ) from exc
    migration_jobs = (
        MigrationJobRunner(
            manager=database_manager,
            registry=registry,
            safety=safety,
            jobs_root=settings.migration_jobs_root,
        )
        if settings.migration_jobs_root is not None
        else None
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

    def active_runtime_revision() -> str | None:
        if build_identity_provider is None:
            return None
        try:
            identity = build_identity_provider()
        except (RuntimeError, TypeError, ValueError):
            return None
        if not isinstance(identity, BuildIdentity):
            return None
        return identity.source_revision

    self_update_manager = SelfUpdateManager(
        config_dir=settings.projects_config.parent,
        registry=registry,
        safety=safety,
        tests=tests,
        source=source_sync,
        resource_url=settings.resource_url,
        server_bind_host=server_bind_host,
        server_bind_port=server_bind_port,
        restart_components=(
            self_update_restart_components
            if self_update_restart_components is not None
            else frozenset({"server"})
        ),
        active_revision_provider=(
            active_runtime_revision
            if build_identity_provider is not None
            else None
        ),
    )
    fabric_bootstrap_manager = FabricBootstrapManager(
        config_dir=settings.projects_config.parent,
        safety=safety,
        self_update_status_provider=self_update_manager.runtime_status,
    )
    fabric_update_manager = FabricUpdateManager(
        config_dir=settings.projects_config.parent,
        safety=safety,
        self_update_status_provider=self_update_manager.runtime_status,
    )

    fabric_coding_availability_runner = FabricCodingAvailabilityQualificationRunner(
        safety=safety,
        environment=private_values,
    )
    fabric_continuity_status_runner = FabricContinuityStatusRunner(
        environment=private_values,
    )
    worker_qualification_environment = dict(private_values)
    fabric_worker_qualification_provisioner = FabricWorkerQualificationProvisioner(
        safety=safety,
        environment=worker_qualification_environment,
        config_dir=settings.projects_config.parent,
    )
    bewind_disposable_bootstrap_restorer = BewindDisposableBootstrapRestorer(
        safety=safety,
        environment=worker_qualification_environment,
        config_dir=settings.projects_config.parent,
    )
    artifact_custody = ContentAddressedArtifactCustody(
        config_dir=settings.projects_config.parent,
    )
    bewind_ocr_qualification_source_provisioner = (
        BewindOcrQualificationSourceProvisioner(
            safety=safety,
            config_dir=settings.projects_config.parent,
            custody=artifact_custody,
        )
    )
    bewind_ocr_qualification_execution_authority = (
        BewindOcrQualificationExecutionAuthorityConfigurator(
            safety=safety,
            environment=worker_qualification_environment,
            config_dir=settings.projects_config.parent,
        )
    )
    bewind_ocr_qualification_stager = BewindOcrQualificationStager(
        safety=safety,
        environment=worker_qualification_environment,
        config_dir=settings.projects_config.parent,
    )
    bewind_worker_policy_configurator = BewindWorkerQualificationPolicyConfigurator(
        safety=safety,
        environment=worker_qualification_environment,
        config_dir=settings.projects_config.parent,
    )
    fabric_disposable_target_runner = FabricDisposableTargetQualificationRunner(
        safety=safety,
        environment=worker_qualification_environment,
    )
    mirror_runtime_environment = dict(private_values)
    fabric_repository_mirror_runner = FabricRepositoryMirrorRunner(
        safety=safety,
        environment=mirror_runtime_environment,
    )
    fabric_repository_mirror_activator = FabricRepositoryMirrorActivator(
        safety=safety,
        environment=mirror_runtime_environment,
        config_dir=settings.projects_config.parent,
        github_token=github_token or None,
    )

    fabric_bridge = (
        FabricBridgeClient(
            FabricBridgeConfig(
                endpoint=settings.fabric_resource_url,
                bearer_token=settings.fabric_bearer_token,
            )
        )
        if (
            settings.fabric_resource_url is not None
            and settings.fabric_bearer_token is not None
        )
        else None
    )

    def bewind_qualification_readiness() -> Mapping[str, object]:
        if fabric_bridge is None:
            raise FabricBridgeError("Runner Fabric bridge is not configured")
        return fabric_bridge.worker_qualification_readiness(
            "aifordable-lab",
            "bewind-ocr-qualification-v1",
        )

    bewind_ocr_qualification_runner = BewindOcrQualificationRunner(
        safety=safety,
        environment=worker_qualification_environment,
        config_dir=settings.projects_config.parent,
        stager=bewind_ocr_qualification_stager,
        disposable_qualifier=fabric_disposable_target_runner,
        readiness_provider=bewind_qualification_readiness,
    )

    ci_guest_specs = {
        "aifordable-lab-ci": CIRunnerGuestSpec(
            alias="aifordable-lab-ci",
            repository="Blacksp1d3r/AIfordable",
            runner_name="aifordable-lab-ci",
            labels=("aifordable-ci",),
            transport_binding_key="aifordable-lab-ci",
        )
    }

    ci_guest_enrollment = None
    if fabric_bridge is not None and ci_guest_specs and github_token:
        handoff_root = settings.projects_config.parent / "ci-runner-handoffs"
        try:
            handoff_root.mkdir(mode=0o700, exist_ok=True)
            ci_guest_enrollment = CIRunnerGuestEnrollmentManager(
                github=CIRunnerGuestGitHubController(
                    GitHubApiSession(token=github_token)
                ),
                transport=CIRunnerGuestFabricTransport(
                    handoffs=CIRunnerSecretHandoffStore(root=handoff_root),
                    fabric=fabric_bridge,
                ),
            )
        except (OSError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "CI guest enrollment private configuration is invalid"
            ) from exc

    if build_identity_provider is not None and not callable(
        build_identity_provider
    ):
        raise TypeError("build_identity_provider must be callable")

    def build_identity() -> dict[str, object]:
        """Return bounded first-party build/protocol/interface identity."""

        if build_identity_provider is None:
            raise ValueError("build_identity_unavailable")
        try:
            identity = build_identity_provider()
        except (RuntimeError, TypeError, ValueError):
            raise ValueError("build_identity_unavailable") from None
        if not isinstance(identity, BuildIdentity):
            raise TypeError("build_identity_unavailable")
        return identity.to_payload()

    if build_identity_provider is not None:
        mcp.tool()(build_identity)

    @mcp.tool()
    def runtime_status() -> dict:
        """Return safe Runner MCP runtime state without private host metadata."""
        status = safety.status()
        try:
            package = version("aifordable-runner-mcp")
        except PackageNotFoundError:
            package = "development"
        result = {
            "version": package,
            "mode": status.mode,
            "emergency_stop": status.stop_active,
            "retention_confirmed": settings.retention_confirmed,
            "projects": len(registry.projects),
            "test_execution_configured": tests is not None,
            "test_worker_limit": settings.max_test_jobs,
            "test_queue_limit": settings.max_queued_tests,
            "mailbox_worker_limit": settings.mailbox_workers,
            "mailbox_inflight_limit": settings.mailbox_max_inflight,
            "database_backups_configured": settings.database_backup_root is not None,
            "deployment_jobs_configured": deployment_jobs is not None,
            "migration_jobs_configured": migration_jobs is not None,
            "approvals_configured": approval_manager is not None,
            "fabric_bridge_configured": fabric_bridge is not None,
        }
        try:
            result.update(self_update_manager.runtime_status())
            result.update(fabric_bootstrap_manager.runtime_status())
            result.update(fabric_update_manager.runtime_status())
        except (SelfUpdateError, FabricBootstrapError, FabricUpdateError) as exc:
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
    def runtime_doctor() -> dict:
        """Return bounded safe runtime checks without paths, endpoints or secrets."""
        checks: list[dict[str, str]] = []

        def add(name: str, state: str, detail: str) -> None:
            checks.append({"name": name, "state": state, "detail": detail})

        add(
            "retention",
            "pass" if settings.retention_confirmed else "fail",
            "confirmed" if settings.retention_confirmed else "not_confirmed",
        )
        safety_state = safety.status()
        add(
            "emergency_stop",
            "warn" if safety_state.stop_active else "pass",
            "active" if safety_state.stop_active else "inactive",
        )
        resource = urlsplit(settings.resource_url)
        transport_ok = resource.scheme == "https" or (resource.hostname or "").lower() in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        add(
            "resource_transport",
            "pass" if transport_ok else "fail",
            "secure_or_loopback" if transport_ok else "unsafe",
        )
        add(
            "github_source_auth",
            "pass" if github_token else "warn",
            "configured" if github_token else "not_configured",
        )

        try:
            self_update_status = self_update_manager.runtime_status()
        except SelfUpdateError:
            add(
                "self_update_source_baseline",
                "warn",
                "unavailable",
            )
        else:
            installed_commit = self_update_status.get("last_installed_commit")
            source_commit = self_update_status.get("source_commit")
            aligned = self_update_status.get("source_baseline_aligned")
            if aligned is True:
                add(
                    "self_update_source_baseline",
                    "pass",
                    "aligned",
                )
            elif installed_commit is None:
                add(
                    "self_update_source_baseline",
                    "warn",
                    "not_recorded",
                )
            elif source_commit is None:
                add(
                    "self_update_source_baseline",
                    "fail",
                    "source_unavailable",
                )
            else:
                add(
                    "self_update_source_baseline",
                    "fail",
                    "source_baseline_drift",
                )

            active_revision = self_update_status.get("active_runtime_revision")
            activation_aligned = self_update_status.get(
                "runtime_activation_aligned"
            )
            if activation_aligned is True:
                add(
                    "self_update_runtime_activation",
                    "pass",
                    "aligned",
                )
            elif installed_commit is None:
                add(
                    "self_update_runtime_activation",
                    "warn",
                    "not_recorded",
                )
            elif active_revision is None:
                add(
                    "self_update_runtime_activation",
                    "fail",
                    "active_revision_unavailable",
                )
            else:
                add(
                    "self_update_runtime_activation",
                    "fail",
                    "runtime_activation_drift",
                )

        try:
            actions_readiness = fabric_update_manager.actions_readiness()
        except FabricUpdateError:
            add(
                "runner_fabric_actions_read",
                "warn",
                "unavailable_or_unauthorized",
            )
        else:
            add(
                "runner_fabric_actions_read",
                "pass" if actions_readiness.get("actions_readable") is True else "warn",
                "readable" if actions_readiness.get("actions_readable") is True else "unavailable_or_unauthorized",
            )

        try:
            fabric_continuity_status_runner.status()
        except FabricContinuityStatusError as exc:
            add(
                "fabric_continuity_status",
                "warn",
                str(exc),
            )
        else:
            add(
                "fabric_continuity_status",
                "pass",
                "available",
            )

        if fabric_bridge is None:
            add(
                "fabric_worker_qualification_readiness",
                "warn",
                "bridge_not_configured",
            )
        else:
            try:
                readiness = fabric_bridge.worker_qualification_readiness(
                    "aifordable-lab",
                    "bewind-ocr-qualification-v1",
                )
            except FabricBridgeError:
                add(
                    "fabric_worker_qualification_readiness",
                    "warn",
                    "unavailable",
                )
            else:
                generation = readiness.get("currentGeneration")
                ready = readiness.get("activationReady") is True
                detail = (
                    f"ready_generation_{generation}"
                    if ready and isinstance(generation, int) and not isinstance(generation, bool)
                    else "blocked"
                )
                add(
                    "fabric_worker_qualification_readiness",
                    "pass" if ready else "warn",
                    detail,
                )

        def storage_state(value: Path | None) -> tuple[str, str]:
            if value is None:
                return "warn", "not_configured"
            try:
                safe = (
                    value.exists()
                    and value.is_dir()
                    and not value.is_symlink()
                    and os.access(value, os.W_OK | os.X_OK)
                )
            except OSError:
                safe = False
            return (
                ("pass", "available")
                if safe
                else ("fail", "unavailable_or_unsafe")
            )

        for name, value in (
            ("test_storage", settings.test_jobs_root),
            ("database_backup_storage", settings.database_backup_root),
            ("deployment_job_storage", settings.deployment_jobs_root),
            ("migration_job_storage", settings.migration_jobs_root),
            ("approval_storage", settings.approval_root),
        ):
            state, detail = storage_state(value)
            add(name, state, detail)

        failed = sum(item["state"] == "fail" for item in checks)
        warned = sum(item["state"] == "warn" for item in checks)
        result = {
            "state": "fail" if failed else ("warn" if warned else "pass"),
            "failed_checks": failed,
            "warning_checks": warned,
            "checks": checks,
        }
        audit.append(
            AuditEvent(
                current_request_id(),
                "runtime_doctor",
                None,
                "authenticated-client",
                result["state"],
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_bootstrap(commit: str) -> dict:
        """Start one bounded canonical Runner Fabric bootstrap job."""
        try:
            result = fabric_bootstrap_manager.start(commit)
        except FabricBootstrapError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_bootstrap",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_bootstrap",
                "runner-fabric",
                "authenticated-client",
                "started",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_bootstrap_status(job_id: str) -> dict:
        """Return bounded status for one Runner Fabric bootstrap job."""
        try:
            result = fabric_bootstrap_manager.status(job_id)
        except FabricBootstrapError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_bootstrap_status",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_bootstrap_status",
                "runner-fabric",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_worker_qualification_provision(
        worker_id: str,
        capability_profile: str,
        generation: int,
        plan_digest: str,
        policy_expires_at: str,
        fabric_revision: str,
        request_fingerprint: str,
    ) -> dict:
        """Provision fixed local state for one Fabric-authorized qualification."""
        try:
            result = fabric_worker_qualification_provisioner.provision(
                worker_id=worker_id,
                capability_profile=capability_profile,
                generation=generation,
                plan_digest=plan_digest,
                policy_expires_at=policy_expires_at,
                fabric_revision=fabric_revision,
                request_fingerprint=request_fingerprint,
            )
        except (
            FabricWorkerQualificationProvisioningError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_worker_qualification_provision",
                    "runner-fabric:worker-qualification",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric worker qualification provisioning is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_worker_qualification_provision",
                "runner-fabric:worker-qualification",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def bewind_ocr_qualification_execution_authority_configure() -> dict:
        """Configure the one fixed Bewind OCR qualification execution authority."""
        try:
            result = bewind_ocr_qualification_execution_authority.configure()
        except (
            BewindOcrQualificationExecutionAuthorityError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "bewind_ocr_qualification_execution_authority_configure",
                    "bewind:ocr-qualification-execution-authority",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Bewind OCR qualification execution authority is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "bewind_ocr_qualification_execution_authority_configure",
                "bewind:ocr-qualification-execution-authority",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def bewind_ocr_qualification_source_provision() -> dict:
        """Provision the canonical source and its fixed execution authority."""
        try:
            result = bewind_ocr_qualification_source_provisioner.provision()
            authority = bewind_ocr_qualification_execution_authority.configure()
        except (
            BewindOcrQualificationSourceProvisionError,
            BewindOcrQualificationExecutionAuthorityError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "bewind_ocr_qualification_source_provision",
                    "bewind:ocr-qualification-source",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Bewind OCR qualification source provisioning is unavailable"
            ) from None
        result = dict(result)
        result["executionAuthorityReady"] = (
            authority.get("state") == "configured"
            and authority.get("normalActivationEnabled") is False
        )
        if result["executionAuthorityReady"] is not True:
            raise ValueError(
                "Bewind OCR qualification execution authority is unavailable"
            )
        audit.append(
            AuditEvent(
                current_request_id(),
                "bewind_ocr_qualification_source_provision",
                "bewind:ocr-qualification-source",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def bewind_ocr_qualification_stage() -> dict:
        """Stage the one fixed content-addressed Bewind OCR qualification source."""
        try:
            result = bewind_ocr_qualification_stager.stage()
        except (
            BewindOcrQualificationStagingError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "bewind_ocr_qualification_stage",
                    "bewind:ocr-qualification-source",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Bewind OCR qualification source staging is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "bewind_ocr_qualification_stage",
                "bewind:ocr-qualification-source",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def bewind_ocr_qualification_run() -> dict:
        """Run exactly one fixed Bewind OCR qualification unit."""
        try:
            result = bewind_ocr_qualification_runner.run()
        except (
            BewindOcrQualificationExecutionError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "bewind_ocr_qualification_run",
                    "bewind:ocr-qualification",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Bewind OCR qualification execution is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "bewind_ocr_qualification_run",
                "bewind:ocr-qualification",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_disposable_target_qualify() -> dict:
        """Run the fixed bounded disposable-target qualification lifecycle."""
        try:
            result = fabric_disposable_target_runner.run()
        except (
            FabricDisposableTargetQualificationError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_disposable_target_qualify",
                    "runner-fabric:disposable-target",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric disposable target qualification is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_disposable_target_qualify",
                "runner-fabric:disposable-target",
                "authenticated-client",
                "qualified",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_coding_availability_qualify(
        case: str,
        expected_revision: str,
    ) -> dict:
        """Run one fixed bounded coding-worker availability qualification case."""
        try:
            result = fabric_coding_availability_runner.run(
                case,
                expected_revision,
            )
        except (
            FabricCodingAvailabilityQualificationError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_coding_availability_qualify",
                    "runner-fabric:coding-availability",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric coding availability qualification is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_coding_availability_qualify",
                "runner-fabric:coding-availability",
                "authenticated-client",
                "qualified",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_continuity_status() -> dict:
        """Return fixed read-only Runner Fabric continuity evidence."""
        try:
            result = fabric_continuity_status_runner.status()
        except FabricContinuityStatusError:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_continuity_status",
                    "runner-fabric:continuity-status",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric continuity status is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_continuity_status",
                "runner-fabric:continuity-status",
                "authenticated-client",
                str(result.get("mode", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_repository_mirrors_activation_readiness() -> dict:
        """Inspect fixed F34 mirror activation prerequisites without mutation."""
        result = fabric_repository_mirror_runner.readiness()
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_repository_mirrors_activation_readiness",
                "runner-fabric:repository-mirrors",
                "authenticated-client",
                str(result.get("reasonCode", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_repository_mirrors_activate() -> dict:
        """Activate fixed private F34 mirror bindings without running reconcile."""
        try:
            result = fabric_repository_mirror_activator.activate()
        except (
            FabricRepositoryMirrorActivationError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_repository_mirrors_activate",
                    "runner-fabric:repository-mirrors",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric repository mirror activation is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_repository_mirrors_activate",
                "runner-fabric:repository-mirrors",
                "authenticated-client",
                "activated",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_repository_mirrors_preflight() -> dict:
        """Validate fixed private F34 repository-mirror activation inputs."""
        try:
            result = fabric_repository_mirror_runner.preflight()
        except FabricRepositoryMirrorError:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_repository_mirrors_preflight",
                    "runner-fabric:repository-mirrors",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric repository mirror preflight is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_repository_mirrors_preflight",
                "runner-fabric:repository-mirrors",
                "authenticated-client",
                "ready",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_repository_mirrors_reconcile() -> dict:
        """Reconcile the fixed host-owned F34 managed repository mirror set."""
        try:
            result = fabric_repository_mirror_runner.reconcile()
        except (
            FabricRepositoryMirrorError,
            OperatorStopActive,
            SafetyConfigurationError,
        ):
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_repository_mirrors_reconcile",
                    "runner-fabric:repository-mirrors",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(
                "Fabric repository mirror reconcile is unavailable"
            ) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_repository_mirrors_reconcile",
                "runner-fabric:repository-mirrors",
                "authenticated-client",
                "complete" if result.get("successful") is True else "failed",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_update_readiness(commit: str) -> dict:
        """Check bounded Runner Fabric update artifact readiness without mutation."""
        try:
            result = fabric_update_manager.readiness(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_update_readiness",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_update_readiness",
                "runner-fabric",
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_local_bundle_stage(commit: str) -> dict:
        """Stage one exact canonical Runner Fabric update bundle into local custody."""
        try:
            result = fabric_update_manager.stage_local_bundle(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_local_bundle_stage",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_local_bundle_stage",
                "runner-fabric",
                "authenticated-client",
                "ready",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_local_update_readiness(commit: str) -> dict:
        """Check one exact locally-custodied Runner Fabric bundle."""
        try:
            result = fabric_update_manager.local_readiness(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_local_update_readiness",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_local_update_readiness",
                "runner-fabric",
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_local_update(commit: str) -> dict:
        """Start one exact managed Runner Fabric update from local custody."""
        try:
            result = fabric_update_manager.start_local(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_local_update",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_local_update",
                "runner-fabric",
                "authenticated-client",
                "started",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_update(commit: str) -> dict:
        """Start one exact canonical managed Runner Fabric update."""
        try:
            result = fabric_update_manager.start(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_update",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_update",
                "runner-fabric",
                "authenticated-client",
                "started",
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_update_status(job_id: str) -> dict:
        """Return bounded status for one managed Runner Fabric update."""
        try:
            result = fabric_update_manager.status(job_id)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_update_status",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_update_status",
                "runner-fabric",
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def fabric_update_rollback(commit: str) -> dict:
        """Rollback only the currently active managed Runner Fabric update."""
        try:
            result = fabric_update_manager.rollback(commit)
        except FabricUpdateError as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "fabric_update_rollback",
                    "runner-fabric",
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                current_request_id(),
                "fabric_update_rollback",
                "runner-fabric",
                "authenticated-client",
                "completed",
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

    def _require_fabric_bridge() -> FabricBridgeClient:
        if fabric_bridge is None:
            raise ValueError("Runner Fabric bridge is not configured")
        return fabric_bridge

    def _audit_fabric(
        tool_name: str,
        resource_id: str,
        result: str,
    ) -> None:
        audit.append(
            AuditEvent(
                current_request_id(),
                tool_name,
                resource_id,
                "authenticated-client",
                result,
                utc_timestamp(),
            )
        )

    def _fabric_host_inspect_failure(exc: FabricBridgeError) -> dict:
        """Project one Fabric host-inspection failure into bounded public evidence."""

        category = (
            "fabric_inspection_unavailable"
            if str(exc) == "Runner Fabric host inspection failed"
            else "invalid_inspection_payload"
        )
        bridge = _require_fabric_bridge()
        preflight_method = getattr(bridge, "preflight", None)
        if callable(preflight_method):
            try:
                preflight = preflight_method()
            except FabricBridgeError:
                preflight = {}
        else:
            preflight = {}
        reason = preflight.get("reason_code") if isinstance(preflight, dict) else None
        if (
            preflight.get("state") == "blocked"
            and isinstance(reason, str)
            and reason in {
                "transport_or_auth_unavailable",
                "initialization_failed",
                "protocol_incompatible",
                "interface_incompatible",
                "build_identity_incompatible",
                "server_identity_invalid",
                "session_invalid",
                "response_invalid",
                "peer_unavailable",
                "bridge_unavailable",
            }
        ):
            category = reason
        return {
            "schema_version": "runner-mcp/fabric-host-inspection-error/v1",
            "state": "unavailable",
            "error_category": category,
            "mutation_enabled": False,
        }

    def fabric_bridge_preflight() -> dict:
        """Return bounded read-only Fabric MCP handshake readiness."""

        try:
            result = _require_fabric_bridge().preflight()
        except FabricBridgeError:
            result = {
                "schema_version": "runner-mcp/fabric-bridge-preflight/v1",
                "state": "blocked",
                "reason_code": "bridge_unavailable",
                "protocol_version": None,
                "server_name": None,
                "server_version": None,
                "source_revision": None,
                "a6_prepare_available": False,
                "synthetic_probe_status_available": False,
                "mutation_enabled": False,
            }
        _audit_fabric(
            "fabric_bridge_preflight",
            "fabric:bridge",
            str(result.get("state", "blocked")),
        )
        return result

    def fabric_host_inspect() -> dict:
        """Return bounded Runner Fabric host/browser readiness without host authority."""
        try:
            result = _require_fabric_bridge().host_inspect()
        except FabricBridgeError as exc:
            _audit_fabric("fabric_host_inspect", "host:local", "denied")
            return _fabric_host_inspect_failure(exc)
        _audit_fabric("fabric_host_inspect", "host:local", "ok")
        return result

    def fabric_external_target_preflight() -> dict:
        """Return bounded config-only readiness for the trusted external target."""
        try:
            result = _require_fabric_bridge().external_target_preflight()
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_external_target_preflight",
                "external-target:managed",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_external_target_preflight",
            "external-target:managed",
            "ok",
        )
        return result

    def fabric_external_target_inspect() -> dict:
        """Return bounded live read-only qualification for the trusted external target."""
        try:
            result = _require_fabric_bridge().external_target_inspect()
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_external_target_inspect",
                "external-target:managed",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_external_target_inspect",
            "external-target:managed",
            str(result.get("readiness", "unknown")),
        )
        return result

    def fabric_ci_runner_guest_status() -> dict:
        """Return bounded isolated CI guest state without host authority."""
        try:
            result = _require_fabric_bridge().ci_runner_guest_status()
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_ci_runner_guest_status",
                "ci-runner:aifordable-lab-ci",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_ci_runner_guest_status",
            "ci-runner:aifordable-lab-ci",
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_ci_runner_guest_start() -> dict:
        """Start the isolated CI guest listener through bounded Fabric authority."""
        try:
            safety.assert_action_allowed(ActionClass.SERVICE)
            result = _require_fabric_bridge().ci_runner_guest_start()
        except (
            FabricBridgeError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_fabric(
                "fabric_ci_runner_guest_start",
                "ci-runner:aifordable-lab-ci",
                "denied",
            )
            raise ValueError("CI guest start is unavailable") from exc
        _audit_fabric(
            "fabric_ci_runner_guest_start",
            "ci-runner:aifordable-lab-ci",
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_ci_runner_guest_stop() -> dict:
        """Stop the isolated CI guest listener through bounded Fabric authority."""
        try:
            safety.assert_action_allowed(ActionClass.SERVICE)
            result = _require_fabric_bridge().ci_runner_guest_stop()
        except (
            FabricBridgeError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_fabric(
                "fabric_ci_runner_guest_stop",
                "ci-runner:aifordable-lab-ci",
                "denied",
            )
            raise ValueError("CI guest stop is unavailable") from exc
        _audit_fabric(
            "fabric_ci_runner_guest_stop",
            "ci-runner:aifordable-lab-ci",
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_agent_restart() -> dict:
        """Restart the fixed loopback Fabric qualification agent safely."""
        if (
            settings.fabric_resource_url is None
            or settings.fabric_bearer_token is None
        ):
            raise ValueError("Fabric agent restart is not configured")
        try:
            safety.assert_action_allowed(ActionClass.SERVICE)
            config_root = settings.projects_config.parent.expanduser().resolve()
            service_home = config_root.parent.parent
            a6_state_root = service_home / ".local" / "state" / "runner-fabric"
            if a6_state_requested(a6_state_root):
                preflight = _require_fabric_bridge().preflight()
                repair_a6_qualification_binding(
                    environment=worker_qualification_environment,
                    config_dir=settings.projects_config.parent,
                    state_root=a6_state_root,
                    fabric_revision=preflight.get("source_revision"),
                )
            result = restart_fabric_qualification_agent(
                config_dir=settings.projects_config.parent,
                resource_url=settings.fabric_resource_url,
                bearer_token=settings.fabric_bearer_token,
            )
        except (
            FabricA6BindingRepairError,
            FabricAgentRestartError,
            FabricBridgeError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_fabric(
                "fabric_agent_restart",
                "fabric-agent:qualification",
                "denied",
            )
            raise ValueError("Fabric agent restart is unavailable") from exc
        _audit_fabric(
            "fabric_agent_restart",
            "fabric-agent:qualification",
            "restarted",
        )
        return result


    def tunnel_topology_refresh() -> dict:
        """Refresh private external topology evidence through AIfordable."""

        try:
            result = refresh_tunnel_topology_attestation(
                settings.projects_config.parent
            )
        except TunnelTopologyRefreshError as exc:
            reason = bounded_tunnel_topology_refresh_reason(exc)
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "tunnel_topology_refresh",
                    None,
                    "authenticated-client",
                    "blocked" if reason is not None else "denied",
                    utc_timestamp(),
                )
            )
            if reason is not None:
                return {
                    "state": "blocked",
                    "reason": reason,
                    "qualified": False,
                }
            raise ValueError("Tunnel topology refresh is unavailable") from exc
        audit.append(
            AuditEvent(
                current_request_id(),
                "tunnel_topology_refresh",
                None,
                "authenticated-client",
                "ok" if result.get("qualified") is True else "blocked",
                utc_timestamp(),
            )
        )
        return result

    mcp.tool()(tunnel_topology_refresh)

    def fabric_a6_update_qualification_prepare(candidate_commit: str) -> dict:
        """Prepare off-target A6 evidence without starting a Runner-MCP update."""
        try:
            result = _require_fabric_bridge().a6_update_qualification_prepare(
                candidate_commit
            )
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_a6_update_qualification_prepare",
                "runner-mcp:a6",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_a6_update_qualification_prepare",
            "runner-mcp:a6",
            "prepared",
        )
        return result

    def fabric_a6_update_qualification_finalize(
        correlation_id: str,
        job_id: str,
    ) -> dict:
        """Finalize off-target A6 evidence after an existing Runner-MCP update."""
        try:
            result = _require_fabric_bridge().a6_update_qualification_finalize(
                correlation_id,
                job_id,
            )
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_a6_update_qualification_finalize",
                "runner-mcp:a6",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_a6_update_qualification_finalize",
            "runner-mcp:a6",
            "qualified",
        )
        return result

    def bewind_disposable_bootstrap_restore() -> dict:
        """Restore the fixed aifordable-lab Bewind disposable bootstrap."""
        try:
            result = bewind_disposable_bootstrap_restorer.restore()
        except (
            BewindDisposableBootstrapError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_fabric(
                "bewind_disposable_bootstrap_restore",
                "worker:aifordable-lab",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "bewind_disposable_bootstrap_restore",
            "worker:aifordable-lab",
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_worker_qualification_policy_configure() -> dict:
        """Refresh the fixed Bewind bootstrap and configure its worker policy."""
        try:
            bewind_disposable_bootstrap_restorer.restore()
            result = bewind_worker_policy_configurator.configure()
        except (
            BewindDisposableBootstrapError,
            BewindWorkerQualificationPolicyError,
            OperatorStopActive,
            SafetyConfigurationError,
        ) as exc:
            _audit_fabric(
                "fabric_worker_qualification_policy_configure",
                "worker:aifordable-lab",
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_worker_qualification_policy_configure",
            "worker:aifordable-lab",
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_worker_qualification_readiness(
        worker_id: str,
        capability_profile: str,
    ) -> dict:
        """Return bounded Fabric-owned worker qualification readiness."""
        try:
            result = _require_fabric_bridge().worker_qualification_readiness(
                worker_id,
                capability_profile,
            )
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_worker_qualification_readiness",
                worker_id,
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_worker_qualification_readiness",
            worker_id,
            "ready" if result.get("activationReady") is True else "blocked",
        )
        return result

    def fabric_worker_qualification_activate(
        worker_id: str,
        capability_profile: str,
        expected_generation: int,
    ) -> dict:
        """Request one Fabric-owned bounded worker qualification provision."""
        try:
            result = _require_fabric_bridge().worker_qualification_provision(
                worker_id,
                capability_profile,
                expected_generation,
            )
        except FabricBridgeError as exc:
            _audit_fabric(
                "fabric_worker_qualification_activate",
                worker_id,
                "denied",
            )
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_worker_qualification_activate",
            worker_id,
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_operational_snapshot() -> dict:
        """Return bounded end-to-end operational state from Runner Fabric."""
        try:
            result = _require_fabric_bridge().operational_snapshot()
        except FabricBridgeError as exc:
            _audit_fabric("fabric_operational_snapshot", "fabric:operational", "denied")
            raise ValueError(str(exc)) from None
        _audit_fabric("fabric_operational_snapshot", "fabric:operational", "ok")
        return result

    def fabric_run_work_unit(
        work_unit_id: str,
        project_id: str,
        work_item_id: str,
        expected_revision: str,
        change_plan_id: str,
        validation_profile: str = "foundation",
        correction_budget: int = 1,
        landing_mode: str = "managed_branch_push",
    ) -> dict:
        """Run or safely join one coarse Runner Fabric work-unit."""
        try:
            result = _require_fabric_bridge().run_work_unit(
                work_unit_id=work_unit_id,
                project_id=project_id,
                work_item_id=work_item_id,
                expected_revision=expected_revision,
                change_plan_id=change_plan_id,
                validation_profile=validation_profile,
                correction_budget=correction_budget,
                landing_mode=landing_mode,
            )
        except FabricBridgeError as exc:
            _audit_fabric("fabric_run_work_unit", work_unit_id, "denied")
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_run_work_unit",
            work_unit_id,
            str(result.get("state", "unknown")),
        )
        return result

    def fabric_get_work_unit(work_unit_id: str) -> dict:
        """Return bounded local Runner Fabric work-unit state."""
        try:
            result = _require_fabric_bridge().get_work_unit(work_unit_id)
        except FabricBridgeError as exc:
            _audit_fabric("fabric_get_work_unit", work_unit_id, "denied")
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_get_work_unit",
            work_unit_id,
            str(result.get("status", "unknown")),
        )
        return result

    def fabric_cancel_work_unit(work_unit_id: str) -> dict:
        """Request bounded cooperative cancellation of one Fabric work-unit."""
        try:
            result = _require_fabric_bridge().cancel_work_unit(work_unit_id)
        except FabricBridgeError as exc:
            _audit_fabric("fabric_cancel_work_unit", work_unit_id, "denied")
            raise ValueError(str(exc)) from None
        _audit_fabric(
            "fabric_cancel_work_unit",
            work_unit_id,
            str(result.get("status", "unknown")),
        )
        return result

    mcp.tool()(bewind_disposable_bootstrap_restore)
    mcp.tool()(fabric_worker_qualification_policy_configure)

    if fabric_bridge is not None:
        mcp.tool()(fabric_bridge_preflight)
        mcp.tool()(fabric_host_inspect)
        mcp.tool()(fabric_external_target_preflight)
        mcp.tool()(fabric_external_target_inspect)
        mcp.tool()(fabric_ci_runner_guest_status)
        mcp.tool()(fabric_ci_runner_guest_start)
        mcp.tool()(fabric_ci_runner_guest_stop)
        mcp.tool()(fabric_agent_restart)
        mcp.tool()(fabric_a6_update_qualification_prepare)
        mcp.tool()(fabric_a6_update_qualification_finalize)
        mcp.tool()(fabric_worker_qualification_readiness)
        mcp.tool()(fabric_worker_qualification_activate)
        mcp.tool()(fabric_operational_snapshot)
        mcp.tool()(fabric_run_work_unit)
        mcp.tool()(fabric_get_work_unit)
        mcp.tool()(fabric_cancel_work_unit)

    def _ci_runner_spec(alias: str):
        spec = ci_runner_specs.get(alias)
        if spec is None:
            raise ValueError("Unknown or disabled CI runner")
        return spec

    def _ci_guest_spec(alias: str) -> CIRunnerGuestSpec:
        spec = ci_guest_specs.get(alias)
        if spec is None:
            raise ValueError("Unknown or disabled CI guest")
        return spec

    def list_ci_runners() -> list[dict[str, object]]:
        """List configured CI runner aliases without private host paths."""
        result = [
            {
                "alias": spec.alias,
                "repository": spec.repository,
                "runner_name": spec.runner_name,
                "labels": list(spec.labels),
            }
            for spec in sorted(ci_runner_specs.values(), key=lambda item: item.alias)
        ]
        audit.append(
            AuditEvent(
                current_request_id(),
                "list_ci_runners",
                None,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    def ci_runner_status(alias: str) -> dict:
        """Return bounded local registration readiness for one configured CI runner."""
        try:
            result = inspect_ci_runner(_ci_runner_spec(alias)).to_payload()
        except (CIRunnerLifecycleError, OSError) as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "ci_runner_status",
                    alias,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("CI runner status is unavailable") from exc
        audit.append(
            AuditEvent(
                current_request_id(),
                "ci_runner_status",
                alias,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    def ci_runner_plan(alias: str) -> dict:
        """Return the read-only enrollment plan for one configured CI runner."""
        try:
            result = plan_ci_runner(_ci_runner_spec(alias)).to_payload()
        except (CIRunnerLifecycleError, OSError) as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "ci_runner_plan",
                    alias,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("CI runner plan is unavailable") from exc
        audit.append(
            AuditEvent(
                current_request_id(),
                "ci_runner_plan",
                alias,
                "authenticated-client",
                "ok",
                utc_timestamp(),
            )
        )
        return result

    def ci_runner_enroll(alias: str) -> dict:
        """Enroll one preconfigured CI runner identity without caller path/argv authority."""
        if ci_runner_enrollment is None:
            raise ValueError("CI runner enrollment is not configured")
        try:
            safety.assert_action_allowed(ActionClass.SERVICE)
            result = ci_runner_enrollment.enroll(
                _ci_runner_spec(alias)
            ).to_payload()
        except (
            CIRunnerEnrollmentError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "ci_runner_enroll",
                    alias,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("CI runner enrollment is unavailable") from exc
        audit.append(
            AuditEvent(
                current_request_id(),
                "ci_runner_enroll",
                alias,
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    def ci_runner_guest_enroll(alias: str) -> dict:
        """Enroll one configured isolated CI guest without exposing registration secrets."""
        if ci_guest_enrollment is None:
            raise ValueError("CI guest enrollment is not configured")
        try:
            safety.assert_action_allowed(ActionClass.SERVICE)
            result = ci_guest_enrollment.enroll(
                _ci_guest_spec(alias)
            ).to_payload()
        except (
            CIRunnerGuestEnrollmentError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            audit.append(
                AuditEvent(
                    current_request_id(),
                    "ci_runner_guest_enroll",
                    alias,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("CI guest enrollment is unavailable") from exc
        audit.append(
            AuditEvent(
                current_request_id(),
                "ci_runner_guest_enroll",
                alias,
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    if ci_runner_specs:
        mcp.tool()(list_ci_runners)
        mcp.tool()(ci_runner_status)
        mcp.tool()(ci_runner_plan)
        if ci_runner_enrollment is not None:
            mcp.tool()(ci_runner_enroll)

    if ci_guest_enrollment is not None:
        mcp.tool()(ci_runner_guest_enroll)

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
    def known_project_preflight(project_id: str) -> dict:
        """Return bounded preparation state for one built-in managed project."""
        request_id = current_request_id()
        try:
            result = preflight_known_project_binding(
                registry,
                project_id=project_id,
            )
            if result.get("state") == "ready-to-prepare":
                source = preflight_known_project_source_binding(
                    project_id=project_id,
                    github_token=known_project_github_token(project_id),
                    local_source_bindings_raw=known_project_local_sources or None,
                )
                if source.get("reason_code") not in {"ready", "local-source-ready"}:
                    result = {
                        "code": str(source.get("code", project_id)),
                        "repository": str(source.get("repository", result.get("repository", ""))),
                        "state": str(source.get("reason_code", "source-unavailable")),
                    }
        except KnownProjectRegistrationError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "known_project_preflight",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                request_id,
                "known_project_preflight",
                str(result.get("code", project_id)),
                "authenticated-client",
                str(result.get("state", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def known_project_source_preflight(project_id: str) -> dict:
        """Return bounded source-auth readiness for one built-in managed project."""
        request_id = current_request_id()
        try:
            result = preflight_known_project_source_binding(
                project_id=project_id,
                github_token=known_project_github_token(project_id),
                local_source_bindings_raw=known_project_local_sources or None,
            )
        except KnownProjectRegistrationError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "known_project_source_preflight",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                request_id,
                "known_project_source_preflight",
                str(result.get("code", project_id)),
                "authenticated-client",
                str(result.get("reason_code", "unknown")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def prepare_known_project(project_id: str) -> dict:
        """Prepare one built-in managed project clone without caller-selected repo or path."""
        request_id = current_request_id()
        if safety.status().stop_active:
            audit.append(
                AuditEvent(
                    request_id,
                    "prepare_known_project",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("Emergency stop is active")
        try:
            result = prepare_known_project_binding(
                registry,
                project_id=project_id,
                github_token=known_project_github_token(project_id),
                local_source_bindings_raw=known_project_local_sources or None,
            )
        except KnownProjectRegistrationError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "prepare_known_project",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                request_id,
                "prepare_known_project",
                str(result.get("code", project_id)),
                "authenticated-client",
                str(result.get("state", "prepared")),
                utc_timestamp(),
            )
        )
        return result

    @mcp.tool()
    def register_known_project(project_id: str) -> dict:
        """Register one built-in managed project without caller-selected repo or path."""
        request_id = current_request_id()
        if safety.status().stop_active:
            audit.append(
                AuditEvent(
                    request_id,
                    "register_known_project",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError("Emergency stop is active")
        try:
            result = register_known_project_binding(
                settings.projects_config.parent,
                settings.projects_config,
                registry,
                project_id=project_id,
            )
        except KnownProjectRegistrationError as exc:
            audit.append(
                AuditEvent(
                    request_id,
                    "register_known_project",
                    project_id,
                    "authenticated-client",
                    "denied",
                    utc_timestamp(),
                )
            )
            raise ValueError(str(exc)) from None
        audit.append(
            AuditEvent(
                request_id,
                "register_known_project",
                str(result.get("code", project_id)),
                "authenticated-client",
                str(result.get("state", "registered")),
                utc_timestamp(),
            )
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
        return migration_plan_material(registry, project)

    def _migration_async_approval_material(
        project: str,
    ) -> tuple[dict, dict, dict]:
        return async_migration_approval_material(registry, project)

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
        if action == "migration_async":
            _migration_binding, approval_binding, summary = (
                _migration_async_approval_material(project)
            )
            return approval_binding, summary
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
        """Create a short-lived human approval plan for a supported staging action."""
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

    def _require_migration_jobs() -> MigrationJobRunner:
        if migration_jobs is None:
            raise ValueError("Migration jobs are not configured")
        return migration_jobs

    @mcp.tool()
    def start_migration_job(project: str, approval_id: str) -> dict:
        """Start one durable asynchronous migration after matching human approval."""
        try:
            jobs = _require_migration_jobs()
            migration_binding, approval_binding, summary = (
                _migration_async_approval_material(project)
            )
            safety.assert_project_action_allowed(
                ActionClass.MIGRATION,
                environment=str(migration_binding["environment"]),
            )
            _require_approval_manager().consume(
                approval_id,
                action="migration_async",
                project=project,
                binding=approval_binding,
            )
            result = jobs.start(
                project,
                expected_binding_fingerprint=migration_binding_fingerprint(
                    migration_binding
                ),
                expected_commit=str(summary["commit"]),
            )
        except (
            ApprovalError,
            MigrationJobError,
            SourceControlError,
            OperatorStopActive,
            SafetyConfigurationError,
            ValueError,
        ) as exc:
            _audit_database_result(
                tool_name="start_migration_job",
                project=project,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(
            tool_name="start_migration_job",
            project=project,
            result="started",
        )
        return result

    @mcp.tool()
    def migration_job_status(job_id: str) -> dict:
        """Return safe persisted status for one asynchronous migration job."""
        try:
            result = _require_migration_jobs().status(job_id)
        except (MigrationJobError, ValueError) as exc:
            _audit_database_result(
                tool_name="migration_job_status",
                project=None,
                result="denied",
            )
            raise ValueError(str(exc)) from None
        _audit_database_result(
            tool_name="migration_job_status",
            project=str(result.get("project")),
            result=str(result.get("state", "unknown")),
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


async def runner_mcp_interface_schema_digest(mcp: MCPServer) -> str:
    """Hash exact registered MCP tool names and generated JSON schemas."""

    if not isinstance(mcp, MCPServer):
        raise TypeError("mcp must be MCPServer")
    tools = await mcp.list_tools()
    if not 1 <= len(tools) <= 512:
        raise ValueError("Runner MCP tool surface is outside supported bounds")
    interface: list[dict[str, object]] = []
    for tool in sorted(tools, key=lambda item: item.name):
        if (
            not isinstance(tool.name, str)
            or not 1 <= len(tool.name) <= 128
            or not tool.name.isascii()
        ):
            raise ValueError("Runner MCP tool name is invalid")
        interface.append(
            {
                "name": tool.name,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
            }
        )
    try:
        encoded = json.dumps(
            interface,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Runner MCP tool schema is not canonical JSON") from exc
    if not encoded or len(encoded) > 4 * 1024 * 1024:
        raise ValueError("Runner MCP tool schema exceeds supported bounds")
    return hashlib.sha256(encoded).hexdigest()


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_app(
    settings: Settings | None = None,
    registry: ProjectRegistry | None = None,
    secret_values: Mapping[str, str] | None = None,
    self_update_restart_components: frozenset[str] | None = None,
    server_bind_host: str | None = None,
    server_bind_port: int | None = None,
) -> Starlette:
    settings = settings or Settings.from_env()
    registry = registry or load_project_registry(settings.projects_config)
    try:
        package_version = version("aifordable-runner-mcp")
    except PackageNotFoundError:
        package_version = "development"
    identity: BuildIdentity | None = None
    source_revision = installed_source_revision(settings.projects_config.parent)

    def current_build_identity() -> BuildIdentity:
        if identity is None:
            return runner_mcp_mcp_build_identity(
                package_version,
                source_revision=source_revision,
            )
        return identity

    audit = AuditLogger(
        settings.audit_log,
        build_identity=runner_mcp_build_identity(
            package_version,
            source_revision=source_revision,
        ),
    )
    audit.append(
        AuditEvent(
            "runtime-start",
            "runtime",
            None,
            "system",
            "started",
            utc_timestamp(),
        )
    )
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
        self_update_restart_components=self_update_restart_components,
        server_bind_host=server_bind_host,
        server_bind_port=server_bind_port,
        build_identity_provider=current_build_identity,
    )
    transport_security = transport_security_for(settings.resource_url)

    @asynccontextmanager
    async def lifespan(_: Starlette):
        nonlocal identity
        identity = runner_mcp_mcp_build_identity(
            package_version,
            source_revision=source_revision,
            interface_schema_digest=await runner_mcp_interface_schema_digest(mcp),
        )
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
