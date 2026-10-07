from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS

from .bridge_processor import BridgeExecutionAdapterError
from .http_middleware import active_traceparent


class _StaleMCPSessionError(BridgeExecutionAdapterError):
    """Internal marker for a confirmed stale downstream MCP session."""


MAX_MCP_RESPONSE_BYTES = 1_048_576
MAX_MCP_SESSION_ID_CHARS = 256
MAX_MCP_JOB_ID_CHARS = 32
_MCP_PROTOCOL_VERSION = "2025-06-18"
_MCP_PREVIOUS_PROTOCOL_VERSION = "2025-03-26"
_MCP_POLICY_PROTOCOL_VERSIONS = frozenset(
    {_MCP_PROTOCOL_VERSION, _MCP_PREVIOUS_PROTOCOL_VERSION}
)
_PEER_LOGGER = logging.getLogger("runner_mcp.peer_identity")
_PEER_INFO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ +:/()-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._~-]{1,256}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_TERMINAL_TEST_STATES = {
    "passed",
    "failed",
    "timed_out",
    "stopped",
    "cancelled",
    "interrupted",
}
_NONTERMINAL_TEST_STATES = {"queued", "claimed", "running"}
_MIGRATION_JOB_STATES = {
    "queued",
    "running",
    "completed",
    "stopped",
    "error",
    "interrupted",
}
_MIGRATION_JOB_KEYS = {
    "job_id",
    "project",
    "operation",
    "state",
    "created_at",
    "started_at",
    "finished_at",
    "migration_state",
    "error_category",
    "pre_migration_backup_created",
    "output_truncated",
}


def _validate_migration_job_payload(
    payload: Any,
    *,
    expected_project: str | None = None,
    require_initial: bool = False,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _MIGRATION_JOB_KEYS:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job result"
        )
    job_id = payload.get("job_id")
    project = payload.get("project")
    state = payload.get("state")
    if not isinstance(job_id, str) or not _JOB_ID_RE.fullmatch(job_id):
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job identifier"
        )
    if (
        not isinstance(project, str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", project)
        or (expected_project is not None and project != expected_project)
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job project"
        )
    if payload.get("operation") != "migration":
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job operation"
        )
    if not isinstance(state, str) or state not in _MIGRATION_JOB_STATES:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job state"
        )

    created_at = payload.get("created_at")
    started_at = payload.get("started_at")
    finished_at = payload.get("finished_at")
    migration_state = payload.get("migration_state")
    error_category = payload.get("error_category")
    backup_created = payload.get("pre_migration_backup_created")
    output_truncated = payload.get("output_truncated")

    if not isinstance(created_at, str) or not 1 <= len(created_at) <= 64:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration job timestamp"
        )
    for value in (started_at, finished_at):
        if value is not None and (
            not isinstance(value, str) or not 1 <= len(value) <= 64
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an invalid migration job timestamp"
            )
    if migration_state not in {None, "applied", "failed", "timed_out"}:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration result state"
        )
    if error_category not in {
        None,
        "operator_stop",
        "safety_configuration",
        "plan_changed",
        "database_busy",
        "migration_failed",
        "migration_timed_out",
        "runner_restart",
        "unexpected_error",
    }:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid migration error category"
        )
    if not isinstance(backup_created, bool) or not isinstance(output_truncated, bool):
        raise BridgeExecutionAdapterError(
            "Runner MCP returned invalid migration job evidence"
        )

    if state == "queued":
        if any(
            value is not None
            for value in (started_at, finished_at, migration_state, error_category)
        ) or backup_created or output_truncated:
            raise BridgeExecutionAdapterError(
                "Runner MCP returned inconsistent queued migration state"
            )
    elif state == "running":
        if (
            started_at is None
            or finished_at is not None
            or migration_state is not None
            or error_category is not None
            or backup_created
            or output_truncated
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned inconsistent running migration state"
            )
    elif state == "completed":
        if (
            started_at is None
            or finished_at is None
            or migration_state != "applied"
            or error_category is not None
            or not backup_created
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned inconsistent completed migration state"
            )
    elif state == "stopped":
        if (
            finished_at is None
            or migration_state is not None
            or error_category != "operator_stop"
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned inconsistent stopped migration state"
            )
    elif state == "interrupted":
        if (
            finished_at is None
            or migration_state is not None
            or error_category != "runner_restart"
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned inconsistent interrupted migration state"
            )
    elif finished_at is None or error_category is None:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned inconsistent failed migration state"
        )

    if require_initial and state != "queued":
        raise BridgeExecutionAdapterError(
            "Runner MCP returned an invalid initial migration job state"
        )
    return payload


