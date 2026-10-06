import json
import logging
import threading
import urllib.error
import urllib.request

import pytest
from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS

from runner_mcp.bridge_mcp_executor import (
    _MCP_POLICY_PROTOCOL_VERSIONS,
    MAX_MCP_RESPONSE_BYTES,
    LocalMCPBridgeExecutor,
    LocalMCPClient,
    LocalMCPConfig,
    _decode_mcp_response,
    _validate_initialize_peer,
    _validate_peer_tool_surface,
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
        "http://example.invalid/mcp",
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


def test_mcp_policy_versions_are_real_sdk_handshake_versions() -> None:
    assert _MCP_POLICY_PROTOCOL_VERSIONS == {
        "2025-06-18",
        "2025-03-26",
    }
    assert _MCP_POLICY_PROTOCOL_VERSIONS <= set(
        HANDSHAKE_PROTOCOL_VERSIONS
    )


def test_initialize_peer_accepts_forward_compatible_server_metadata() -> None:
    assert _validate_initialize_peer(
        {
            "protocolVersion": "2025-06-18",
            "serverInfo": {
                "name": "Runner Fabric Agent",
                "version": "1.0",
                "title": "Runner Fabric Agent",
                "websiteUrl": "https://example.invalid",
            },
        }
    ) == {
        "protocol_version": "2025-06-18",
        "server_name": "Runner Fabric Agent",
        "server_version": "1.0",
    }


@pytest.mark.parametrize(
    ("server_info", "expected_name", "expected_version"),
    [
        ({"version": "1.0", "title": "missing-name"}, None, "1.0"),
        ({"name": "Runner Fabric Agent", "title": "missing-version"}, "Runner Fabric Agent", None),
        ({"name": "Runner Fabric Agent", "version": ""}, "Runner Fabric Agent", None),
        ({}, None, None),
    ],
)
def test_initialize_peer_accepts_optional_advisory_server_identity_fields(
    server_info,
    expected_name,
    expected_version,
) -> None:
    result = _validate_initialize_peer(
        {
            "protocolVersion": "2025-06-18",
            "serverInfo": server_info,
        }
    )
    assert result["server_name"] == expected_name
    assert result["server_version"] == expected_version


@pytest.mark.parametrize(
    "server_info",
    [
        {"name": "", "version": "1.0"},
        {"name": 123, "version": "1.0"},
        {"name": "Runner Fabric Agent", "version": []},
    ],
)
def test_initialize_peer_rejects_invalid_present_server_identity_fields(
    server_info,
) -> None:
    with pytest.raises(BridgeExecutionAdapterError, match="server identity"):
        _validate_initialize_peer(
            {
                "protocolVersion": "2025-06-18",
                "serverInfo": server_info,
            }
        )


def test_client_rejects_required_tools_outside_allowlist() -> None:
    with pytest.raises(ValueError, match="required MCP tools"):
        LocalMCPClient(
            _config(),
            allowed_tools=frozenset({"one"}),
            required_tools=frozenset({"two"}),
        )


def test_client_records_bounded_peer_handshake_identity(monkeypatch) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","serverInfo":{"name":"Runner MCP","version":"0.1.3"}}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    client.initialize()

    assert client.peer_identity == {
        "protocol_version": "2025-06-18",
        "server_name": "Runner MCP",
        "server_version": "0.1.3",
    }


@pytest.mark.parametrize(
    "protocol_version",
    ["2025-06-18", "2025-03-26"],
)
def test_client_preflights_required_surface_and_build_identity(
    monkeypatch,
    caplog,
    protocol_version: str,
) -> None:
    tools = [
        {
            "name": "build_identity",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "list_projects",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    ]
    digest, names = _validate_peer_tool_surface(
        {"result": {"tools": tools}},
        required_tools=frozenset({"list_projects"}),
    )
    identity = {
        "component_id": "runner-mcp",
        "build_version": "0.1.3",
        "source_revision": None,
        "artifact_digest": None,
        "protocol_min": "2025-03-26",
        "protocol_max": "2025-06-18",
        "interface_schema_digest": digest,
    }
    responses = [
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": protocol_version,
                        "serverInfo": {
                            "name": "Runner MCP",
                            "version": "0.1.3",
                        },
                    },
                }
            ).encode(),
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": tools},
                }
            ).encode()
        ),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "isError": False,
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(identity),
                            }
                        ],
                    },
                }
            ).encode()
        ),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps([{"code": "demo"}]),
                            }
                        ],
                    },
                }
            ).encode()
        ),
    ]
    captured = []

    def respond(request, timeout):
        del timeout
        captured.append(json.loads(request.data))
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", respond)
    client = LocalMCPClient(
        _config(),
        allowed_tools=frozenset({"list_projects"}),
        compatibility_preflight=True,
    )

    with caplog.at_level(logging.INFO, logger="runner_mcp.peer_identity"):
        assert client._call_tool("list_projects", {}) == [{"code": "demo"}]
    assert client.peer_build_identity == identity
    assert client.peer_tool_names == tuple(sorted(names))
    assert [item["method"] for item in captured] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call",
        "tools/call",
    ]
    assert captured[3]["params"] == {
        "name": "build_identity",
        "arguments": {},
    }
    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "runner_mcp.peer_identity"
    ]
    assert len(records) == 1
    peer = records[0]
    assert peer["event"] == "runner_mcp_peer_observed"
    assert peer["initialize_protocol_version"] == protocol_version
    assert peer["server_name"] == "Runner MCP"
    assert peer["server_version"] == "0.1.3"
    assert peer["peer_component_id"] == "runner-mcp"
    assert peer["peer_protocol_min"] == "2025-03-26"
    assert peer["peer_protocol_max"] == "2025-06-18"
    assert peer["peer_interface_schema_digest"] == digest
    rendered = json.dumps(peer)
    assert "safe-token" not in rendered
    assert "127.0.0.1" not in rendered


