import json

from runner_mcp.bridge_processor import (
    BridgeProcessState,
    BridgeProcessor,
)
from runner_mcp.bridge_protocol import parse_bridge_request, parse_bridge_result
from runner_mcp.bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayState,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.raise_on: str | None = None
        self.unsafe_result = False

    def _result(self, action: str, *args: str):
        self.calls.append((action, args))
        if self.raise_on == action:
            raise RuntimeError("private exception detail /srv/secret")
        if self.unsafe_result:
            return object()
        return {"action": action, "args": list(args)}

    def list_projects(self):
        return self._result("list_projects")

    def safety_status(self):
        return self._result("safety_status")

    def project_status(self, project: str):
        return self._result("project_status", project)

    def project_capabilities(self, project: str):
        return self._result("project_capabilities", project)

    def list_test_profiles(self, project: str):
        return self._result("list_test_profiles", project)

    def run_tests_to_completion(self, project: str, suite: str):
        return self._result("run_tests", project, suite)


class FakeSink:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []
        self.fail = False

    def persist_result(self, request_id: str, result_json: str) -> None:
        if self.fail:
            raise OSError("transport unavailable at private endpoint")
        self.records.append((request_id, result_json))


class FinalizeFailLedger(BridgeReplayLedger):
    def complete(self, request):
        raise BridgeReplayError("simulated finalize failure")


def _processor(tmp_path, *, ledger=None, executor=None, sink=None):
    return BridgeProcessor(
        ledger=ledger or BridgeReplayLedger(tmp_path / "replay.json"),
        executor=executor or FakeExecutor(),
        result_sink=sink or FakeSink(),
    )


def test_success_persists_result_before_marking_completed(tmp_path) -> None:
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    sink = FakeSink()
    processor = _processor(
        tmp_path,
        ledger=ledger,
        executor=executor,
        sink=sink,
    )
    payload = '{"request_id":"req-401","action":"project_status","project":"demo"}'

    outcome = processor.process(payload)

    assert outcome.state == BridgeProcessState.COMPLETED
    assert outcome.requires_recovery is False
    assert executor.calls == [("project_status", ("demo",))]
    assert len(sink.records) == 1
    assert sink.records[0][0] == "req-401"

    request = parse_bridge_request(payload)
    record = ledger.inspect(request)
    assert record is not None
    assert record.state == ReplayState.COMPLETED

    result = parse_bridge_result(sink.records[0][1])
    assert result.request_id == "req-401"
    assert result.state.value == "completed"


def test_completed_duplicate_never_executes_or_persists_again(tmp_path) -> None:
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    sink = FakeSink()
    processor = _processor(
        tmp_path,
        ledger=ledger,
        executor=executor,
        sink=sink,
    )
    payload = '{"request_id":"req-402","action":"list_projects"}'

    first = processor.process(payload)
    second = processor.process(payload)

    assert first.state == BridgeProcessState.COMPLETED
    assert second.state == BridgeProcessState.ALREADY_COMPLETED
    assert second.serialized_result is None
    assert executor.calls == [("list_projects", ())]
    assert len(sink.records) == 1


def test_persistence_failure_never_reexecutes_on_duplicate(tmp_path) -> None:
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    sink = FakeSink()
    sink.fail = True
    processor = _processor(
        tmp_path,
        ledger=ledger,
        executor=executor,
        sink=sink,
    )
    payload = '{"request_id":"req-403","action":"safety_status"}'

    first = processor.process(payload)
    second = processor.process(payload)

    assert first.state == BridgeProcessState.PERSISTENCE_FAILED
    assert first.requires_recovery is True
    assert first.serialized_result is not None
    assert second.state == BridgeProcessState.AMBIGUOUS
    assert executor.calls == [("safety_status", ())]

    request = parse_bridge_request(payload)
    record = ledger.inspect(request)
    assert record is not None
    assert record.state == ReplayState.CLAIMED


def test_executor_exception_becomes_safe_generic_failure(tmp_path) -> None:
    executor = FakeExecutor()
    executor.raise_on = "project_status"
    sink = FakeSink()
    processor = _processor(tmp_path, executor=executor, sink=sink)
    payload = '{"request_id":"req-404","action":"project_status","project":"demo"}'

    outcome = processor.process(payload)

    assert outcome.state == BridgeProcessState.COMPLETED
    assert len(sink.records) == 1
    result_json = sink.records[0][1]
    assert "private exception detail" not in result_json
    assert "/srv/secret" not in result_json

    result = parse_bridge_result(result_json)
    assert result.state.value == "failed"
    assert result.error_code == "EXECUTION_FAILED"
    assert result.summary == "The allow-listed Runner MCP action failed"