@dataclass(frozen=True, slots=True)
class LocalMCPConfig:
    endpoint: str
    bearer_token: str
    request_timeout_seconds: float = 30.0
    test_wait_timeout_seconds: float = 900.0
    test_poll_interval_seconds: float = 0.5

    def __post_init__(self) -> None:
        _validate_endpoint(self.endpoint)
        _validate_token(self.bearer_token)
        if not 1 <= self.request_timeout_seconds <= 120:
            raise ValueError("MCP request timeout is outside the supported range")
        if not 5 <= self.test_wait_timeout_seconds <= 3_900:
            raise ValueError("MCP test wait timeout is outside the supported range")
        if not 0.1 <= self.test_poll_interval_seconds <= 5:
            raise ValueError("MCP test poll interval is outside the supported range")


def _validate_endpoint(endpoint: str) -> None:
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("local MCP endpoint must use HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ValueError("local MCP endpoint must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("local MCP endpoint must not contain query or fragment")
    if parsed.hostname not in _LOOPBACK_HOSTS:
        raise ValueError("local MCP endpoint must use a loopback host")
    if parsed.path.rstrip("/") != "/mcp":
        raise ValueError("local MCP endpoint path must be /mcp")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("local MCP endpoint port is invalid") from exc
    if port is not None and not 1 <= port <= 65_535:
        raise ValueError("local MCP endpoint port is invalid")


def _validate_token(token: str) -> None:
    if not token or len(token) > 4_096:
        raise ValueError("Runner MCP bearer token is missing or unreasonably large")
    if not token.isascii():
        raise ValueError("Runner MCP bearer token must use ASCII characters")
    if any(ord(char) < 33 or ord(char) == 127 for char in token):
        raise ValueError("Runner MCP bearer token contains unsupported characters")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _strict_json_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonstandard_json_constant,
    )


def _decode_mcp_response(raw: bytes) -> dict[str, Any] | None:
    if len(raw) > MAX_MCP_RESPONSE_BYTES:
        raise BridgeExecutionAdapterError("Runner MCP response exceeds size limit")
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise BridgeExecutionAdapterError(
            "Runner MCP response must be UTF-8"
        ) from exc
    if not text:
        return None

    try:
        if text.startswith("{"):
            parsed = _strict_json_loads(text)
            if not isinstance(parsed, dict):
                raise BridgeExecutionAdapterError(
                    "Runner MCP response must be a JSON object"
                )
            return parsed

        blocks = text.replace("\r\n", "\n").split("\n\n")
        data_payloads: list[str] = []
        for block in blocks:
            lines = block.splitlines()
            data_lines = [
                line[5:].lstrip()
                for line in lines
                if line.startswith("data:")
            ]
            if data_lines:
                data_payloads.append("\n".join(data_lines))

        if len(data_payloads) != 1:
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an unsupported event stream"
            )
        parsed = _strict_json_loads(data_payloads[0])
        if not isinstance(parsed, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP response must be a JSON object"
            )
        return parsed
    except BridgeExecutionAdapterError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise BridgeExecutionAdapterError(
            "Runner MCP returned invalid JSON"
        ) from exc


