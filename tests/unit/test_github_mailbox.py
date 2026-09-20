import base64
import email.message
import urllib.error
import urllib.request

import pytest

from runner_mcp.bridge_processor import (
    BridgeProcessor,
    BridgeProcessState,
)
from runner_mcp.bridge_protocol import (
    BridgeAction,
    BridgeResult,
    BridgeResultState,
    parse_bridge_request,
    serialize_bridge_result,
)
from runner_mcp.bridge_replay import BridgeReplayLedger, ReplayState
from runner_mcp.bridge_resilience import (
    BridgeResilienceError,
    TransportFailureKind,
    WatcherHeartbeat,
    WatcherState,
    serialize_watcher_heartbeat,
)
from runner_mcp.github_mailbox import (
    GITHUB_API_BASE,
    HEARTBEAT_PATH,
    REQUESTS_PATH,
    RESULTS_PATH,
    GitHubApiSession,
    GitHubMailboxConfig,
    GitHubMailboxResultSinkError,
    GitHubMailboxTransport,
    GitHubMailboxTransportError,
)


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._payload


class FakeSession:
    def __init__(self) -> None:
        self.get_responses: list[object] = []
        self.get_calls: list[tuple[str, dict[str, str] | None, bool]] = []
        self.put_calls: list[tuple[str, dict]] = []
        self.put_error: GitHubMailboxTransportError | None = None

    def get_json(self, api_path, *, query=None, allow_not_found=False):
        self.get_calls.append((api_path, query, allow_not_found))
        if not self.get_responses:
            raise AssertionError("unexpected get_json call")
        result = self.get_responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def put_json(self, api_path, *, payload):
        self.put_calls.append((api_path, payload))
        if self.put_error is not None:
            raise self.put_error
        return {"ok": True}


class FakeExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def list_projects(self):
        self.calls += 1
        return [{"project": "demo"}]

    def safety_status(self):
        raise AssertionError("unexpected executor call")

    def project_status(self, project: str):
        raise AssertionError("unexpected executor call")

    def project_capabilities(self, project: str):
        raise AssertionError("unexpected executor call")

    def list_test_profiles(self, project: str):
        raise AssertionError("unexpected executor call")

    def run_tests_to_completion(self, project: str, suite: str):
        raise AssertionError("unexpected executor call")


def _config() -> GitHubMailboxConfig:
    return GitHubMailboxConfig(
        repository="example/runner-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
    )


def _transport(session: FakeSession | None = None) -> GitHubMailboxTransport:
    return GitHubMailboxTransport(
        config=_config(),
        session=session or FakeSession(),
    )


def _file_record(content: bytes, *, sha: str = "a" * 40) -> dict:
    encoded = base64.b64encode(content).decode("ascii")
    return {
        "sha": sha,
        "encoding": "base64",
        "content": encoded,
    }


def _completed_result(request_id: str = "req-501") -> str:
    return serialize_bridge_result(
        BridgeResult(
            request_id=request_id,
            action=BridgeAction.LIST_PROJECTS,
            state=BridgeResultState.COMPLETED,
            data={"projects": ["demo"]},
        )
    )


@pytest.mark.parametrize(
    "repository",
    [
        "",
        "owner-only",
        "/repo",
        "owner/",
        "owner/repo/extra",
        "owner repo/name",
        "owner/name?query",
    ],
)
def test_mailbox_config_rejects_unsafe_repository(repository: str) -> None:
    with pytest.raises(ValueError, match="repository"):
        GitHubMailboxConfig(
            repository=repository,
            request_ref="runner-control",
            result_ref="runner-results",
        )


@pytest.mark.parametrize(
    "ref",
    [
        "",
        ".hidden",
        "/absolute",
        "feature//nested",
        "feature/../main",
        "feature@{1}",
        "branch.lock",
        "branch.",
        "bad ref",
        "bad?ref",
    ],
)
def test_mailbox_config_rejects_unsafe_refs(ref: str) -> None:
    with pytest.raises(ValueError, match="ref"):
        GitHubMailboxConfig(
            repository="example/repo",
            request_ref=ref,
            result_ref="runner-results",
        )