def test_client_preflight_rejects_missing_required_tool(monkeypatch) -> None:
    tools = [
        {
            "name": "build_identity",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    ]
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
                    "result": {"tools": tools},
                }
            ).encode()
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(
        _config(),
        allowed_tools=frozenset({"list_projects"}),
        compatibility_preflight=True,
    )

    with pytest.raises(
        BridgeExecutionAdapterError,
        match="interface schema",
    ):
        client.initialize()


def test_client_preflight_rejects_peer_digest_mismatch(monkeypatch) -> None:
    tools = [
        {
            "name": "build_identity",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "list_projects",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    ]
    identity = {
        "component_id": "runner-mcp",
        "build_version": "0.1.3",
        "source_revision": None,
        "artifact_digest": None,
        "protocol_min": "2025-03-26",
        "protocol_max": "2025-06-18",
        "interface_schema_digest": "f" * 64,
    }
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
                    "result": {"tools": tools},
                }
            ).encode()
        ),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "isError": False,
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(identity),
                            }
                        ],
                    },
                }
            ).encode()
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(
        _config(),
        allowed_tools=frozenset({"list_projects"}),
        compatibility_preflight=True,
    )

    with pytest.raises(
        BridgeExecutionAdapterError,
        match="interface schema",
    ):
        client.initialize()


def test_client_sends_negotiated_protocol_header(monkeypatch) -> None:
    captured: list[str | None] = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26"}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
    ]

    def respond(request, timeout):
        del timeout
        captured.append(request.get_header("Mcp-protocol-version"))
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", respond)
    LocalMCPClient(_config()).initialize()

    assert captured == [None, "2025-03-26"]


def test_client_rejects_observed_protocol_version_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="protocol version"):
        client.initialize()


@pytest.mark.parametrize(
    "server_info",
    [
        {"name": "../private", "version": "1"},
        {"name": "Runner MCP", "version": "x" * 129},
        {"name": "Runner MCP", "version": "bad\nversion"},
    ],
)
def test_client_rejects_invalid_observed_server_identity(
    monkeypatch,
    server_info: dict,
) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2025-06-18",
            "serverInfo": server_info,
        },
    }
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(
            json.dumps(payload).encode(),
            headers={"Mcp-Session-Id": "session-123"},
        ),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="server identity"):
        client.initialize()


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


