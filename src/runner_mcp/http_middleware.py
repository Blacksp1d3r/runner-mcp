from __future__ import annotations

import asyncio
import re
import secrets
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass
from time import monotonic
from typing import Any
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_TRACEPARENT_RE = re.compile(
    r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-([0-9a-fA-F]{2})$"
)


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    parent_id: str
    trace_flags: str = "00"

    def __post_init__(self) -> None:
        trace_id = self.trace_id.lower()
        parent_id = self.parent_id.lower()
        trace_flags = self.trace_flags.lower()
        if (
            len(trace_id) != 32
            or any(char not in "0123456789abcdef" for char in trace_id)
            or trace_id == "0" * 32
        ):
            raise ValueError("trace_id is invalid")
        if (
            len(parent_id) != 16
            or any(char not in "0123456789abcdef" for char in parent_id)
            or parent_id == "0" * 16
        ):
            raise ValueError("parent_id is invalid")
        if (
            len(trace_flags) != 2
            or any(char not in "0123456789abcdef" for char in trace_flags)
        ):
            raise ValueError("trace_flags are invalid")
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "parent_id", parent_id)
        object.__setattr__(self, "trace_flags", trace_flags)

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.parent_id}-{self.trace_flags}"


_request_id: ContextVar[str | None] = ContextVar("runner_mcp_request_id", default=None)
_trace_context: ContextVar[TraceContext | None] = ContextVar(
    "runner_mcp_trace_context",
    default=None,
)


def current_request_id() -> str:
    value = _request_id.get()
    return value if value is not None else str(uuid4())


def current_trace_id() -> str:
    context = _trace_context.get()
    return context.trace_id if context is not None else _new_trace_id()


def current_traceparent() -> str:
    context = _trace_context.get()
    return context.traceparent if context is not None else _new_trace_context().traceparent


def active_traceparent() -> str | None:
    """Return only a trace context actually bound to the current HTTP request."""

    context = _trace_context.get()
    return None if context is None else context.traceparent


def parse_traceparent(value: str | None) -> TraceContext | None:
    """Parse the bounded W3C traceparent v00 form; malformed input is non-authoritative."""

    if not isinstance(value, str) or len(value) != 55:
        return None
    matched = _TRACEPARENT_RE.fullmatch(value)
    if matched is None:
        return None
    try:
        return TraceContext(
            trace_id=matched.group(1),
            parent_id=matched.group(2),
            trace_flags=matched.group(3),
        )
    except ValueError:
        return None


def _new_trace_id() -> str:
    while True:
        value = secrets.token_hex(16)
        if value != "0" * 32:
            return value


def _new_parent_id() -> str:
    while True:
        value = secrets.token_hex(8)
        if value != "0" * 16:
            return value


def _new_trace_context(parent: TraceContext | None = None) -> TraceContext:
    return TraceContext(
        trace_id=parent.trace_id if parent is not None else _new_trace_id(),
        parent_id=_new_parent_id(),
        trace_flags=parent.trace_flags if parent is not None else "00",
    )


def _incoming_traceparent(scope: Scope) -> str | None:
    values: list[str] = []
    for key, value in scope.get("headers", []):
        if key.lower() != b"traceparent":
            continue
        try:
            values.append(value.decode("ascii"))
        except UnicodeDecodeError:
            return None
    if len(values) != 1:
        return None
    return values[0]


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        request_token = _request_id.set(request_id)
        parent = parse_traceparent(_incoming_traceparent(scope))
        trace_context = _new_trace_context(parent)
        trace_token = _trace_context.set(trace_context)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["traceparent"] = trace_context.traceparent
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _trace_context.reset(trace_token)
            _request_id.reset(request_token)


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        max_requests: int,
        window_seconds: float = 60.0,
        max_clients: int = 1024,
        exempt_paths: set[str] | None = None,
    ) -> None:
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self.exempt_paths = exempt_paths or {"/healthz"}
        self._events: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _client_key(scope: Scope) -> str:
        client: Any = scope.get("client")
        if isinstance(client, tuple) and client:
            return str(client[0])
        return "unknown"

    async def _allow(self, key: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self.max_clients:
                    stale = [
                        item_key
                        for item_key, item_events in self._events.items()
                        if not item_events or item_events[-1] < cutoff
                    ]
                    for item_key in stale:
                        self._events.pop(item_key, None)
                if len(self._events) >= self.max_clients:
                    return False
                events = deque()
                self._events[key] = events

            while events and events[0] < cutoff:
                events.popleft()

            if len(events) >= self.max_requests:
                return False

            events.append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        if not await self._allow(self._client_key(scope)):
            response = JSONResponse(
                {"error": "rate_limit_exceeded"},
                status_code=429,
                headers={"Retry-After": str(max(1, int(self.window_seconds)))},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
