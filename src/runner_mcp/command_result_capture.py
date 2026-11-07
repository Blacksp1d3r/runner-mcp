"""Safe MCP completion metadata upload for the registered AIfordable lab runner."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import secrets
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from .aifordable_relay import AIfordableRelayConfig

_ROUTE = "/internal/control-relay/command-results"
_EXPECTED_SUBJECT = "runner:aifordable-lab"
_CUSTOMER_ID = "AF-CUSTOMER-0001"
_HOST_ID = "AF-VM-0001"
_SERVICE_ID = "AF-SVC-0003"
_PROJECT_ID = "runner-mcp"
_COMMAND_LABEL = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_EVIDENCE_REF = re.compile(r"^cmd:[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_AUTHORITY = re.compile(r"^infra:[0-9a-f]{64}$")
_MAX_RESPONSE_BYTES = 16 * 1024
_MAX_BATCH = 25
_MAX_RECORDS = 1024
_MAX_TIMEOUT_SECONDS = 2.0


class CommandResultCaptureError(RuntimeError):
    """Safe command-result failure code without credentials or response details."""

    def __init__(self, code: str) -> None:
        if code not in {
            "configuration_unavailable",
            "invalid_record",
            "invalid_response",
            "payload_rejected",
            "source_rejected",
            "transport_unavailable",
            "retry_backoff",
            "buffer_full",
        }:
            raise ValueError("invalid command-result failure code")
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class SafeCommandResult:
    evidence_ref: str
    customer_id: str
    host_id: str
    project_id: str
    chat_id: str
    connector: str
    command_label: str
    started_at: datetime
    finished_at: datetime
    status: str
    error_code: str | None

    def __post_init__(self) -> None:
        if not _EVIDENCE_REF.fullmatch(self.evidence_ref):
            raise ValueError("invalid evidence reference")
        if self.customer_id != _CUSTOMER_ID or self.host_id != _HOST_ID:
            raise ValueError("command result source scope mismatch")
        if self.project_id != _PROJECT_ID or self.connector != "runner_mcp":
            raise ValueError("command result source type mismatch")
        if not isinstance(self.chat_id, str) or not re.fullmatch(
            r"mcp:[0-9a-f]{48}", self.chat_id
        ):
            raise ValueError("invalid command result chat identity")
        if not isinstance(self.command_label, str) or not _COMMAND_LABEL.fullmatch(
            self.command_label
        ):
            raise ValueError("invalid command result label")
        if self.started_at.tzinfo is None or self.finished_at.tzinfo is None:
            raise ValueError("command result timestamps must be timezone-aware")
        if self.finished_at < self.started_at:
            raise ValueError("command result time range is invalid")
        if self.status not in {"completed", "failed"}:
            raise ValueError("invalid command result status")
        if self.error_code not in {None, "command_failed"}:
            raise ValueError("invalid command result error code")
        if (self.status == "completed") != (self.error_code is None):
            raise ValueError("command result status and error code disagree")


@dataclass(frozen=True, slots=True)
class CommandResultUploadResponse:
    status: int
    body: bytes


@dataclass(frozen=True, slots=True)
class CommandResultFlushReport:
    attempted: int
    accepted: int
    pending_remaining: int
    failure_code: str | None


class CommandResultExchange(Protocol):
    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> CommandResultUploadResponse: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        del req, fp, code, msg, headers, newurl


class HttpsCommandResultExchange:
    """Fixed-route HTTPS transport using the existing Runner-MCP credential."""

    def __init__(self, config: AIfordableRelayConfig) -> None:
        if not isinstance(config, AIfordableRelayConfig):
            raise TypeError("AIfordableRelayConfig is required")
        parsed = urllib.parse.urlsplit(config.base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise CommandResultCaptureError("configuration_unavailable")
        self._url = config.base_url.rstrip("/") + _ROUTE
        self._credential = config.credential
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirect(),
        )

    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> CommandResultUploadResponse:
        if route != _ROUTE:
            raise CommandResultCaptureError("payload_rejected")
        if not isinstance(body, bytes) or not 1 <= len(body) <= _MAX_RESPONSE_BYTES:
            raise CommandResultCaptureError("payload_rejected")
        if not 0 < timeout_seconds <= _MAX_TIMEOUT_SECONDS:
            raise CommandResultCaptureError("payload_rejected")
        request = urllib.request.Request(
            self._url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-AIfordable-Runner-Credential": self._credential,
                "User-Agent": "runner-mcp-command-results",
            },
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=timeout_seconds) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
                if len(raw) > _MAX_RESPONSE_BYTES:
                    raise CommandResultCaptureError("invalid_response")
                return CommandResultUploadResponse(response.status, raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                raise CommandResultCaptureError("invalid_response") from None
            return CommandResultUploadResponse(exc.code, raw)
        except (urllib.error.URLError, TimeoutError, OSError):
            raise CommandResultCaptureError("transport_unavailable") from None


class CommandResultCapture:
    """Bounded safe queue and ACK-verified publisher for one registered source."""

    def __init__(
        self,
        config: AIfordableRelayConfig,
        *,
        exchange: CommandResultExchange | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(config, AIfordableRelayConfig):
            raise TypeError("AIfordableRelayConfig is required")
        if config.runner_subject != _EXPECTED_SUBJECT:
            raise CommandResultCaptureError("configuration_unavailable")
        self._config = config
        self._exchange = HttpsCommandResultExchange(config) if exchange is None else exchange
        self._monotonic = monotonic
        self._lock = threading.RLock()
        self._flush_lock = threading.Lock()
        self._pending: deque[SafeCommandResult] = deque()
        self._failure_count = 0
        self._retry_after = 0.0

    def capture_completed(
        self,
        *,
        chat_id: str,
        command_label: str,
        started_at: datetime,
        finished_at: datetime,
        failed: bool,
    ) -> SafeCommandResult:
        if type(failed) is not bool:
            raise TypeError("failed must be boolean")
        row = SafeCommandResult(
            evidence_ref="cmd:" + secrets.token_hex(16),
            customer_id=_CUSTOMER_ID,
            host_id=_HOST_ID,
            project_id=_PROJECT_ID,
            chat_id=chat_id,
            connector="runner_mcp",
            command_label=command_label,
            started_at=started_at,
            finished_at=finished_at,
            status="failed" if failed else "completed",
            error_code="command_failed" if failed else None,
        )
        with self._lock:
            if len(self._pending) >= _MAX_RECORDS:
                raise CommandResultCaptureError("buffer_full")
            self._pending.append(row)
        return row

    def flush_pending(self, *, limit: int = _MAX_BATCH) -> CommandResultFlushReport:
        if type(limit) is not int or not 1 <= limit <= _MAX_BATCH:
            raise ValueError("invalid command-result flush limit")
        if not self._flush_lock.acquire(blocking=False):
            return CommandResultFlushReport(0, 0, self.pending_count, "retry_backoff")
        try:
            now = self._monotonic()
            if now < self._retry_after:
                return CommandResultFlushReport(
                    0, 0, self.pending_count, "retry_backoff"
                )
            with self._lock:
                batch = tuple(list(self._pending)[:limit])
            attempted = 0
            accepted = 0
            failure_code = None
            for row in batch:
                attempted += 1
                payload = _payload(row)
                body = _json_bytes(payload)
                try:
                    response = self._exchange.post(
                        _ROUTE,
                        body,
                        timeout_seconds=_MAX_TIMEOUT_SECONDS,
                    )
                    ack = _decode_ack(response)
                    _validate_ack(ack, row, self._config, payload)
                except CommandResultCaptureError as exc:
                    failure_code = exc.code
                    break
                with self._lock:
                    self._pending = deque(
                        pending
                        for pending in self._pending
                        if pending.evidence_ref != row.evidence_ref
                    )
                accepted += 1
            if failure_code is not None:
                self._failure_count += 1
                self._retry_after = self._monotonic() + min(
                    60.0, float(2 ** min(self._failure_count - 1, 6))
                )
            else:
                self._failure_count = 0
                self._retry_after = 0.0
            return CommandResultFlushReport(
                attempted, accepted, self.pending_count, failure_code
            )
        finally:
            self._flush_lock.release()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)


class CommandResultCaptureMiddleware:
    """Capture only MCP tool name, session, timestamps and outcome status."""

    def __init__(self, capture: CommandResultCapture) -> None:
        if not isinstance(capture, CommandResultCapture):
            raise TypeError("CommandResultCapture is required")
        self._capture = capture
        self._flush_task: asyncio.Task[Any] | None = None
        self._capture_failures = 0

    async def __call__(self, ctx: Any, call_next: Callable[[Any], Any]) -> Any:
        if (
            getattr(ctx, "method", None) != "tools/call"
            or getattr(ctx, "request_id", None) is None
            or not isinstance(getattr(ctx, "params", None), Mapping)
        ):
            return await call_next(ctx)
        command_label = ctx.params.get("name")
        if (
            not isinstance(command_label, str)
            or not _COMMAND_LABEL.fullmatch(command_label)
        ):
            return await call_next(ctx)
        started_at = datetime.now(UTC)
        result: Any = None
        try:
            result = await call_next(ctx)
        finally:
            failed = (
                sys.exc_info()[0] is not None
                or _tool_result_failed(result)
            )
            try:
                self._capture.capture_completed(
                    chat_id=_session_chat_id(ctx),
                    command_label=command_label,
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    failed=failed,
                )
            except (CommandResultCaptureError, TypeError, ValueError):
                self._capture_failures += 1
            self._schedule_flush()
        return result

    def _schedule_flush(self) -> None:
        current = self._flush_task
        if current is not None and not current.done():
            return
        try:
            self._flush_task = asyncio.create_task(
                asyncio.to_thread(self._capture.flush_pending, limit=_MAX_BATCH)
            )
        except RuntimeError:
            self._capture_failures += 1
            return
        self._flush_task.add_done_callback(self._finish_flush)

    def _finish_flush(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return
        try:
            task.result()
        except (CommandResultCaptureError, OSError, RuntimeError, TypeError, ValueError):
            self._capture_failures += 1


def build_command_result_capture(
    values: Mapping[str, str],
    *,
    exchange: CommandResultExchange | None = None,
) -> CommandResultCaptureMiddleware | None:
    """Enable only for the existing, uniquely registered AIfordable lab identity."""
    try:
        config = AIfordableRelayConfig.from_mapping(values)
    except (TypeError, ValueError):
        return None
    if config.runner_subject != _EXPECTED_SUBJECT:
        return None
    try:
        return CommandResultCaptureMiddleware(
            CommandResultCapture(config, exchange=exchange)
        )
    except (CommandResultCaptureError, TypeError, ValueError):
        return None


def _session_chat_id(ctx: Any) -> str:
    request = getattr(ctx, "request", None)
    headers = getattr(request, "headers", None)
    session_id = (
        headers.get("mcp-session-id")
        if callable(getattr(headers, "get", None))
        else None
    )
    raw = (
        f"session:{session_id}"
        if isinstance(session_id, str) and session_id
        else f"request:{ctx.request_id}"
    )
    return "mcp:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:48]


def _tool_result_failed(result: Any) -> bool:
    if isinstance(result, Mapping):
        return result.get("isError") is True or result.get("is_error") is True
    return (
        getattr(result, "isError", False) is True
        or getattr(result, "is_error", False) is True
    )


def _payload(row: SafeCommandResult) -> dict[str, object]:
    return {
        "evidence_ref": row.evidence_ref,
        "customer_id": row.customer_id,
        "host_id": row.host_id,
        "project_id": row.project_id,
        "chat_id": row.chat_id,
        "connector": row.connector,
        "command_label": row.command_label,
        "started_at": row.started_at.astimezone(UTC).isoformat(),
        "finished_at": row.finished_at.astimezone(UTC).isoformat(),
        "exit_code": None,
        "status": row.status,
        "error_code": row.error_code,
        "event": "tool_result",
        "visibility": "status_only",
        "output_preview": None,
    }


def _json_bytes(payload: dict[str, object]) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise CommandResultCaptureError("invalid_record") from None


def _decode_ack(response: CommandResultUploadResponse) -> dict[str, object]:
    if not isinstance(response, CommandResultUploadResponse):
        raise CommandResultCaptureError("invalid_response")
    if response.status != 200 or not isinstance(response.body, bytes):
        raise CommandResultCaptureError("payload_rejected")
    if len(response.body) > _MAX_RESPONSE_BYTES:
        raise CommandResultCaptureError("invalid_response")
    try:
        ack = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CommandResultCaptureError("invalid_response") from None
    if not isinstance(ack, dict):
        raise CommandResultCaptureError("invalid_response")
    return ack


def _validate_ack(
    ack: dict[str, object],
    row: SafeCommandResult,
    config: AIfordableRelayConfig,
    payload: dict[str, object],
) -> None:
    if (
        ack.get("evidence_ref") != row.evidence_ref
        or ack.get("source_subject") != config.runner_subject
        or ack.get("customer_id") != _CUSTOMER_ID
        or ack.get("asset_id") != _HOST_ID
        or ack.get("service_id") != _SERVICE_ID
        or ack.get("accepted") is not True
        or type(ack.get("replayed")) is not bool
        or type(ack.get("credential_generation")) is not int
        or ack["credential_generation"] < 1
        or not isinstance(ack.get("result_digest"), str)
        or not _DIGEST.fullmatch(ack["result_digest"])
        or not isinstance(ack.get("authority_revision"), str)
        or not _AUTHORITY.fullmatch(ack["authority_revision"])
    ):
        raise CommandResultCaptureError("source_rejected")
    if ack["result_digest"] != _expected_digest(payload, ack):
        raise CommandResultCaptureError("source_rejected")


def _expected_digest(
    payload: dict[str, object],
    ack: dict[str, object],
) -> str:
    try:
        started = datetime.fromisoformat(str(payload["started_at"]))
        finished = datetime.fromisoformat(str(payload["finished_at"]))
        canonical = {
            "evidence_ref": payload["evidence_ref"],
            "customer_id": ack["customer_id"],
            "asset_id": ack["asset_id"],
            "service_id": ack["service_id"],
            "source_subject": ack["source_subject"],
            "credential_generation": ack["credential_generation"],
            "authority_revision": ack["authority_revision"],
            "project_id": payload["project_id"],
            "chat_id": payload["chat_id"],
            "connector": payload["connector"],
            "command_label": payload["command_label"],
            "started_at": started.astimezone(UTC).isoformat(),
            "finished_at": finished.astimezone(UTC).isoformat(),
            "exit_code": payload["exit_code"],
            "status": payload["status"],
            "error_code": payload["error_code"],
            "event": payload["event"],
            "visibility": payload["visibility"],
            "output_preview": payload["output_preview"],
        }
        encoded = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (KeyError, TypeError, ValueError):
        raise CommandResultCaptureError("invalid_response") from None
    return hashlib.sha256(encoded).hexdigest()