def test_client_propagates_only_bound_traceparent(monkeypatch) -> None:
    traceparent = (
        "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
    )
    captured: list[str | None] = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
        FakeResponse(
            b'{"jsonrpc":"2.0","id":2,"result":{"content":[]}}'
        ),
    ]

    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.active_traceparent",
        lambda: traceparent,
    )

    def fake_urlopen(request, *, timeout):
        del timeout
        captured.append(request.get_header("Traceparent"))
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = LocalMCPClient(_config())

    assert client._call_tool("runtime_status", {}) is None
    assert captured == [traceparent, traceparent, traceparent]


def test_client_omits_traceparent_without_bound_request(monkeypatch) -> None:
    captured: list[str | None] = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-123"},
        ),
        FakeResponse(b""),
    ]

    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.active_traceparent",
        lambda: None,
    )

    def fake_urlopen(request, *, timeout):
        del timeout
        captured.append(request.get_header("Traceparent"))
        return responses.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    LocalMCPClient(_config()).initialize()

    assert captured == [None, None]


def test_client_accepts_multi_item_list_tool_content(monkeypatch) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
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
                            {"type": "text", "text": '{"name":"privacy"}'},
                            {"type": "text", "text": '{"name":"unit"}'},
                        ]
                    },
                }
            ).encode()
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    assert client._call_tool("list_test_profiles", {"project": "demo"}) == [
        {"name": "privacy"},
        {"name": "unit"},
    ]


def test_client_rejects_multi_item_non_list_tool_content(monkeypatch) -> None:
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
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
                            {"type": "text", "text": '{"status":"one"}'},
                            {"type": "text", "text": '{"status":"two"}'},
                        ]
                    },
                }
            ).encode()
        ),
    ]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: responses.pop(0),
    )
    client = LocalMCPClient(_config())

    with pytest.raises(BridgeExecutionAdapterError):
        client._call_tool("project_status", {"project": "demo"})


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
            b'"content":[{"type":"text","text":"private detail"}]}}'
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

    assert "private detail" not in str(caught.value)