def _validate_initialize_peer(value: object) -> dict[str, str | None]:
    if not isinstance(value, dict):
        raise BridgeExecutionAdapterError(
            "Runner MCP initialization result is invalid"
        )
    protocol = value.get("protocolVersion")
    if protocol is not None and (
        not isinstance(protocol, str)
        or protocol not in _MCP_POLICY_PROTOCOL_VERSIONS
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP protocol version is incompatible"
        )

    server_name: str | None = None
    server_version: str | None = None
    server_info = value.get("serverInfo")
    if server_info is not None:
        if not isinstance(server_info, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP server identity container is invalid"
            )
        name = server_info.get("name")
        version = server_info.get("version")
        if name is not None and (
            not isinstance(name, str)
            or _PEER_INFO_RE.fullmatch(name) is None
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP server identity name is invalid"
            )
        if version is not None and (
            not isinstance(version, str)
            or len(version) > 128
            or not version.isascii()
            or any(ord(char) < 32 or ord(char) == 127 for char in version)
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP server identity version is invalid"
            )
        server_name = name
        server_version = version or None

    return {
        "protocol_version": protocol,
        "server_name": server_name,
        "server_version": server_version,
    }


def _validate_peer_tool_surface(
    response: object,
    *,
    required_tools: frozenset[str],
) -> tuple[str, frozenset[str]]:
    if not isinstance(response, dict) or "error" in response:
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    result = response.get("result")
    if not isinstance(result, dict):
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    tools = result.get("tools")
    if not isinstance(tools, list) or not 1 <= len(tools) <= 512:
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    interface: list[dict[str, object]] = []
    names: set[str] = set()
    for item in tools:
        if not isinstance(item, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP interface schema is incompatible"
            )
        name = item.get("name")
        input_schema = item.get("inputSchema")
        output_schema = item.get("outputSchema")
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", name)
            or name in names
            or not isinstance(input_schema, dict)
            or (
                output_schema is not None
                and not isinstance(output_schema, dict)
            )
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP interface schema is incompatible"
            )
        names.add(name)
        interface.append(
            {
                "name": name,
                "input_schema": input_schema,
                "output_schema": output_schema,
            }
        )
    required = set(required_tools) | {"build_identity"}
    if not required.issubset(names):
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    encoded = json.dumps(
        sorted(interface, key=lambda item: str(item["name"])),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    if not encoded or len(encoded) > 4 * 1024 * 1024:
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    return hashlib.sha256(encoded).hexdigest(), frozenset(names)


def _tool_result_payload(response: object) -> dict[str, Any]:
    if not isinstance(response, dict) or "error" in response:
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        )
    result = response.get("result")
    if not isinstance(result, dict) or result.get("isError") is True:
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        )
    content = result.get("content")
    if not isinstance(content, list) or len(content) != 1:
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        )
    item = content[0]
    if (
        not isinstance(item, dict)
        or item.get("type") != "text"
        or not isinstance(item.get("text"), str)
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        )
    try:
        payload = _strict_json_loads(item["text"])
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        ) from exc
    if not isinstance(payload, dict):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is unavailable"
        )
    return payload


def _validate_peer_build_identity(
    payload: object,
    *,
    observed_interface_digest: str,
    negotiated_protocol_version: str,
    expected_component_id: str = "runner-mcp",
) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is incompatible"
        )
    expected = {
        "component_id",
        "build_version",
        "source_revision",
        "artifact_digest",
        "protocol_min",
        "protocol_max",
        "interface_schema_digest",
    }
    if (
        not isinstance(expected_component_id, str)
        or not re.fullmatch(r"[a-z][a-z0-9._:-]{0,127}", expected_component_id)
        or set(payload) != expected
        or payload.get("component_id") != expected_component_id
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is incompatible"
        )
    build_version = payload.get("build_version")
    source_revision = payload.get("source_revision")
    artifact_digest = payload.get("artifact_digest")
    protocol_min = payload.get("protocol_min")
    protocol_max = payload.get("protocol_max")
    interface_digest = payload.get("interface_schema_digest")
    if (
        not isinstance(build_version, str)
        or not build_version
        or len(build_version) > 128
        or not build_version.isascii()
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is incompatible"
        )
    if source_revision is not None and (
        not isinstance(source_revision, str)
        or _REVISION_RE.fullmatch(source_revision) is None
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is incompatible"
        )
    if artifact_digest is not None and (
        not isinstance(artifact_digest, str)
        or _DIGEST_RE.fullmatch(artifact_digest) is None
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP build identity is incompatible"
        )
    if (
        not isinstance(protocol_min, str)
        or not isinstance(protocol_max, str)
        or not _protocol_range_contains(
            negotiated_protocol_version,
            protocol_min=protocol_min,
            protocol_max=protocol_max,
        )
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP protocol version is incompatible"
        )
    if (
        not isinstance(interface_digest, str)
        or _DIGEST_RE.fullmatch(interface_digest) is None
        or interface_digest != observed_interface_digest
    ):
        raise BridgeExecutionAdapterError(
            "Runner MCP interface schema is incompatible"
        )
    return dict(payload)


