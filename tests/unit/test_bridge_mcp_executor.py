import json
import urllib.error
import urllib.request

import pytest

from runner_mcp.bridge_mcp_executor import (
    MAX_MCP_RESPONSE_BYTES,
    LocalMCPBridgeExecutor,
    LocalMCPClient,
    LocalMCPConfig,
    _decode_mcp_response,
)
from runner_mcp.bridge_processor import BridgeExecutionAdapterError


class FakeResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._payload


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def _call_tool(self, name: str, arguments: dict):
        self.calls.append((name, arguments))
        if not self.responses:
            raise AssertionError("unexpected tool call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _config(**overrides) -> LocalMCPConfig:
    values = {
        "endpoint": "http://127.0.0.1:8000/mcp",
        "bearer_token": "safe-token",
    }
    values.update(overrides)
    return LocalMCPConfig(**values)


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "ftp://127.0.0.1/mcp",
        "http://example.com/mcp",
        "http://10.0.0.1/mcp",
        "http://user:pass@127.0.0.1/mcp",
        "http://127.0.0.1/other",
        "http://127.0.0.1/mcp?x=1",
        "http://127.0.0.1/mcp#frag",
        "http://127.0.0.1:99999/mcp",
    ],
)
def test_local_mcp_config_rejects_unsafe_endpoint(endpoint: str) -> None:
    with pytest.raises(ValueError, match="MCP endpoint"):
        _config(endpoint=endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1/mcp",
        "https://127.0.0.1:8443/mcp",
        "http://localhost:8000/mcp/",
        "http://[::1]:8000/mcp",
    ],
)
def test_local_mcp_config_accepts_loopback_endpoint(endpoint: str) -> None:
    config = _config(endpoint=endpoint)
    assert config.endpoint == endpoint


@pytest.mark.parametrize(
    "token",
    [
        "",
        "has space",
        "line\nbreak",
        "tökén",
    ],
)
def test_local_mcp_config_rejects_unsafe_token(token: str) -> None:
    with pytest.raises(ValueError, match="bearer token"):
        _config(bearer_token=token)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_timeout_seconds", 0),
        ("request_timeout_seconds", 121),
        ("test_wait_timeout_seconds", 4),
        ("test_wait_timeout_seconds", 3901),
        ("test_poll_interval_seconds", 0),
        ("test_poll_interval_seconds", 5.1),
    ],
)
def test_local_mcp_config_bounds_timing(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        _config(**{field: value})


@pytest.mark.parametrize(
    "payload",
    [
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'[]',
        b'not-json',
        b'\xff',
        (
            b'data: {"jsonrpc":"2.0"}\n\n'
            b'data: {"jsonrpc":"2.0"}\n\n'
        ),
    ],
)
def test_decode_mcp_response_rejects_unsafe_content(payload: bytes) -> None:
    with pytest.raises(BridgeExecutionAdapterError):
        _decode_mcp_response(payload)


def test_decode_mcp_response_accepts_json_and_single_sse_event() -> None:
    assert _decode_mcp_response(b'{"jsonrpc":"2.0","id":1}') == {
        "jsonrpc": "2.0",
        "id": 1,
    }
    assert _decode_mcp_response(
        b'event: message\ndata: {"jsonrpc":"2.0","id":1}\n\n'
    ) == {"jsonrpc": "2.0", "id": 1}


def test_decode_mcp_response_accepts_empty_body() -> None:
    assert _decode_mcp_response(b"") is None
    assert _decode_mcp_response(b"  \n") is None


def test_decode_mcp_response_is_size_bounded() -> None:
    with pytest.raises(BridgeExecutionAdapterError, match="size limit"):
        _decode_mcp_response(b"x" * (MAX_MCP_RESPONSE_BYTES + 1))


def test_client_initializes_session_and_sends_authenticated_tool_call(
    monkeypatch,
) -> None:
    captured: list[dict] = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps([{"code": "demo"}]),
                            }
                        ]
                    },
                }
            ).encode()
        ),
    ]

    def fake_urlopen(request, *, timeout):
        captured.append(
            {
                "url": request.full_url,
                "auth": request.get_header("Authorization"),
                "session": request.get_header("Mcp-session-id"),
                "body": json.loads(request.data),
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = LocalMCPClient(_config())

    result = client._call_tool("list_projects", {})

    assert result == [{"code": "demo"}]
    assert [item["body"]["method"] for item in captured] == [
        "initialize",
        "notifications/initialized",
        "tools/call",
    ]
    assert captured[0]["auth"] == "Bearer safe-token"
    assert captured[0]["session"] is None
    assert captured[1]["session"] == "session-123"
    assert captured[2]["session"] == "session-123"
    assert captured[2]["body"]["params"] == {
        "name": "list_projects",
        "arguments": {},
    }


def test_client_initialize_is_idempotent(monkeypatch) -> None:
    calls = 0
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
    ]

    def fake_urlopen(request, *, timeout):
        nonlocal calls
        calls += 1
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = LocalMCPClient(_config())

    client.initialize()
    client.initialize()

    assert calls == 2


def test_client_rejects_invalid_session_identifier(monkeypatch) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "bad session"},
        ),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="session"):
        client.initialize()


