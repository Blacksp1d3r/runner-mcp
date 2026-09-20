import json
import os
from pathlib import Path

import pytest

from runner_mcp.bridge_processor import BridgeExecutionAdapterError
from runner_mcp.bridge_protocol import (
    BridgeAction,
    BridgeResult,
    BridgeResultState,
    parse_bridge_result,
)
from runner_mcp.bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayState,
)
from runner_mcp.bridge_resilience import (
    TransportFailureKind,
    WatcherState,
    parse_watcher_heartbeat,
)
from runner_mcp.github_mailbox import (
    GitHubMailboxResultSinkError,
    GitHubMailboxTransportError,
)
from runner_mcp.github_watcher import (
    MAX_CURSOR_BYTES,
    GitHubMailboxWatcher,
    GitHubWatcherCursorStore,
    GitHubWatcherCycleState,
    GitHubWatcherError,
)


class FakeTransport:
    def __init__(self) -> None:
        self.head = "b" * 40
        self.changed_ids: list[str] = []
        self.requests: dict[str, bytes] = {}
        self.results: dict[str, BridgeResult] = {}
        self.persisted_json: dict[str, str] = {}
        self.heartbeats = []
        self.fail_head = False
        self.fail_compare = False
        self.fail_persist = False
        self.fail_heartbeat = False
        self.compare_calls: list[tuple[str, str]] = []

    def request_head_sha(self) -> str:
        if self.fail_head:
            raise GitHubMailboxTransportError(
                "head unavailable",
                kind=TransportFailureKind.UNAVAILABLE,
            )
        return self.head

    def changed_request_ids(self, *, base_sha: str, head_sha: str) -> list[str]:
        self.compare_calls.append((base_sha, head_sha))
        if self.fail_compare:
            raise GitHubMailboxTransportError(
                "compare unavailable",
                kind=TransportFailureKind.UNAVAILABLE,
            )
        return list(self.changed_ids)

    def fetch_request(self, request_id: str) -> bytes:
        return self.requests[request_id]

    def fetch_result(self, request_id: str) -> BridgeResult | None:
        return self.results.get(request_id)

    def persist_result(self, request_id: str, result_json: str) -> None:
        if self.fail_persist:
            raise GitHubMailboxResultSinkError(
                "persist unavailable",
                kind=TransportFailureKind.UNAVAILABLE,
            )
        self.persisted_json[request_id] = result_json
        self.results[request_id] = parse_bridge_result(result_json)

    def publish_heartbeat(self, heartbeat_json: str) -> None:
        if self.fail_heartbeat:
            raise GitHubMailboxTransportError(
                "heartbeat unavailable",
                kind=TransportFailureKind.UNAVAILABLE,
            )
        self.heartbeats.append(parse_watcher_heartbeat(heartbeat_json))


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.fail_action: str | None = None

    def _call(self, action: str, *args: str):
        self.calls.append((action, args))
        if self.fail_action == action:
            raise BridgeExecutionAdapterError("safe adapter boundary failure")
        return {"action": action, "args": list(args)}

    def list_projects(self):
        return self._call("list_projects")

    def safety_status(self):
        return self._call("safety_status")

    def project_status(self, project: str):
        return self._call("project_status", project)

    def project_capabilities(self, project: str):
        return self._call("project_capabilities", project)

    def list_test_profiles(self, project: str):
        return self._call("list_test_profiles", project)

    def run_tests_to_completion(self, project: str, suite: str):
        return self._call("run_tests", project, suite)


class FailingAdvanceCursorStore(GitHubWatcherCursorStore):
    def advance(self, *, expected_sha: str, new_sha: str) -> None:
        raise GitHubWatcherError("simulated cursor race")


def _request(request_id: str, action: str = "list_projects") -> bytes:
    return json.dumps(
        {
            "request_id": request_id,
            "action": action,
        },
        separators=(",", ":"),
    ).encode()


def _existing_result(
    request_id: str,
    action: BridgeAction = BridgeAction.LIST_PROJECTS,
) -> BridgeResult:
    return BridgeResult(
        request_id=request_id,
        action=action,
        state=BridgeResultState.COMPLETED,
        data={"result": "already-durable"},
    )