def _protocol_range_contains(
    protocol_version: str,
    *,
    protocol_min: str,
    protocol_max: str,
) -> bool:
    versions = tuple(HANDSHAKE_PROTOCOL_VERSIONS)
    if (
        protocol_version not in versions
        or protocol_min not in versions
        or protocol_max not in versions
    ):
        return False
    return (
        versions.index(protocol_min)
        <= versions.index(protocol_version)
        <= versions.index(protocol_max)
    )


def _log_peer_identity_observed(
    *,
    protocol_version: str | None,
    server_name: str | None,
    server_version: str | None,
    build_identity: dict[str, object],
) -> None:
    if not isinstance(build_identity, dict):
        raise TypeError("build_identity must be a dict")
    _PEER_LOGGER.info(
        json.dumps(
            {
                "event": "runner_mcp_peer_observed",
                "initialize_protocol_version": protocol_version,
                "server_name": server_name,
                "server_version": server_version,
                **{
                    f"peer_{key}": value
                    for key, value in build_identity.items()
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


_RUNNER_MCP_BRIDGE_TOOLS = frozenset(
    {
        "list_projects",
        "safety_status",
        "project_status",
        "project_capabilities",
        "sync_project",
        "list_test_profiles",
        "run_tests",
        "test_status",
        "queue_status",
        "worker_status",
        "job_status",
        "cancel_job",
        "get_test_log",
        "list_services",
        "service_status",
        "start_service",
        "stop_service",
        "restart_service",
        "list_backups",
        "backup_database",
        "request_action_approval",
        "approval_status",
        "migration_status",
        "apply_migrations",
        "start_migration_job",
        "migration_job_status",
        "plan_deploy",
        "deploy_staging",
        "deployment_status",
        "list_releases",
        "rollback_plan",
        "rollback_release",
        "rollback_status",
        "runtime_status",
        "runtime_doctor",
        "fabric_operational_snapshot",
        "self_update",
        "self_update_status",
        "fabric_bootstrap",
        "fabric_bootstrap_status",
    }
)


class LocalMCPClient:
    """Minimal loopback-only MCP client with a fixed internal tool allow-list."""

    def __init__(
        self,
        config: LocalMCPConfig,
        *,
        allowed_tools: frozenset[str] = _RUNNER_MCP_BRIDGE_TOOLS,
        client_name: str = "runner-mcp-github-watcher",
        compatibility_preflight: bool = False,
        required_tools: frozenset[str] | None = None,
        expected_component_id: str = "runner-mcp",
    ) -> None:
        if not isinstance(allowed_tools, frozenset) or not allowed_tools:
            raise ValueError("MCP tool allow-list must be a non-empty frozenset")
        if any(
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name)
            for name in allowed_tools
        ):
            raise ValueError("MCP tool allow-list contains an invalid tool name")
        if not isinstance(client_name, str) or not re.fullmatch(
            r"[a-z][a-z0-9-]{0,63}",
            client_name,
        ):
            raise ValueError("MCP client name is invalid")
        if not isinstance(compatibility_preflight, bool):
            raise TypeError("compatibility_preflight must be boolean")
        if required_tools is not None and not isinstance(required_tools, frozenset):
            raise TypeError("required_tools must be a frozenset or None")
        if (
            not isinstance(expected_component_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9._:-]{0,127}", expected_component_id)
        ):
            raise ValueError("expected MCP component id is invalid")
        effective_required_tools = (
            allowed_tools if required_tools is None else required_tools
        )
        if not effective_required_tools.issubset(allowed_tools):
            raise ValueError("required MCP tools must be allowed")
        self._config = config
        self._allowed_tools = allowed_tools
        self._required_tools = effective_required_tools
        self._client_name = client_name
        self._compatibility_preflight = compatibility_preflight
        self._expected_component_id = expected_component_id
        self._session_id: str | None = None
        self._next_request_id = 1
        self._initialized = False
        self._peer_protocol_version: str | None = None
        self._peer_server_name: str | None = None
        self._peer_server_version: str | None = None
        self._peer_build_identity: dict[str, object] | None = None
        self._peer_tool_names: frozenset[str] = frozenset()

    @property
    def peer_identity(self) -> dict[str, str | None]:
        return {
            "protocol_version": self._peer_protocol_version,
            "server_name": self._peer_server_name,
            "server_version": self._peer_server_version,
        }

    @property
    def peer_build_identity(self) -> dict[str, object] | None:
        return (
            None
            if self._peer_build_identity is None
            else dict(self._peer_build_identity)
        )

    @property
    def peer_tool_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._peer_tool_names))

    def initialize(self) -> None:
        if self._initialized:
            return

        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": _MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": self._client_name,
                        "version": "1",
                    },
                },
            }
        )
        if response is None or self._session_id is None:
            raise BridgeExecutionAdapterError(
                "Runner MCP initialization failed"
            )
        if "error" in response:
            raise BridgeExecutionAdapterError(
                "Runner MCP initialization was rejected"
            )
        peer = _validate_initialize_peer(response.get("result"))
        self._peer_protocol_version = peer["protocol_version"]
        self._peer_server_name = peer["server_name"]
        self._peer_server_version = peer["server_version"]

        self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )
        if self._compatibility_preflight:
            tool_surface = self._post(
                {
                    "jsonrpc": "2.0",
                    "id": self._allocate_request_id(),
                    "method": "tools/list",
                    "params": {},
                }
            )
            observed_digest, tool_names = _validate_peer_tool_surface(
                tool_surface,
                required_tools=self._required_tools,
            )
            identity_response = self._post(
                {
                    "jsonrpc": "2.0",
                    "id": self._allocate_request_id(),
                    "method": "tools/call",
                    "params": {
                        "name": "build_identity",
                        "arguments": {},
                    },
                }
            )
            if self._peer_protocol_version is None:
                raise BridgeExecutionAdapterError(
                    "Runner MCP protocol version is unavailable"
                )
            self._peer_build_identity = _validate_peer_build_identity(
                _tool_result_payload(identity_response),
                observed_interface_digest=observed_digest,
                negotiated_protocol_version=self._peer_protocol_version,
                expected_component_id=self._expected_component_id,
            )
            self._peer_tool_names = tool_names
            _log_peer_identity_observed(
                protocol_version=self._peer_protocol_version,
                server_name=self._peer_server_name,
                server_version=self._peer_server_version,
                build_identity=self._peer_build_identity,
            )
        self._initialized = True

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._allowed_tools:
            raise BridgeExecutionAdapterError(
                "local MCP executor rejected an unsupported tool"
            )
        self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "id": self._allocate_request_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        try:
            response = self._post(payload)
        except _StaleMCPSessionError:
            self._session_id = None
            self._initialized = False
            self._peer_protocol_version = None
            self._peer_server_name = None
            self._peer_server_version = None
            self._peer_build_identity = None
            self._peer_tool_names = frozenset()
            self.initialize()
            payload = {
                **payload,
                "id": self._allocate_request_id(),
            }
            response = self._post(payload)
        if response is None or not isinstance(response, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an empty tool response"
            )
        if "error" in response:
            raise BridgeExecutionAdapterError(
                "Runner MCP rejected the tool request"
            )

        result = response.get("result")
        if not isinstance(result, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an invalid tool result"
            )
        if result.get("isError") is True:
            raise BridgeExecutionAdapterError(
                "Runner MCP tool execution failed"
            )

        content = result.get("content")
        if content in (None, []):
            return None
        if not isinstance(content, list) or len(content) > 256:
            raise BridgeExecutionAdapterError(
                "Runner MCP returned unsupported tool content"
            )

        parsed_items: list[Any] = []
        for item in content:
            if (
                not isinstance(item, dict)
                or item.get("type") != "text"
                or not isinstance(item.get("text"), str)
            ):
                raise BridgeExecutionAdapterError(
                    "Runner MCP returned unsupported tool content"
                )
            try:
                parsed_items.append(_strict_json_loads(item["text"]))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise BridgeExecutionAdapterError(
                    "Runner MCP tool content is not valid JSON"
                ) from exc

        if len(parsed_items) == 1:
            return parsed_items[0]
        if name in {
            "list_projects",
            "list_test_profiles",
            "list_services",
            "list_backups",
            "list_releases",
        } and all(
            isinstance(item, dict) for item in parsed_items
        ):
            return parsed_items
        raise BridgeExecutionAdapterError(
            "Runner MCP returned unsupported tool content"
        )

    def _allocate_request_id(self) -> int:
        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        data = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._config.bearer_token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": self._client_name,
        }
        if self._session_id is not None:
            headers["Mcp-Session-Id"] = self._session_id
        if self._peer_protocol_version is not None:
            headers["MCP-Protocol-Version"] = self._peer_protocol_version
        traceparent = active_traceparent()
        if traceparent is not None:
            headers["traceparent"] = traceparent

        request = urllib.request.Request(
            self._config.endpoint,
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._config.request_timeout_seconds,
            ) as response:
                raw = response.read(MAX_MCP_RESPONSE_BYTES + 1)
                if self._session_id is None:
                    session_id = response.headers.get("Mcp-Session-Id")
                    if session_id is not None:
                        if (
                            len(session_id) > MAX_MCP_SESSION_ID_CHARS
                            or not _SESSION_ID_RE.fullmatch(session_id)
                        ):
                            raise BridgeExecutionAdapterError(
                                "Runner MCP returned an invalid session identifier"
                            )
                        self._session_id = session_id
        except BridgeExecutionAdapterError:
            raise
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and self._session_id is not None:
                raise _StaleMCPSessionError(
                    "Runner MCP session is no longer available"
                ) from exc
            raise BridgeExecutionAdapterError(
                "Runner MCP is unavailable or rejected the request"
            ) from exc
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:
            raise BridgeExecutionAdapterError(
                "Runner MCP is unavailable or rejected the request"
            ) from exc

        return _decode_mcp_response(raw)


