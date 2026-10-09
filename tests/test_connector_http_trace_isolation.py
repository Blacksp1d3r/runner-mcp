"""HTTP request/response tracing isolation regressions for connector triage #590."""

from __future__ import annotations

import asyncio

from runner_mcp.http_middleware import (
    RequestIdMiddleware,
    active_traceparent,
    current_request_id,
)


def _headers(messages: list[dict]) -> dict[bytes, bytes]:
    start = next(message for message in messages if message["type"] == "http.response.start")
    return dict(start["headers"])


async def _invoke(
    app: RequestIdMiddleware,
    *,
    traceparent: str | None = None,
) -> tuple[dict[bytes, bytes], str | None, str]:
    incoming = [] if traceparent is None else [(b"traceparent", traceparent.encode("ascii"))]
    scope = {"type": "http", "method": "GET", "path": "/mcp", "headers": incoming}
    sent: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        sent.append(message)

    await app(scope, receive, send)
    return _headers(sent), active_traceparent(), current_request_id()


def test_response_trace_isolated_for_concurrent_requests() -> None:
    observed: list[tuple[str, str | None]] = []

    async def endpoint(scope: dict, receive: object, send: object) -> None:
        rid = current_request_id()
        trace = active_traceparent()
        await asyncio.sleep(0)
        assert current_request_id() == rid
        assert active_traceparent() == trace
        observed.append((rid, trace))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    app = RequestIdMiddleware(endpoint)

    async def run() -> list[tuple[dict[bytes, bytes], str | None, str]]:
        return await asyncio.gather(*(_invoke(app) for _ in range(8)))

    results = asyncio.run(run())
    request_ids = [headers[b"x-request-id"].decode("ascii") for headers, _, _ in results]
    trace_ids = [headers[b"traceparent"].decode("ascii").split("-")[1] for headers, _, _ in results]
    assert len(set(request_ids)) == len(results)
    assert len(set(trace_ids)) == len(results)
    assert set(request_ids) == {request_id for request_id, _ in observed}
    assert all(trace is not None for _, trace in observed)
    assert all(parent is None for _, parent, _ in results)


def test_client_trace_id_retained_without_reusing_parent_span() -> None:
    incoming = "00-" + "a" * 32 + "-" + "b" * 16 + "-01"

    async def endpoint(scope: dict, receive: object, send: object) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    headers, _, _ = asyncio.run(_invoke(RequestIdMiddleware(endpoint), traceparent=incoming))
    returned = headers[b"traceparent"].decode("ascii")
    assert returned.split("-")[1] == "a" * 32
    assert returned.split("-")[2] != "b" * 16
    assert returned.endswith("-01")


def test_malformed_client_trace_is_not_authoritative() -> None:
    async def endpoint(scope: dict, receive: object, send: object) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    invalid = "00-" + "0" * 32 + "-" + "b" * 16 + "-01"
    headers, _, _ = asyncio.run(_invoke(RequestIdMiddleware(endpoint), traceparent=invalid))
    returned = headers[b"traceparent"].decode("ascii")
    assert returned.split("-")[1] != "0" * 32
    assert headers[b"x-request-id"]