def test_unsupported_executor_result_fails_closed_without_raw_value(tmp_path) -> None:
    executor = FakeExecutor()
    executor.unsafe_result = True
    sink = FakeSink()
    processor = _processor(tmp_path, executor=executor, sink=sink)

    outcome = processor.process(
        '{"request_id":"req-405","action":"list_projects"}'
    )

    assert outcome.state == BridgeProcessState.COMPLETED
    result = parse_bridge_result(sink.records[0][1])
    assert result.state.value == "failed"
    assert result.error_code == "UNSAFE_RESULT"
    assert result.data is None


def test_sensitive_executor_data_is_scrubbed_before_persistence(tmp_path) -> None:
    class SensitiveExecutor(FakeExecutor):
        def project_status(self, project: str):
            self.calls.append(("project_status", (project,)))
            return {
                "project": project,
                "path": "/private/location",
                "token": "not-for-mailbox",
                "healthy": True,
            }

    executor = SensitiveExecutor()
    sink = FakeSink()
    processor = _processor(tmp_path, executor=executor, sink=sink)

    processor.process(
        '{"request_id":"req-406","action":"project_status","project":"demo"}'
    )

    raw = json.loads(sink.records[0][1])
    published = raw["data"]["result"]
    assert published["project"] == "demo"
    assert published["healthy"] is True
    assert published["path"] == "[redacted]"
    assert published["token"] == "[redacted]"


def test_run_tests_uses_explicit_terminal_executor_with_suite(tmp_path) -> None:
    executor = FakeExecutor()
    sink = FakeSink()
    processor = _processor(tmp_path, executor=executor, sink=sink)

    outcome = processor.process(
        '{"request_id":"req-407","action":"run_tests",'
        '"project":"demo","profile":"unit"}'
    )

    assert outcome.state == BridgeProcessState.COMPLETED
    assert executor.calls == [("run_tests", ("demo", "unit"))]


def test_all_allow_listed_actions_dispatch_only_to_explicit_methods(tmp_path) -> None:
    executor = FakeExecutor()
    sink = FakeSink()
    processor = _processor(tmp_path, executor=executor, sink=sink)
    payloads = [
        '{"request_id":"req-408","action":"list_projects"}',
        '{"request_id":"req-409","action":"safety_status"}',
        '{"request_id":"req-410","action":"project_status","project":"demo"}',
        '{"request_id":"req-411","action":"project_capabilities","project":"demo"}',
        '{"request_id":"req-412","action":"list_test_profiles","project":"demo"}',
        '{"request_id":"req-413","action":"run_tests","project":"demo","profile":"unit"}',
    ]

    for payload in payloads:
        assert processor.process(payload).state == BridgeProcessState.COMPLETED

    assert [name for name, _args in executor.calls] == [
        "list_projects",
        "safety_status",
        "project_status",
        "project_capabilities",
        "list_test_profiles",
        "run_tests",
    ]


def test_changed_content_under_claimed_request_id_fails_before_execution(
    tmp_path,
) -> None:
    ledger = BridgeReplayLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    sink = FakeSink()
    sink.fail = True
    processor = _processor(
        tmp_path,
        ledger=ledger,
        executor=executor,
        sink=sink,
    )

    processor.process(
        '{"request_id":"req-414","action":"project_status","project":"demo"}'
    )

    try:
        processor.process(
            '{"request_id":"req-414","action":"project_status","project":"other"}'
        )
    except BridgeReplayError:
        pass
    else:
        raise AssertionError("changed request content should fail closed")

    assert executor.calls == [("project_status", ("demo",))]


def test_result_persisted_but_ledger_finalize_failed_requires_recovery(
    tmp_path,
) -> None:
    ledger = FinalizeFailLedger(tmp_path / "replay.json")
    executor = FakeExecutor()
    sink = FakeSink()
    processor = _processor(
        tmp_path,
        ledger=ledger,
        executor=executor,
        sink=sink,
    )

    outcome = processor.process(
        '{"request_id":"req-415","action":"list_projects"}'
    )

    assert outcome.state == BridgeProcessState.FINALIZE_FAILED
    assert outcome.requires_recovery is True
    assert len(sink.records) == 1
    assert executor.calls == [("list_projects", ())]