class LocalMCPBridgeExecutor:
    """Explicit BridgeExecutor backed by the local Runner MCP endpoint."""

    def __init__(self, config: LocalMCPConfig) -> None:
        self._config = config
        self._local = threading.local()

    def _client(self) -> LocalMCPClient:
        client = getattr(self._local, "client", None)
        if client is None:
            client = LocalMCPClient(
                self._config,
                compatibility_preflight=True,
            )
            self._local.client = client
        return client

    def list_projects(self) -> Any:
        return self._client()._call_tool("list_projects", {})

    def safety_status(self) -> Any:
        return self._client()._call_tool("safety_status", {})

    def runtime_status(self) -> Any:
        return self._client()._call_tool("runtime_status", {})

    def runtime_doctor(self) -> Any:
        return self._client()._call_tool("runtime_doctor", {})

    def self_update(self, commit: str) -> Any:
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise BridgeExecutionAdapterError("Invalid self-update commit identifier")
        return self._client()._call_tool("self_update", {"commit": commit})

    def self_update_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid self-update job identifier")
        return self._client()._call_tool(
            "self_update_status",
            {"job_id": job_id},
        )

    def fabric_bootstrap(self, commit: str) -> Any:
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise BridgeExecutionAdapterError(
                "Invalid Runner Fabric bootstrap commit identifier"
            )
        return self._client()._call_tool(
            "fabric_bootstrap",
            {"commit": commit},
        )

    def fabric_bootstrap_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError(
                "Invalid Runner Fabric bootstrap job identifier"
            )
        return self._client()._call_tool(
            "fabric_bootstrap_status",
            {"job_id": job_id},
        )

    def project_status(self, project: str) -> Any:
        return self._client()._call_tool(
            "project_status",
            {"project": project},
        )

    def project_capabilities(self, project: str) -> Any:
        return self._client()._call_tool(
            "project_capabilities",
            {"project": project},
        )

    def sync_project(self, project: str, commit: str) -> Any:
        if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
            raise BridgeExecutionAdapterError("Invalid Git commit identifier")
        return self._client()._call_tool(
            "sync_project",
            {"project": project, "commit": commit.lower()},
        )

    def list_test_profiles(self, project: str) -> Any:
        return self._client()._call_tool(
            "list_test_profiles",
            {"project": project},
        )

    def run_tests(self, project: str, suite: str) -> Any:
        started = self._client()._call_tool(
            "run_tests",
            {"project": project, "suite": suite},
        )
        if not isinstance(started, dict):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an invalid test start result"
            )
        job_id = started.get("job_id")
        if (
            not isinstance(job_id, str)
            or len(job_id) > MAX_MCP_JOB_ID_CHARS
            or not _JOB_ID_RE.fullmatch(job_id)
        ):
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an invalid test job identifier"
            )
        status = started.get("status")
        if status not in {"queued", "claimed", "running"}:
            raise BridgeExecutionAdapterError(
                "Runner MCP returned an invalid initial test status"
            )
        return started

    def queue_status(self) -> Any:
        return self._client()._call_tool("queue_status", {})

    def worker_status(self) -> Any:
        return self._client()._call_tool("worker_status", {})

    def job_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid test job identifier")
        return self._client()._call_tool("job_status", {"job_id": job_id})

    def cancel_job(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid test job identifier")
        return self._client()._call_tool("cancel_job", {"job_id": job_id})

    def job_log(self, job_id: str, *, offset: int = 0, length: int = 100) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid test job identifier")
        if offset < 0 or offset > 100_000:
            raise BridgeExecutionAdapterError("Invalid test log offset")
        if length < 1 or length > 100:
            raise BridgeExecutionAdapterError("Invalid test log length")
        return self._client()._call_tool(
            "get_test_log",
            {"job_id": job_id, "offset": offset, "length": length},
        )

    def list_services(self, project: str) -> Any:
        return self._client()._call_tool("list_services", {"project": project})

    def service_status(self, project: str, service: str) -> Any:
        return self._client()._call_tool(
            "service_status",
            {"project": project, "service": service},
        )

    def start_service(self, project: str, service: str) -> Any:
        return self._client()._call_tool(
            "start_service",
            {"project": project, "service": service},
        )

    def stop_service(self, project: str, service: str) -> Any:
        return self._client()._call_tool(
            "stop_service",
            {"project": project, "service": service},
        )

    def restart_service(self, project: str, service: str) -> Any:
        return self._client()._call_tool(
            "restart_service",
            {"project": project, "service": service},
        )

    def list_backups(self, project: str, *, limit: int = 100) -> Any:
        if limit < 1 or limit > 100:
            raise BridgeExecutionAdapterError("Invalid backup list limit")
        return self._client()._call_tool(
            "list_backups",
            {"project": project, "limit": limit},
        )

    def backup_database(self, project: str) -> Any:
        return self._client()._call_tool("backup_database", {"project": project})

    def request_action_approval(self, project: str, operation: str) -> Any:
        if operation not in {
            "migration",
            "migration_async",
            "deploy",
            "code_rollback",
        }:
            raise BridgeExecutionAdapterError("Invalid approval operation")
        return self._client()._call_tool(
            "request_action_approval",
            {"project": project, "action": operation},
        )

    def approval_status(self, approval_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(approval_id):
            raise BridgeExecutionAdapterError("Invalid approval identifier")
        return self._client()._call_tool(
            "approval_status",
            {"approval_id": approval_id},
        )

    def migration_status(self, project: str) -> Any:
        return self._client()._call_tool("migration_status", {"project": project})

    def apply_migrations(self, project: str, approval_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(approval_id):
            raise BridgeExecutionAdapterError("Invalid approval identifier")
        return self._client()._call_tool(
            "apply_migrations",
            {"project": project, "approval_id": approval_id},
        )

    def start_migration_job(self, project: str, approval_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(approval_id):
            raise BridgeExecutionAdapterError("Invalid approval identifier")
        result = self._client()._call_tool(
            "start_migration_job",
            {"project": project, "approval_id": approval_id},
        )
        return _validate_migration_job_payload(
            result,
            expected_project=project,
            require_initial=True,
        )

    def migration_job_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid migration job identifier")
        result = self._client()._call_tool(
            "migration_job_status",
            {"job_id": job_id},
        )
        validated = _validate_migration_job_payload(result)
        if validated["job_id"] != job_id:
            raise BridgeExecutionAdapterError(
                "Runner MCP returned a mismatched migration job identifier"
            )
        return validated

    def plan_deploy(self, project: str) -> Any:
        return self._client()._call_tool("plan_deploy", {"project": project})

    def deploy_staging(self, project: str, approval_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(approval_id):
            raise BridgeExecutionAdapterError("Invalid approval identifier")
        return self._client()._call_tool(
            "deploy_staging",
            {"project": project, "approval_id": approval_id},
        )

    def deployment_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid deployment job identifier")
        return self._client()._call_tool(
            "deployment_status",
            {"job_id": job_id},
        )

    def list_releases(self, project: str, *, limit: int = 100) -> Any:
        if limit < 1 or limit > 100:
            raise BridgeExecutionAdapterError("Invalid release list limit")
        return self._client()._call_tool(
            "list_releases",
            {"project": project, "limit": limit},
        )

    def rollback_plan(self, project: str) -> Any:
        return self._client()._call_tool("rollback_plan", {"project": project})

    def rollback_release(self, project: str, approval_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(approval_id):
            raise BridgeExecutionAdapterError("Invalid approval identifier")
        return self._client()._call_tool(
            "rollback_release",
            {"project": project, "approval_id": approval_id},
        )

    def rollback_status(self, job_id: str) -> Any:
        if not _JOB_ID_RE.fullmatch(job_id):
            raise BridgeExecutionAdapterError("Invalid rollback job identifier")
        return self._client()._call_tool("rollback_status", {"job_id": job_id})

    def run_tests_to_completion(self, project: str, suite: str) -> Any:
        """Compatibility helper for local callers; mailbox dispatch does not use it."""
        started = self.run_tests(project, suite)
        job_id = started["job_id"]

        deadline = time.monotonic() + self._config.test_wait_timeout_seconds
        while True:
            status_payload = self.job_status(job_id)
            if not isinstance(status_payload, dict):
                raise BridgeExecutionAdapterError(
                    "Runner MCP returned an invalid test status"
                )
            status = status_payload.get("status")
            if not isinstance(status, str):
                raise BridgeExecutionAdapterError(
                    "Runner MCP returned an invalid test status"
                )

            if status in _TERMINAL_TEST_STATES:
                return {
                    "project": project,
                    "suite": suite,
                    "status": status,
                }
            if status not in _NONTERMINAL_TEST_STATES:
                raise BridgeExecutionAdapterError(
                    "Runner MCP returned an unsupported test status"
                )
            if time.monotonic() >= deadline:
                raise BridgeExecutionAdapterError(
                    "Runner MCP test wait timeout expired"
                )
            time.sleep(self._config.test_poll_interval_seconds)
