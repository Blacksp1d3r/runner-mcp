import json

from runner_mcp.bridge_processor import (
    BridgeExecutionAdapterError,
    BridgeProcessor,
    BridgeProcessState,
    BridgeResultSinkError,
)
from runner_mcp.bridge_protocol import parse_bridge_request, parse_bridge_result
from runner_mcp.bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayState,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.raise_on: str | None = None
        self.unsafe_result = False

    def _result(self, action: str, *args: object):
        self.calls.append((action, args))
        if self.raise_on == action:
            raise BridgeExecutionAdapterError("private exception detail /srv/secret")
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

    def sync_project(self, project: str, commit: str):
        return self._result("sync_project", project, commit)

    def run_tests(self, project: str, suite: str):
        return self._result("run_tests", project, suite)

    def queue_status(self):
        return self._result("queue_status")

    def worker_status(self):
        return self._result("worker_status")

    def job_status(self, job_id: str):
        return self._result("job_status", job_id)

    def cancel_job(self, job_id: str):
        return self._result("cancel_job", job_id)

    def job_log(self, job_id: str, *, offset: int = 0, length: int = 100):
        return self._result("job_log", job_id, offset, length)

    def list_services(self, project: str):
        return self._result("list_services", project)

    def service_status(self, project: str, service: str):
        return self._result("service_status", project, service)

    def start_service(self, project: str, service: str):
        return self._result("start_service", project, service)

    def stop_service(self, project: str, service: str):
        return self._result("stop_service", project, service)

    def restart_service(self, project: str, service: str):
        return self._result("restart_service", project, service)

    def list_backups(self, project: str, *, limit: int = 100):
        return self._result("list_backups", project, limit)

    def backup_database(self, project: str):
        return self._result("backup_database", project)

    def request_action_approval(self, project: str, operation: str):
        return self._result("request_action_approval", project, operation)

    def approval_status(self, approval_id: str):
        return self._result("approval_status", approval_id)

    def migration_status(self, project: str):
        return self._result("migration_status", project)

    def apply_migrations(self, project: str, approval_id: str):
        return self._result("apply_migrations", project, approval_id)

    def plan_deploy(self, project: str):
        return self._result("plan_deploy", project)

    def deploy_staging(self, project: str, approval_id: str):
        return self._result("deploy_staging", project, approval_id)

    def deployment_status(self, job_id: str):
        return self._result("deployment_status", job_id)

    def list_releases(self, project: str, *, limit: int = 100):
        return self._result("list_releases", project, limit)

    def rollback_plan(self, project: str):
        return self._result("rollback_plan", project)

    def rollback_release(self, project: str, approval_id: str):
        return self._result("rollback_release", project, approval_id)

    def rollback_status(self, job_id: str):
        return self._result("rollback_status", job_id)

    def runtime_status(self):
        return self._result("runtime_status")

    def self_update(self, commit: str):
        return self._result("self_update", commit)

    def self_update_status(self, job_id: str):
        return self._result("self_update_status", job_id)


class FakeSink:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []
        self.fail = False

    def persist_result(self, request_id: str, result_json: str) -> None:
        if self.fail:
            raise BridgeResultSinkError("transport unavailable at private endpoint")
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


def test_run_tests_uses_immediate_job_executor_with_suite(tmp_path) -> None:
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
        '{"request_id":"req-sync-all","action":"sync_project","project":"demo","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
        '{"request_id":"req-413","action":"run_tests","project":"demo","profile":"unit"}',
        '{"request_id":"req-416","action":"queue_status"}',
        '{"request_id":"req-417","action":"worker_status"}',
        '{"request_id":"req-418","action":"job_status","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
        '{"request_id":"req-419","action":"cancel_job","job_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}',
        '{"request_id":"req-420","action":"job_log","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","offset":5,"length":20}',
        '{"request_id":"req-421","action":"list_services","project":"demo"}',
        '{"request_id":"req-422","action":"service_status","project":"demo","service":"web"}',
        '{"request_id":"req-423","action":"start_service","project":"demo","service":"web"}',
        '{"request_id":"req-424","action":"stop_service","project":"demo","service":"web"}',
        '{"request_id":"req-425","action":"restart_service","project":"demo","service":"web"}',
        '{"request_id":"req-426","action":"list_backups","project":"demo","limit":10}',
        '{"request_id":"req-427","action":"backup_database","project":"demo"}',
        '{"request_id":"req-428","action":"request_action_approval","project":"demo","operation":"deploy"}',
        '{"request_id":"req-429","action":"approval_status","approval_id":"cccccccccccccccccccccccccccccccc"}',
        '{"request_id":"req-430","action":"migration_status","project":"demo"}',
        '{"request_id":"req-431","action":"apply_migrations","project":"demo","approval_id":"dddddddddddddddddddddddddddddddd"}',
        '{"request_id":"req-432","action":"plan_deploy","project":"demo"}',
        '{"request_id":"req-433","action":"deploy_staging","project":"demo","approval_id":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}',
        '{"request_id":"req-434","action":"deployment_status","job_id":"ffffffffffffffffffffffffffffffff"}',
        '{"request_id":"req-435","action":"list_releases","project":"demo","limit":12}',
        '{"request_id":"req-436","action":"rollback_plan","project":"demo"}',
        '{"request_id":"req-437","action":"rollback_release","project":"demo","approval_id":"11111111111111111111111111111111"}',
        '{"request_id":"req-438","action":"rollback_status","job_id":"22222222222222222222222222222222"}',
        '{"request_id":"req-439","action":"runtime_status"}',
        '{"request_id":"req-440","action":"self_update","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
        '{"request_id":"req-441","action":"self_update_status","job_id":"33333333333333333333333333333333"}',
    ]

    for payload in payloads:
        assert processor.process(payload).state == BridgeProcessState.COMPLETED

    assert [name for name, _args in executor.calls] == [
        "list_projects",
        "safety_status",
        "project_status",
        "project_capabilities",
        "list_test_profiles",
        "sync_project",
        "run_tests",
        "queue_status",
        "worker_status",
        "job_status",
        "cancel_job",
        "job_log",
        "list_services",
        "service_status",
        "start_service",
        "stop_service",
        "restart_service",
        "list_backups",
        "backup_database",
        "request_action_approval",
        "approval_status",
        "migration_status",
        "apply_migrations",
        "plan_deploy",
        "deploy_staging",
        "deployment_status",
        "list_releases",
        "rollback_plan",
        "rollback_release",
        "rollback_status",
        "runtime_status",
        "self_update",
        "self_update_status",
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



def test_sync_project_dispatches_only_project_and_commit(tmp_path) -> None:
    executor = FakeExecutor()
    processor = _processor(tmp_path, executor=executor)
    commit = "b" * 40

    outcome = processor.process(
        json.dumps(
            {
                "request_id": "req-sync-001",
                "action": "sync_project",
                "project": "demo",
                "commit": commit,
            }
        )
    )

    assert outcome.state == BridgeProcessState.COMPLETED
    assert executor.calls == [("sync_project", ("demo", commit))]
