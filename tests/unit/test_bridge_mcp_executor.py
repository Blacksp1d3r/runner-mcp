import json
import threading
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
    deploy_job = "c" * 32
    rollback_job = "d" * 32
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
        else:
            executor.approval_status(args[0])


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
        def __init__(self, _config):
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