@pytest.mark.parametrize(
    "content",
    [
        {"content": "not-a-list"},
        {
            "content": [
                {"type": "text", "text": "[]"},
                {"type": "text", "text": "{}"},
            ]
        },
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
        client._call_tool("arbitrary_shell", {})


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
    job_id = "a" * 32
    fake = FakeClient(
        [
            ["p1"],
            {"stop_active": False},
            {"project": "demo"},
            {"adapter": "python"},
            [{"name": "unit"}],
            {"queued_jobs": 0},
            {"available_workers": 4},
            {"job_id": job_id, "status": "running"},
            {"job_id": job_id, "status": "cancelled"},
        ]
    )
    executor._local.client = fake

    assert executor.list_projects() == ["p1"]
    assert executor.safety_status() == {"stop_active": False}
    assert executor.project_status("demo") == {"project": "demo"}
    assert executor.project_capabilities("demo") == {"adapter": "python"}
    assert executor.list_test_profiles("demo") == [{"name": "unit"}]
    assert executor.queue_status() == {"queued_jobs": 0}
    assert executor.worker_status() == {"available_workers": 4}
    assert executor.job_status(job_id)["status"] == "running"
    assert executor.cancel_job(job_id)["status"] == "cancelled"

    assert fake.calls == [
        ("list_projects", {}),
        ("safety_status", {}),
        ("project_status", {"project": "demo"}),
        ("project_capabilities", {"project": "demo"}),
        ("list_test_profiles", {"project": "demo"}),
        ("queue_status", {}),
        ("worker_status", {}),
        ("job_status", {"job_id": job_id}),
        ("cancel_job", {"job_id": job_id}),
    ]


def test_executor_exposes_bounded_operational_calls() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    test_job = "a" * 32
    approval_id = "b" * 32
    migration_job = "f" * 32
    deploy_job = "c" * 32
    rollback_job = "d" * 32
    migration_queued = {
        "job_id": migration_job,
        "project": "demo",
        "operation": "migration",
        "state": "queued",
        "created_at": "2026-09-28T20:00:00+00:00",
        "started_at": None,
        "finished_at": None,
        "migration_state": None,
        "error_category": None,
        "pre_migration_backup_created": False,
        "output_truncated": False,
    }
    migration_running = {
        **migration_queued,
        "state": "running",
        "started_at": "2026-09-28T20:00:01+00:00",
    }
    fake = FakeClient(
        [
            {"content": "safe"},
            [{"service": "web"}],
            {"service": "web", "active": True},
            {"service": "web", "status": "started"},
            {"service": "web", "status": "stopped"},
            {"service": "web", "status": "restarted"},
            [{"backup_id": "one"}],
            {"status": "completed"},
            {"approval_id": approval_id, "state": "pending"},
            {"approval_id": approval_id, "state": "approved"},
            {"status": "clean"},
            {"status": "completed"},
            migration_queued,
            migration_running,
            {"commit": "e" * 40},
            {"job_id": deploy_job, "state": "queued"},
            {"job_id": deploy_job, "state": "running"},
            [{"release_id": "one"}],
            {"eligible": True},
            {"job_id": rollback_job, "state": "queued"},
            {"job_id": rollback_job, "state": "completed"},
        ]
    )
    executor._local.client = fake

    assert executor.job_log(test_job, offset=2, length=10)["content"] == "safe"
    assert executor.list_services("demo")[0]["service"] == "web"
    assert executor.service_status("demo", "web")["active"] is True
    assert executor.start_service("demo", "web")["status"] == "started"
    assert executor.stop_service("demo", "web")["status"] == "stopped"
    assert executor.restart_service("demo", "web")["status"] == "restarted"
    assert executor.list_backups("demo", limit=5)[0]["backup_id"] == "one"
    assert executor.backup_database("demo")["status"] == "completed"
    assert (
        executor.request_action_approval("demo", "deploy")["approval_id"]
        == approval_id
    )
    assert executor.approval_status(approval_id)["state"] == "approved"
    assert executor.migration_status("demo")["status"] == "clean"
    assert executor.apply_migrations("demo", approval_id)["status"] == "completed"
    assert (
        executor.start_migration_job("demo", approval_id)["job_id"]
        == migration_job
    )
    assert executor.migration_job_status(migration_job)["state"] == "running"
    assert executor.plan_deploy("demo")["commit"] == "e" * 40
    assert executor.deploy_staging("demo", approval_id)["job_id"] == deploy_job
    assert executor.deployment_status(deploy_job)["state"] == "running"
    assert executor.list_releases("demo", limit=7)[0]["release_id"] == "one"
    assert executor.rollback_plan("demo")["eligible"] is True
    assert executor.rollback_release("demo", approval_id)["job_id"] == rollback_job
    assert executor.rollback_status(rollback_job)["state"] == "completed"

    assert fake.calls == [
        ("get_test_log", {"job_id": test_job, "offset": 2, "length": 10}),
        ("list_services", {"project": "demo"}),
        ("service_status", {"project": "demo", "service": "web"}),
        ("start_service", {"project": "demo", "service": "web"}),
        ("stop_service", {"project": "demo", "service": "web"}),
        ("restart_service", {"project": "demo", "service": "web"}),
        ("list_backups", {"project": "demo", "limit": 5}),
        ("backup_database", {"project": "demo"}),
        (
            "request_action_approval",
            {"project": "demo", "action": "deploy"},
        ),
        ("approval_status", {"approval_id": approval_id}),
        ("migration_status", {"project": "demo"}),
        (
            "apply_migrations",
            {"project": "demo", "approval_id": approval_id},
        ),
        (
            "start_migration_job",
            {"project": "demo", "approval_id": approval_id},
        ),
        ("migration_job_status", {"job_id": migration_job}),
        ("plan_deploy", {"project": "demo"}),
        (
            "deploy_staging",
            {"project": "demo", "approval_id": approval_id},
        ),
        ("deployment_status", {"job_id": deploy_job}),
        ("list_releases", {"project": "demo", "limit": 7}),
        ("rollback_plan", {"project": "demo"}),
        (
            "rollback_release",
            {"project": "demo", "approval_id": approval_id},
        ),
        ("rollback_status", {"job_id": rollback_job}),
    ]


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("job_log", ("a" * 32, -1, 10)),
        ("job_log", ("a" * 32, 0, 101)),
        ("list_backups", ("demo", 101)),
        ("list_releases", ("demo", 0)),
        ("request_action_approval", ("demo", "shell")),
        ("approval_status", ("bad-id",)),
        ("migration_job_status", ("bad-id",)),
    ],
)
def test_executor_rejects_unbounded_operational_arguments(
    method: str,
    args: tuple,
) -> None:
    executor = LocalMCPBridgeExecutor(_config())

    with pytest.raises(BridgeExecutionAdapterError):
        if method == "job_log":
            executor.job_log(args[0], offset=args[1], length=args[2])
        elif method == "list_backups":
            executor.list_backups(args[0], limit=args[1])
        elif method == "list_releases":
            executor.list_releases(args[0], limit=args[1])
        elif method == "request_action_approval":
            executor.request_action_approval(args[0], args[1])
        elif method == "migration_job_status":
            executor.migration_job_status(args[0])
        else:
            executor.approval_status(args[0])