def test_client_rejects_server_jsonrpc_error(monkeypatch) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            b'{"jsonrpc":"2.0","id":2,"error":{"code":-32000,"message":"private"}}'
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="rejected"):
        client._call_tool("list_projects", {})


def test_client_rejects_tool_error_without_leaking_text(monkeypatch) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            b'{"jsonrpc":"2.0","id":2,"result":{"isError":true,'
            b'"content":[{"type":"text","text":"private /srv/value"}]}}'
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError) as caught:
        client._call_tool("list_projects", {})

    assert "private /srv/value" not in str(caught.value)


@pytest.mark.parametrize(
    "content",
    [
        {"content": "not-a-list"},
        {"content": [{"type": "text", "text": "{}"}, {"type": "text", "text": "{}"}]},
        {"content": [{"type": "image", "data": "..."}]},
        {"content": [{"type": "text", "text": '{"a":1,"a":2}'}]},
        {"content": [{"type": "text", "text": "NaN"}]},
    ],
)
def test_client_rejects_unsupported_tool_content(monkeypatch, content: dict) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": content}).encode()
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError):
        client._call_tool("list_projects", {})


def test_client_rejects_unsupported_internal_tool_name() -> None:
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="unsupported tool"):
        client._call_tool("deploy_staging", {})


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.URLError("offline"),
        urllib.error.HTTPError(
            "http://127.0.0.1/mcp",
            401,
            "unauthorized",
            None,
            None,
        ),
        TimeoutError(),
    ],
)
def test_client_normalizes_transport_failures(monkeypatch, error) -> None:
    def fail(request, timeout):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError) as caught:
        client.initialize()

    assert "offline" not in str(caught.value)
    assert "unauthorized" not in str(caught.value)


def test_executor_exposes_only_fixed_bridge_calls() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    fake = FakeClient(
        [
            ["p1"],
            {"stop_active": False},
            {"project": "demo"},
            {"adapter": "python"},
            [{"name": "unit"}],
        ]
    )
    executor._client = fake

    assert executor.list_projects() == ["p1"]
    assert executor.safety_status() == {"stop_active": False}
    assert executor.project_status("demo") == {"project": "demo"}
    assert executor.project_capabilities("demo") == {"adapter": "python"}
    assert executor.list_test_profiles("demo") == [{"name": "unit"}]

    assert fake.calls == [
        ("list_projects", {}),
        ("safety_status", {}),
        ("project_status", {"project": "demo"}),
        ("project_capabilities", {"project": "demo"}),
        ("list_test_profiles", {"project": "demo"}),
    ]


def test_run_tests_polls_to_terminal_without_fetching_log(monkeypatch) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    fake = FakeClient(
        [
            {"job_id": "job-123"},
            {"status": "queued"},
            {"status": "running"},
            {"status": "passed"},
        ]
    )
    executor._client = fake
    sleeps: list[float] = []
    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.time.sleep",
        sleeps.append,
    )

    result = executor.run_tests_to_completion("demo", "unit")

    assert result == {
        "project": "demo",
        "suite": "unit",
        "status": "passed",
    }
    assert fake.calls == [
        ("run_tests", {"project": "demo", "suite": "unit"}),
        ("test_status", {"job_id": "job-123"}),
        ("test_status", {"job_id": "job-123"}),
        ("test_status", {"job_id": "job-123"}),
    ]
    assert all(name != "get_test_log" for name, _args in fake.calls)
    assert sleeps == [0.5, 0.5]


@pytest.mark.parametrize(
    "terminal",
    ["failed", "timed_out", "stopped", "cancelled", "interrupted"],
)
def test_run_tests_returns_all_terminal_states(monkeypatch, terminal: str) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    executor._client = FakeClient(
        [
            {"job_id": "job-123"},
            {"status": terminal},
        ]
    )
    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.time.sleep",
        lambda _seconds: None,
    )

    assert executor.run_tests_to_completion("demo", "unit")["status"] == terminal


@pytest.mark.parametrize(
    "started",
    [
        None,
        {},
        {"job_id": ""},
        {"job_id": "bad id"},
        {"job_id": 123},
    ],
)
def test_run_tests_rejects_invalid_job_identifier(started) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    executor._client = FakeClient([started])

    with pytest.raises(BridgeExecutionAdapterError, match="job identifier|start result"):
        executor.run_tests_to_completion("demo", "unit")


@pytest.mark.parametrize(
    "status_payload",
    [
        None,
        {},
        {"status": 1},
        {"status": "unknown"},
    ],
)
def test_run_tests_rejects_invalid_status(status_payload) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    executor._client = FakeClient(
        [
            {"job_id": "job-123"},
            status_payload,
        ]
    )

    with pytest.raises(BridgeExecutionAdapterError, match="test status"):
        executor.run_tests_to_completion("demo", "unit")


def test_run_tests_wait_timeout_is_bounded(monkeypatch) -> None:
    executor = LocalMCPBridgeExecutor(
        _config(test_wait_timeout_seconds=5)
    )
    executor._client = FakeClient(
        [
            {"job_id": "job-123"},
            {"status": "running"},
        ]
    )
    times = iter([10.0, 16.0])
    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.time.monotonic",
        lambda: next(times),
    )

    with pytest.raises(BridgeExecutionAdapterError, match="timeout expired"):
        executor.run_tests_to_completion("demo", "unit")