@pytest.mark.parametrize("token", ["", "has space", "line\nbreak", "tökén"])
def test_api_session_rejects_unsafe_token(token: str) -> None:
    with pytest.raises(ValueError, match="token"):
        GitHubApiSession(token=token)


@pytest.mark.parametrize("timeout", [0, 0.5, 121])
def test_api_session_bounds_timeout(timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout"):
        GitHubApiSession(token="safe-token", timeout_seconds=timeout)


def test_api_session_uses_fixed_github_host_and_safe_headers(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, *, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return FakeResponse(b'{"ok":true}')

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    session = GitHubApiSession(token="secret-token", timeout_seconds=12)

    result = session.get_json(
        "/repos/example/repo/contents/file.json",
        query={"ref": "main"},
    )

    assert result == {"ok": True}
    assert captured["url"] == (
        f"{GITHUB_API_BASE}/repos/example/repo/contents/file.json?ref=main"
    )
    assert captured["authorization"] == "Bearer secret-token"
    assert captured["user_agent"] == "runner-mcp"
    assert captured["timeout"] == 12


@pytest.mark.parametrize(
    "api_path",
    [
        "https://evil.invalid/repos/example/repo",
        "/other/example/repo",
        "/repos/example/repo\nX-Injected: yes",
        "/repos/example/repo?redirect=https://evil.invalid",
        "/repos/example/repo#fragment",
        "/repos/example\\repo",
    ],
)
def test_api_session_rejects_non_repository_scoped_paths(api_path: str) -> None:
    session = GitHubApiSession(token="safe-token")

    with pytest.raises(ValueError, match="repository-scoped"):
        session.get_json(api_path)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"value":1,"value":2}',
        b'{"value":NaN}',
        b'{"nested":{"x":1,"x":2}}',
        b'not-json',
        b'\xff',
    ],
)
def test_api_session_rejects_non_strict_json(monkeypatch, payload: bytes) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(payload),
    )
    session = GitHubApiSession(token="safe-token")

    with pytest.raises(GitHubMailboxTransportError) as caught:
        session.get_json("/repos/example/repo/contents/file.json")

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE


def test_api_session_rejects_oversized_response(monkeypatch) -> None:
    payload = b"x" * (1_048_576 + 1)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(payload),
    )
    session = GitHubApiSession(token="safe-token")

    with pytest.raises(GitHubMailboxTransportError) as caught:
        session.get_json("/repos/example/repo/contents/file.json")

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE


def _http_error(status: int, headers: dict[str, str] | None = None):
    message = email.message.Message()
    for key, value in (headers or {}).items():
        message[key] = value
    return urllib.error.HTTPError(
        "https://api.github.com/repos/example/repo",
        status,
        "error",
        message,
        None,
    )


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_http_error(401), TransportFailureKind.AUTHORIZATION),
        (_http_error(403), TransportFailureKind.AUTHORIZATION),
        (
            _http_error(403, {"X-RateLimit-Remaining": "0"}),
            TransportFailureKind.RATE_LIMITED,
        ),
        (
            _http_error(403, {"Retry-After": "60"}),
            TransportFailureKind.RATE_LIMITED,
        ),
        (_http_error(408), TransportFailureKind.TIMEOUT),
        (_http_error(409), TransportFailureKind.UNAVAILABLE),
        (_http_error(429), TransportFailureKind.RATE_LIMITED),
        (_http_error(500), TransportFailureKind.UNAVAILABLE),
        (_http_error(503), TransportFailureKind.UNAVAILABLE),
        (_http_error(422), TransportFailureKind.INVALID_RESPONSE),
    ],
)
def test_api_session_classifies_http_failures(
    monkeypatch,
    error,
    expected: TransportFailureKind,
) -> None:
    def fail(request, timeout):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    session = GitHubApiSession(token="safe-token")

    with pytest.raises(GitHubMailboxTransportError) as caught:
        session.get_json("/repos/example/repo/contents/file.json")

    assert caught.value.kind == expected
    assert "safe-token" not in str(caught.value)