def test_executor_exposes_fixed_self_operations() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    update_job = "a" * 32
    commit = "b" * 40
    fake = FakeClient(
        [
            {
                "version": "0.1.0",
                "self_update_ready": True,
                "active_update": False,
            },
            {
                "job_id": update_job,
                "commit": commit,
                "state": "queued",
            },
            {
                "job_id": update_job,
                "commit": commit,
                "state": "testing",
            },
        ]
    )
    executor._local.client = fake

    assert executor.runtime_status()["self_update_ready"] is True
    assert executor.self_update(commit)["job_id"] == update_job
    assert executor.self_update_status(update_job)["state"] == "testing"
    assert fake.calls == [
        ("runtime_status", {}),
        ("self_update", {"commit": commit}),
        ("self_update_status", {"job_id": update_job}),
    ]


@pytest.mark.parametrize(
    ("method", "value"),
    [
        ("self_update", "main"),
        ("self_update", "A" * 40),
        ("self_update_status", "bad-id"),
    ],
)
def test_executor_rejects_invalid_self_operation_identifiers(
    method: str,
    value: str,
) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    with pytest.raises(BridgeExecutionAdapterError):
        getattr(executor, method)(value)




def test_executor_exposes_fixed_fabric_bootstrap_operations() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    job_id = "c" * 32
    commit = "d" * 40
    fake = FakeClient(
        [
            {"job_id": job_id, "commit": commit, "state": "queued"},
            {"job_id": job_id, "commit": commit, "state": "running"},
        ]
    )
    executor._local.client = fake

    assert executor.fabric_bootstrap(commit)["job_id"] == job_id
    assert executor.fabric_bootstrap_status(job_id)["state"] == "running"
    assert fake.calls == [
        ("fabric_bootstrap", {"commit": commit}),
        ("fabric_bootstrap_status", {"job_id": job_id}),
    ]


@pytest.mark.parametrize(
    ("method", "value"),
    [
        ("fabric_bootstrap", "main"),
        ("fabric_bootstrap", "D" * 40),
        ("fabric_bootstrap_status", "bad-id"),
    ],
)
def test_executor_rejects_invalid_fabric_bootstrap_identifiers(
    method: str,
    value: str,
) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    with pytest.raises(BridgeExecutionAdapterError):
        getattr(executor, method)(value)


def test_run_tests_returns_job_immediately_without_polling() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    job_id = "b" * 32
    executor._local.client = FakeClient(
        [{"job_id": job_id, "project": "demo", "suite": "unit", "status": "queued"}]
    )

    result = executor.run_tests("demo", "unit")

    assert result["job_id"] == job_id
    assert result["status"] == "queued"
    assert executor._local.client.calls == [
        ("run_tests", {"project": "demo", "suite": "unit"})
    ]


@pytest.mark.parametrize(
    "started",
    [
        None,
        {},
        {"job_id": ""},
        {"job_id": "bad id", "status": "queued"},
        {"job_id": 123, "status": "queued"},
        {"job_id": "a" * 32, "status": "passed"},
    ],
)
def test_run_tests_rejects_invalid_initial_job_result(started) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    executor._local.client = FakeClient([started])

    with pytest.raises(
        BridgeExecutionAdapterError,
        match="job identifier|start result|initial test status",
    ):
        executor.run_tests("demo", "unit")