def _watcher(
    tmp_path: Path,
    *,
    transport: FakeTransport | None = None,
    executor: FakeExecutor | None = None,
    ledger: BridgeReplayLedger | None = None,
    cursor_store: GitHubWatcherCursorStore | None = None,
) -> tuple[
    GitHubMailboxWatcher,
    FakeTransport,
    FakeExecutor,
    BridgeReplayLedger,
    GitHubWatcherCursorStore,
]:
    selected_transport = transport or FakeTransport()
    selected_executor = executor or FakeExecutor()
    selected_ledger = ledger or BridgeReplayLedger(tmp_path / "replay.json")
    selected_cursor = cursor_store or GitHubWatcherCursorStore(
        tmp_path / "cursor.json"
    )
    watcher = GitHubMailboxWatcher(
        transport=selected_transport,
        ledger=selected_ledger,
        executor=selected_executor,
        cursor_store=selected_cursor,
        stale_after_seconds=300,
    )
    return (
        watcher,
        selected_transport,
        selected_executor,
        selected_ledger,
        selected_cursor,
    )


def test_cursor_store_initializes_reads_and_restricts_permissions(tmp_path) -> None:
    path = tmp_path / "cursor.json"
    store = GitHubWatcherCursorStore(path)

    assert store.read() is None
    store.initialize("a" * 40)

    assert store.read() == "a" * 40
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_cursor_store_refuses_second_initialization(tmp_path) -> None:
    store = GitHubWatcherCursorStore(tmp_path / "cursor.json")
    store.initialize("a" * 40)

    with pytest.raises(GitHubWatcherError, match="already initialized"):
        store.initialize("b" * 40)

    assert store.read() == "a" * 40


def test_cursor_store_requires_expected_sha_for_advance(tmp_path) -> None:
    store = GitHubWatcherCursorStore(tmp_path / "cursor.json")
    store.initialize("a" * 40)

    with pytest.raises(GitHubWatcherError, match="changed concurrently"):
        store.advance(expected_sha="b" * 40, new_sha="c" * 40)

    assert store.read() == "a" * 40
    store.advance(expected_sha="a" * 40, new_sha="c" * 40)
    assert store.read() == "c" * 40


def test_cursor_store_requires_existing_parent(tmp_path) -> None:
    store = GitHubWatcherCursorStore(tmp_path / "missing" / "cursor.json")

    with pytest.raises(GitHubWatcherError, match="parent"):
        store.read()


