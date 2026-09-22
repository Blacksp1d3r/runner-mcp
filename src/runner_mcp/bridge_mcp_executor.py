from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .bridge_processor import BridgeExecutionAdapterError

MAX_MCP_RESPONSE_BYTES = 1_048_576
MAX_MCP_SESSION_ID_CHARS = 256
MAX_MCP_JOB_ID_CHARS = 32
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


class LocalMCPClient:
    """Minimal loopback-only MCP client used by the GitHub watcher."""

    def __init__(self, config: LocalMCPConfig) -> None:
        self._config = config
        self._session_id: str | None = None
        self._next_request_id = 1
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "runner-mcp-github-watcher",
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

        self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )
        self._initialized = True

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in {
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
            "plan_deploy",
            "deploy_staging",
            "deployment_status",
            "list_releases",
            "rollback_plan",
            "rollback_release",
            "rollback_status",
            "runtime_status",
            "runtime_doctor",
            "self_update",
            "self_update_status",
        }:
            raise BridgeExecutionAdapterError(
                "local MCP executor rejected an unsupported tool"
            )
        self.initialize()
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_request_id(),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
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
            "User-Agent": "runner-mcp-github-watcher",
        }
        if self._session_id is not None:
            headers["Mcp-Session-Id"] = self._session_id

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
        except (
            urllib.error.HTTPError,
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
            client = LocalMCPClient(self._config)
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
        if operation not in {"migration", "deploy", "code_rollback"}:
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