def test_job_actions_reject_invalid_job_identifier() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    with pytest.raises(BridgeExecutionAdapterError, match="job identifier"):
        executor.job_status("../bad")
    with pytest.raises(BridgeExecutionAdapterError, match="job identifier"):
        executor.cancel_job("bad id")


def test_compatibility_wait_helper_uses_job_status(monkeypatch) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    job_id = "c" * 32
    fake = FakeClient(
        [
            {"job_id": job_id, "project": "demo", "suite": "unit", "status": "queued"},
            {"job_id": job_id, "status": "claimed"},
            {"job_id": job_id, "status": "running"},
            {"job_id": job_id, "status": "passed"},
        ]
    )
    executor._local.client = fake
    sleeps: list[float] = []
    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.time.sleep",
        sleeps.append,
    )

    result = executor.run_tests_to_completion("demo", "unit")

    assert result["status"] == "passed"
    assert [name for name, _arguments in fake.calls] == [
        "run_tests",
        "job_status",
        "job_status",
        "job_status",
    ]
    assert sleeps == [0.5, 0.5]



def test_executor_uses_thread_local_clients(monkeypatch) -> None:
    created: list[int] = []

    class TrackingClient:
        def __init__(self, _config, **_kwargs):
            created.append(threading.get_ident())

        def _call_tool(self, name, arguments):
            return {"name": name, "arguments": arguments}

    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor.LocalMCPClient",
        TrackingClient,
    )
    executor = LocalMCPBridgeExecutor(_config())
    barrier = threading.Barrier(2)
    results: list[dict] = []

    def call_status() -> None:
        barrier.wait()
        results.append(executor.queue_status())

    threads = [threading.Thread(target=call_status) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 2
    assert len(created) == 2



def test_executor_runtime_observability_uses_fixed_local_tools() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    fake = FakeClient(
        [
            {"version": "0.1.0", "projects": 3},
            {"state": "pass", "failed_checks": 0, "warning_checks": 0},
        ]
    )
    executor._local.client = fake

    assert executor.runtime_status()["projects"] == 3
    assert executor.runtime_doctor()["state"] == "pass"
    assert fake.calls == [
        ("runtime_status", {}),
        ("runtime_doctor", {}),
    ]


def test_executor_sync_project_is_commit_pinned() -> None:
    executor = LocalMCPBridgeExecutor(_config())
    commit = "c" * 40
    fake = FakeClient([{"project": "demo", "commit": commit, "changed": True}])
    executor._local.client = fake

    result = executor.sync_project("demo", commit)

    assert result == {
        "project": "demo",
        "commit": commit,
        "changed": True,
    }
    assert fake.calls == [
        (
            "sync_project",
            {"project": "demo", "commit": commit},
        )
    ]


def test_executor_sync_project_rejects_non_commit_reference() -> None:
    executor = LocalMCPBridgeExecutor(_config())

    with pytest.raises(BridgeExecutionAdapterError, match="commit"):
        executor.sync_project("demo", "main")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "job_id": "a" * 32,
            "project": "other",
            "operation": "migration",
            "state": "queued",
            "created_at": "2026-09-28T20:00:00+00:00",
            "started_at": None,
            "finished_at": None,
            "migration_state": None,
            "error_category": None,
            "pre_migration_backup_created": False,
            "output_truncated": False,
        },
        {
            "job_id": "not-a-job",
            "project": "demo",
            "operation": "migration",
            "state": "queued",
            "created_at": "2026-09-28T20:00:00+00:00",
            "started_at": None,
            "finished_at": None,
            "migration_state": None,
            "error_category": None,
            "pre_migration_backup_created": False,
            "output_truncated": False,
        },
        {
            "job_id": "a" * 32,
            "project": "demo",
            "operation": "migration",
            "state": "completed",
            "created_at": "2026-09-28T20:00:00+00:00",
            "started_at": None,
            "finished_at": None,
            "migration_state": None,
            "error_category": None,
            "pre_migration_backup_created": False,
            "output_truncated": False,
        },
    ],
)
def test_async_migration_start_rejects_invalid_or_noninitial_result(payload) -> None:
    executor = LocalMCPBridgeExecutor(_config())
    executor._local.client = FakeClient([payload])

    with pytest.raises(BridgeExecutionAdapterError):
        executor.start_migration_job("demo", "b" * 32)