def test_cursor_store_refuses_symlink(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text("", encoding="utf-8")
    link = tmp_path / "cursor.json"
    link.symlink_to(target)
    store = GitHubWatcherCursorStore(link)

    with pytest.raises(GitHubWatcherError, match="opened"):
        store.read()


@pytest.mark.parametrize(
    "content",
    [
        "{",
        '{"version":1,"request_head_sha":"bad"}',
        '{"version":2,"request_head_sha":"' + ("a" * 40) + '"}',
        '{"version":1,"request_head_sha":"' + ("a" * 40) + '","extra":1}',
        (
            '{"version":1,"version":1,"request_head_sha":"'
            + ("a" * 40)
            + '"}'
        ),
        '{"version":NaN,"request_head_sha":"' + ("a" * 40) + '"}',
    ],
)
def test_cursor_store_rejects_invalid_state(tmp_path, content: str) -> None:
    path = tmp_path / "cursor.json"
    path.write_text(content, encoding="utf-8")
    store = GitHubWatcherCursorStore(path)

    with pytest.raises(GitHubWatcherError):
        store.read()


def test_cursor_store_rejects_oversized_state(tmp_path) -> None:
    path = tmp_path / "cursor.json"
    path.write_text("x" * (MAX_CURSOR_BYTES + 1), encoding="utf-8")

    with pytest.raises(GitHubWatcherError, match="size limit"):
        GitHubWatcherCursorStore(path).read()


def test_uninitialized_watcher_never_processes_historical_requests(tmp_path) -> None:
    watcher, transport, executor, _ledger, _cursor = _watcher(tmp_path)
    transport.changed_ids = ["req-701"]
    transport.requests["req-701"] = _request("req-701")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.UNINITIALIZED
    assert outcome.processed_requests == 0
    assert executor.calls == []
    assert transport.compare_calls == []
    assert outcome.heartbeat.state == WatcherState.DEGRADED
    assert outcome.heartbeat_published is True


def test_explicit_bootstrap_skips_existing_history(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    transport.changed_ids = ["req-702"]
    transport.requests["req-702"] = _request("req-702")

    watcher.bootstrap_cursor_at_current_head()
    outcome = watcher.run_cycle()

    assert cursor.read() == transport.head
    assert outcome.state == GitHubWatcherCycleState.IDLE
    assert executor.calls == []
    assert transport.compare_calls == []


def test_fresh_request_executes_once_and_advances_cursor(tmp_path) -> None:
    watcher, transport, executor, ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.head = "b" * 40
    transport.changed_ids = ["req-703"]
    transport.requests["req-703"] = _request("req-703")

    first = watcher.run_cycle()
    second = watcher.run_cycle()

    assert first.state == GitHubWatcherCycleState.PROCESSED
    assert first.discovered_requests == 1
    assert first.processed_requests == 1
    assert first.reconciled_requests == 0
    assert first.recovery_attention == 0
    assert first.heartbeat.state == WatcherState.HEALTHY
    assert cursor.read() == "b" * 40
    assert executor.calls == [("list_projects", ())]
    assert "req-703" in transport.persisted_json

    request = parse_bridge_result(transport.persisted_json["req-703"])
    assert request.state == BridgeResultState.COMPLETED

    replay_request = __import__(
        "runner_mcp.bridge_protocol",
        fromlist=["parse_bridge_request"],
    ).parse_bridge_request(transport.requests["req-703"])
    record = ledger.inspect(replay_request)
    assert record is not None
    assert record.state == ReplayState.COMPLETED

    assert second.state == GitHubWatcherCycleState.IDLE
    assert executor.calls == [("list_projects", ())]


def test_existing_result_is_reconciled_without_execution(tmp_path) -> None:
    watcher, transport, executor, ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-704"]
    transport.requests["req-704"] = _request("req-704")
    transport.results["req-704"] = _existing_result("req-704")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.PROCESSED
    assert outcome.processed_requests == 0
    assert outcome.reconciled_requests == 1
    assert executor.calls == []
    assert cursor.read() == transport.head

    replay_request = __import__(
        "runner_mcp.bridge_protocol",
        fromlist=["parse_bridge_request"],
    ).parse_bridge_request(transport.requests["req-704"])
    record = ledger.inspect(replay_request)
    assert record is not None
    assert record.state == ReplayState.COMPLETED


def test_existing_result_action_mismatch_requires_recovery(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-705"]
    transport.requests["req-705"] = _request("req-705")
    transport.results["req-705"] = _existing_result(
        "req-705",
        action=BridgeAction.SAFETY_STATUS,
    )

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert outcome.recovery_attention == 1
    assert outcome.heartbeat.state == WatcherState.DEGRADED
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_claimed_request_without_result_is_never_reexecuted(tmp_path) -> None:
    watcher, transport, executor, ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-706"]
    transport.requests["req-706"] = _request("req-706")

    replay_request = __import__(
        "runner_mcp.bridge_protocol",
        fromlist=["parse_bridge_request"],
    ).parse_bridge_request(transport.requests["req-706"])
    ledger.claim(replay_request)

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert outcome.recovery_attention == 1
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_completed_request_without_result_is_never_reexecuted(tmp_path) -> None:
    watcher, transport, executor, ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-707"]
    transport.requests["req-707"] = _request("req-707")

    replay_request = __import__(
        "runner_mcp.bridge_protocol",
        fromlist=["parse_bridge_request"],
    ).parse_bridge_request(transport.requests["req-707"])
    ledger.claim(replay_request)
    ledger.complete(replay_request)

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert outcome.recovery_attention == 1
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_result_persistence_failure_does_not_reexecute(tmp_path) -> None:
    watcher, transport, executor, ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-708"]
    transport.requests["req-708"] = _request("req-708")
    transport.fail_persist = True

    first = watcher.run_cycle()
    second = watcher.run_cycle()

    assert first.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert second.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert executor.calls == [("list_projects", ())]
    assert cursor.read() == "a" * 40

    replay_request = __import__(
        "runner_mcp.bridge_protocol",
        fromlist=["parse_bridge_request"],
    ).parse_bridge_request(transport.requests["req-708"])
    record = ledger.inspect(replay_request)
    assert record is not None
    assert record.state == ReplayState.CLAIMED


def test_malformed_request_blocks_cursor_and_remaining_work(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-709", "req-710"]
    transport.requests["req-709"] = b'{"request_id":"wrong","action":"list_projects"}'
    transport.requests["req-710"] = _request("req-710")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert outcome.discovered_requests == 2
    assert outcome.heartbeat.pending_requests == 2
    assert outcome.recovery_attention == 1
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_transport_head_failure_is_degraded_without_execution(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.fail_head = True

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.DEGRADED
    assert outcome.heartbeat.state == WatcherState.DEGRADED
    assert outcome.heartbeat_published is True
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_compare_failure_is_degraded_without_cursor_advance(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.fail_compare = True

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.DEGRADED
    assert cursor.read() == "a" * 40
    assert executor.calls == []


def test_non_request_ref_change_advances_cursor_without_execution(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = []

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.IDLE
    assert cursor.read() == transport.head
    assert executor.calls == []


def test_cursor_race_never_reexecutes_completed_action(tmp_path) -> None:
    path = tmp_path / "cursor.json"
    cursor = FailingAdvanceCursorStore(path)
    cursor.initialize("a" * 40)
    watcher, transport, executor, _ledger, _ = _watcher(
        tmp_path,
        cursor_store=cursor,
    )
    transport.changed_ids = ["req-711"]
    transport.requests["req-711"] = _request("req-711")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert executor.calls == [("list_projects", ())]
    assert cursor.read() == "a" * 40


def test_heartbeat_delivery_failure_does_not_roll_back_cursor(tmp_path) -> None:
    watcher, transport, executor, _ledger, cursor = _watcher(tmp_path)
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-712"]
    transport.requests["req-712"] = _request("req-712")
    transport.fail_heartbeat = True

    first = watcher.run_cycle()
    second = watcher.run_cycle()

    assert first.state == GitHubWatcherCycleState.DEGRADED
    assert first.processed_requests == 1
    assert first.heartbeat_published is False
    assert cursor.read() == transport.head
    assert second.state == GitHubWatcherCycleState.DEGRADED
    assert executor.calls == [("list_projects", ())]


def test_executor_failure_is_persisted_as_terminal_result_and_cursor_advances(
    tmp_path,
) -> None:
    executor = FakeExecutor()
    executor.fail_action = "list_projects"
    watcher, transport, selected_executor, _ledger, cursor = _watcher(
        tmp_path,
        executor=executor,
    )
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-713"]
    transport.requests["req-713"] = _request("req-713")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.PROCESSED
    assert selected_executor.calls == [("list_projects", ())]
    result = transport.results["req-713"]
    assert result.state == BridgeResultState.FAILED
    assert result.error_code == "EXECUTION_FAILED"
    assert cursor.read() == transport.head


class FinalizeFailLedger(BridgeReplayLedger):
    def complete(self, request):
        raise BridgeReplayError("simulated finalize failure")


def test_finalize_failure_keeps_cursor_for_safe_reconciliation(tmp_path) -> None:
    ledger = FinalizeFailLedger(tmp_path / "replay.json")
    watcher, transport, executor, _selected_ledger, cursor = _watcher(
        tmp_path,
        ledger=ledger,
    )
    cursor.initialize("a" * 40)
    transport.changed_ids = ["req-714"]
    transport.requests["req-714"] = _request("req-714")

    outcome = watcher.run_cycle()

    assert outcome.state == GitHubWatcherCycleState.RECOVERY_REQUIRED
    assert "req-714" in transport.results
    assert cursor.read() == "a" * 40
    assert executor.calls == [("list_projects", ())]


def test_watcher_rejects_unsupported_stale_threshold(tmp_path) -> None:
    transport = FakeTransport()
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    cursor = GitHubWatcherCursorStore(tmp_path / "cursor.json")

    with pytest.raises(ValueError, match="stale_after_seconds"):
        GitHubMailboxWatcher(
            transport=transport,
            ledger=ledger,
            executor=FakeExecutor(),
            cursor_store=cursor,
            stale_after_seconds=29,
        )
