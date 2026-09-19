from __future__ import annotations

import asyncio
from collections import deque
from contextvars import ContextVar
from time import monotonic
from typing import Any
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_request_id: ContextVar[str | None] = ContextVar("runner_mcp_request_id", default=None)


def current_request_id() -> str:
    value = _request_id.get()
    return value if value is not None else str(uuid4())


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        token = _request_id.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _request_id.reset(token)


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