def test_migration_job_status_rejects_mismatched_job_identity() -> None:
    requested = "a" * 32
    payload = {
        "job_id": "b" * 32,
        "project": "demo",
        "operation": "migration",
        "state": "running",
        "created_at": "2026-09-28T20:00:00+00:00",
        "started_at": "2026-09-28T20:00:01+00:00",
        "finished_at": None,
        "migration_state": None,
        "error_category": None,
        "pre_migration_backup_created": False,
        "output_truncated": False,
    }
    executor = LocalMCPBridgeExecutor(_config())
    executor._local.client = FakeClient([payload])

    with pytest.raises(BridgeExecutionAdapterError, match="mismatched"):
        executor.migration_job_status(requested)

def _request_session_id(request) -> str | None:
    return next(
        (
            value
            for key, value in request.header_items()
            if key.lower() == "mcp-session-id"
        ),
        None,
    )


def _request_protocol_version(request) -> str | None:
    return next(
        (
            value
            for key, value in request.header_items()
            if key.lower() == "mcp-protocol-version"
        ),
        None,
    )


def test_client_recovers_once_from_confirmed_stale_session(monkeypatch) -> None:
    calls = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}',
            headers={"Mcp-Session-Id": "session-old"},
        ),
        FakeResponse(b""),
        urllib.error.HTTPError(
            "http://127.0.0.1:8000/mcp",
            404,
            "not found",
            None,
            None,
        ),
        FakeResponse(
            b'{"jsonrpc":"2.0","id":3,"result":{"protocolVersion":"2025-03-26"}}',
            headers={"Mcp-Session-Id": "session-new"},
        ),
        FakeResponse(b""),
        FakeResponse(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"ok": True}),
                            }
                        ]
                    },
                }
            ).encode()
        ),
    ]

    def respond(request, timeout):
        calls.append(request)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(urllib.request, "urlopen", respond)
    client = LocalMCPClient(
        _config(),
        allowed_tools=frozenset({"list_projects"}),
    )

    assert client._call_tool("list_projects", {}) == {"ok": True}
    assert responses == []

    payloads = [json.loads(request.data) for request in calls]
    assert [payload["method"] for payload in payloads] == [
        "initialize",
        "notifications/initialized",
        "tools/call",
        "initialize",
        "notifications/initialized",
        "tools/call",
    ]
    assert [payload.get("id") for payload in payloads] == [1, None, 2, 3, None, 4]
    assert [_request_session_id(request) for request in calls] == [
        None,
        "session-old",
        "session-old",
        None,
        "session-new",
        "session-new",
    ]
    assert [_request_protocol_version(request) for request in calls] == [
        None,
        "2025-06-18",
        "2025-06-18",
        None,
        "2025-03-26",
        "2025-03-26",
    ]


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.HTTPError(
            "http://127.0.0.1:8000/mcp",
            401,
            "unauthorized",
            None,
            None,
        ),
        urllib.error.HTTPError(
            "http://127.0.0.1:8000/mcp",
            500,
            "server error",
            None,
            None,
        ),
        urllib.error.URLError("offline"),
        TimeoutError(),
    ],
)
def test_client_does_not_retry_ambiguous_failure_after_session_established(
    monkeypatch,
    failure,
) -> None:
    calls = []
    responses = [
        FakeResponse(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            headers={"Mcp-Session-Id": "session-old"},
        ),
        FakeResponse(b""),
        failure,
    ]

    def respond(request, timeout):
        calls.append(request)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(urllib.request, "urlopen", respond)
    client = LocalMCPClient(
        _config(),
        allowed_tools=frozenset({"list_projects"}),
    )

    with pytest.raises(BridgeExecutionAdapterError):
        client._call_tool("list_projects", {})

    assert responses == []
    assert [json.loads(request.data)["method"] for request in calls] == [
        "initialize",
        "notifications/initialized",
        "tools/call",
    ]