def test_api_session_allows_explicit_not_found(monkeypatch) -> None:
    def fail(request, timeout):
        raise _http_error(404)

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    session = GitHubApiSession(token="safe-token")

    assert (
        session.get_json(
            "/repos/example/repo/contents/missing.json",
            allow_not_found=True,
        )
        is None
    )


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TimeoutError(), TransportFailureKind.TIMEOUT),
        (
            urllib.error.URLError("offline"),
            TransportFailureKind.UNAVAILABLE,
        ),
    ],
)
def test_api_session_classifies_network_failures(
    monkeypatch,
    error,
    expected: TransportFailureKind,
) -> None:
    def fail(request, timeout):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    session = GitHubApiSession(token="safe-token")

    with pytest.raises(GitHubMailboxTransportError) as caught:
        session.get_json("/repos/example/repo/contents/file.json")

    assert caught.value.kind == expected


def test_list_request_ids_filters_non_request_entries() -> None:
    session = FakeSession()
    session.get_responses.append(
        [
            {"type": "file", "name": "req-001.json"},
            {"type": "file", "name": "req-002.json"},
            {"type": "file", "name": "bad id.json"},
            {"type": "file", "name": "notes.txt"},
            {"type": "dir", "name": "nested"},
        ]
    )

    assert _transport(session).list_request_ids() == ["req-001", "req-002"]
    path, query, allow_not_found = session.get_calls[0]
    assert path.endswith(f"/contents/{REQUESTS_PATH}")
    assert query == {"ref": "runner-control"}
    assert allow_not_found is True


def test_list_request_ids_treats_missing_directory_as_empty() -> None:
    session = FakeSession()
    session.get_responses.append(None)

    assert _transport(session).list_request_ids() == []


def test_list_request_ids_rejects_duplicate_ids() -> None:
    session = FakeSession()
    session.get_responses.append(
        [
            {"type": "file", "name": "req-001.json"},
            {"type": "file", "name": "req-001.json"},
        ]
    )

    with pytest.raises(GitHubMailboxTransportError) as caught:
        _transport(session).list_request_ids()

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE


def test_fetch_request_accepts_wrapped_base64_and_matches_filename() -> None:
    payload = b'{"request_id":"req-003","action":"list_projects"}'
    record = _file_record(payload)
    encoded = record["content"]
    record["content"] = f"{encoded[:12]}\n{encoded[12:]}\n"
    session = FakeSession()
    session.get_responses.append(record)

    fetched = _transport(session).fetch_request("req-003")

    assert fetched == payload


def test_fetch_request_rejects_payload_id_mismatch() -> None:
    session = FakeSession()
    session.get_responses.append(
        _file_record(b'{"request_id":"req-other","action":"list_projects"}')
    )

    with pytest.raises(GitHubMailboxTransportError) as caught:
        _transport(session).fetch_request("req-004")

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE


@pytest.mark.parametrize(
    "record",
    [
        {"sha": "a" * 40, "encoding": "base64", "content": "%%%"},
        {"sha": "not-a-sha", "encoding": "base64", "content": "e30="},
        {"sha": "a" * 40, "encoding": "utf-8", "content": "e30="},
        {"sha": "a" * 40, "encoding": "base64", "content": 123},
    ],
)
def test_fetch_request_rejects_invalid_file_metadata(record: dict) -> None:
    session = FakeSession()
    session.get_responses.append(record)

    with pytest.raises(GitHubMailboxTransportError) as caught:
        _transport(session).fetch_request("req-005")

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE


def test_result_exists_uses_result_ref() -> None:
    session = FakeSession()
    session.get_responses.extend([None, _file_record(_completed_result().encode())])
    transport = _transport(session)

    assert transport.result_exists("req-501") is False
    assert transport.result_exists("req-501") is True
    assert all(
        call[1] == {"ref": "runner-results"}
        for call in session.get_calls
    )


def test_persist_result_create_once() -> None:
    result_json = _completed_result("req-502")
    session = FakeSession()
    session.get_responses.append(None)
    transport = _transport(session)

    transport.persist_result("req-502", result_json)

    assert len(session.put_calls) == 1
    path, payload = session.put_calls[0]
    assert path.endswith(f"/contents/{RESULTS_PATH}/req-502.json")
    assert payload["branch"] == "runner-results"
    assert base64.b64decode(payload["content"]).decode() == result_json
    assert "sha" not in payload


def test_persist_result_is_idempotent_for_identical_content() -> None:
    result_json = _completed_result("req-503")
    session = FakeSession()
    session.get_responses.append(_file_record(result_json.encode()))

    _transport(session).persist_result("req-503", result_json)

    assert session.put_calls == []


def test_persist_result_rejects_conflicting_existing_content() -> None:
    result_json = _completed_result("req-504")
    other = _completed_result("req-other")
    session = FakeSession()
    session.get_responses.append(_file_record(other.encode()))

    with pytest.raises(GitHubMailboxResultSinkError) as caught:
        _transport(session).persist_result("req-504", result_json)

    assert caught.value.kind == TransportFailureKind.INVALID_RESPONSE
    assert session.put_calls == []


@pytest.mark.parametrize("failure_phase", ["read", "write"])
def test_persist_result_wraps_all_transport_failures_for_processor(
    failure_phase: str,
) -> None:
    result_json = _completed_result("req-505")
    session = FakeSession()
    transport_error = GitHubMailboxTransportError(
        "safe failure",
        kind=TransportFailureKind.UNAVAILABLE,
    )
    if failure_phase == "read":
        session.get_responses.append(transport_error)
    else:
        session.get_responses.append(None)
        session.put_error = transport_error

    with pytest.raises(GitHubMailboxResultSinkError) as caught:
        _transport(session).persist_result("req-505", result_json)

    assert caught.value.kind == TransportFailureKind.UNAVAILABLE


def test_publish_heartbeat_creates_and_updates_fixed_path() -> None:
    heartbeat = serialize_watcher_heartbeat(
        WatcherHeartbeat(
            state=WatcherState.HEALTHY,
            pending_requests=0,
            stale_requests=0,
            recovery_attention=0,
        )
    )
    session = FakeSession()
    session.get_responses.extend([None, _file_record(heartbeat.encode(), sha="b" * 40)])
    transport = _transport(session)

    transport.publish_heartbeat(heartbeat)
    transport.publish_heartbeat(heartbeat)

    assert len(session.put_calls) == 2
    first_path, first_payload = session.put_calls[0]
    second_path, second_payload = session.put_calls[1]
    assert first_path.endswith(f"/contents/{HEARTBEAT_PATH}")
    assert second_path == first_path
    assert "sha" not in first_payload
    assert second_payload["sha"] == "b" * 40
    assert first_payload["branch"] == "runner-results"


def test_publish_heartbeat_rejects_invalid_payload_before_transport() -> None:
    session = FakeSession()

    with pytest.raises(BridgeResilienceError):
        _transport(session).publish_heartbeat('{"state":"healthy"}')

    assert session.get_calls == []
    assert session.put_calls == []


def test_bridge_processor_maps_transport_failure_to_recovery_state(tmp_path) -> None:
    session = FakeSession()
    session.get_responses.append(None)
    session.put_error = GitHubMailboxTransportError(
        "transport unavailable",
        kind=TransportFailureKind.UNAVAILABLE,
    )
    transport = _transport(session)
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    processor = BridgeProcessor(
        ledger=ledger,
        executor=executor,
        result_sink=transport,
    )
    payload = b'{"request_id":"req-506","action":"list_projects"}'

    outcome = processor.process(payload)

    assert outcome.state == BridgeProcessState.PERSISTENCE_FAILED
    assert outcome.requires_recovery is True
    assert outcome.serialized_result is not None
    assert executor.calls == 1

    request = parse_bridge_request(payload)
    record = ledger.inspect(request)
    assert record is not None
    assert record.state == ReplayState.CLAIMED
