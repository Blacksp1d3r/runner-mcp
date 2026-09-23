import json

import pytest

from runner_mcp.bridge_processor import BridgeProcessor
from runner_mcp.bridge_protocol import (
    MAX_BRIDGE_REQUEST_BYTES,
    MAX_BRIDGE_RESULT_BYTES,
    BridgeAction,
    BridgeProtocolError,
    BridgeRequest,
    BridgeResult,
    BridgeResultState,
    bridge_tool_call,
    parse_bridge_request,
    parse_bridge_result,
    sanitize_bridge_result_data,
    serialize_bridge_result,
)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {"request_id": "req-001", "action": "list_projects"},
            ("list_projects", {}),
        ),
        (
            {"request_id": "req-002", "action": "safety_status"},
            ("safety_status", {}),
        ),
        (
            {"request_id": "req-runtime-01", "action": "runtime_status"},
            ("runtime_status", {}),
        ),
        (
            {"request_id": "req-runtime-02", "action": "runtime_doctor"},
            ("runtime_doctor", {}),
        ),
        (
            {
                "request_id": "req-003",
                "action": "project_status",
                "project": "demo",
            },
            ("project_status", {"project": "demo"}),
        ),
        (
            {
                "request_id": "req-004",
                "action": "project_capabilities",
                "project": "demo",
            },
            ("project_capabilities", {"project": "demo"}),
        ),
        (
            {
                "request_id": "req-005",
                "action": "list_test_profiles",
                "project": "demo",
            },
            ("list_test_profiles", {"project": "demo"}),
        ),
        (
            {
                "request_id": "req-006",
                "action": "run_tests",
                "project": "demo",
                "profile": "unit",
            },
            ("run_tests", {"project": "demo", "suite": "unit"}),
        ),
        (
            {"request_id": "req-007", "action": "queue_status"},
            ("queue_status", {}),
        ),
        (
            {"request_id": "req-008", "action": "worker_status"},
            ("worker_status", {}),
        ),
        (
            {
                "request_id": "req-009",
                "action": "job_status",
                "job_id": "a" * 32,
            },
            ("job_status", {"job_id": "a" * 32}),
        ),
        (
            {
                "request_id": "req-010",
                "action": "cancel_job",
                "job_id": "b" * 32,
            },
            ("cancel_job", {"job_id": "b" * 32}),
        ),
    ],
)
def test_bridge_request_maps_only_to_allow_listed_tool_calls(
    payload: dict[str, object],
    expected: tuple[str, dict[str, str | int]],
) -> None:
    request = parse_bridge_request(json.dumps(payload))
    assert bridge_tool_call(request) == expected


def test_unknown_action_is_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(
            '{"request_id":"req-001","action":"arbitrary_shell"}'
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(
            '{"request_id":"req-001","action":"run_tests",'
            '"project":"demo","profile":"unit","command":"rm -rf /"}'
        )


@pytest.mark.parametrize(
    "payload",
    [
        '{"request_id":"req-001","action":"list_projects","project":"demo"}',
        '{"request_id":"req-001","action":"project_status"}',
        '{"request_id":"req-001","action":"project_status","project":"demo","profile":"unit"}',
        '{"request_id":"req-001","action":"run_tests","project":"demo"}',
        '{"request_id":"req-001","action":"run_tests","profile":"unit"}',
        '{"request_id":"req-001","action":"queue_status","project":"demo"}',
        '{"request_id":"req-001","action":"runtime_status","project":"demo"}',
        '{"request_id":"req-001","action":"runtime_doctor","limit":2}',
        '{"request_id":"req-001","action":"job_status"}',
        '{"request_id":"req-001","action":"job_status","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","project":"demo"}',
        '{"request_id":"req-001","action":"cancel_job","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","profile":"unit"}',
    ],
)
def test_action_specific_arguments_fail_closed(payload: str) -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(payload)


@pytest.mark.parametrize(
    "payload",
    [
        '{"request_id":"../bad","action":"list_projects"}',
        '{"request_id":"req-001","action":"project_status","project":"../demo"}',
        '{"request_id":"req-001","action":"run_tests","project":"demo","profile":"unit;unsafe"}',
        '{"request_id":"req-001","action":"job_status","job_id":"../bad"}',
    ],
)
def test_identifiers_use_safe_shapes(payload: str) -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(payload)


def test_duplicate_json_keys_are_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="duplicate JSON keys"):
        parse_bridge_request(
            '{"request_id":"req-001","action":"list_projects","action":"run_tests"}'
        )


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="JSON object"):
        parse_bridge_request('["list_projects"]')


def test_request_size_is_bounded() -> None:
    payload = b"{" + b" " * MAX_BRIDGE_REQUEST_BYTES + b"}"
    with pytest.raises(BridgeProtocolError, match="size limit"):
        parse_bridge_request(payload)


def test_model_rejects_extra_fields_even_without_json_parser() -> None:
    with pytest.raises(ValueError):
        BridgeRequest.model_validate(
            {
                "request_id": "req-001",
                "action": "list_projects",
                "executable": "/bin/sh",
            }
        )


def test_completed_result_round_trips_with_safe_data() -> None:
    result = BridgeResult.model_validate(
        {
            "request_id": "req-101",
            "action": "project_status",
            "state": "completed",
            "data": {"project": "demo", "healthy": True, "count": 3},
            "summary": "Project status collected",
        }
    )

    encoded = serialize_bridge_result(result)
    parsed = parse_bridge_result(encoded)

    assert parsed == result
    assert len(encoded.encode("utf-8")) <= MAX_BRIDGE_RESULT_BYTES


def test_failed_result_requires_safe_error_code_and_no_data() -> None:
    with pytest.raises(ValueError):
        BridgeResult.model_validate(
            {
                "request_id": "req-102",
                "action": "run_tests",
                "state": "failed",
                "summary": "Test failed",
            }
        )

    with pytest.raises(ValueError):
        BridgeResult.model_validate(
            {
                "request_id": "req-102",
                "action": "run_tests",
                "state": "failed",
                "error_code": "TEST_FAILED",
                "data": {"details": "must not be returned"},
            }
        )


def test_result_unknown_fields_fail_closed() -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_result(
            '{"request_id":"req-103","action":"list_projects",'
            '"state":"completed","private_path":"/srv/private"}'
        )


def test_result_duplicate_keys_fail_closed() -> None:
    with pytest.raises(BridgeProtocolError, match="duplicate JSON keys"):
        parse_bridge_result(
            '{"request_id":"req-104","action":"list_projects",'
            '"state":"completed","state":"failed"}'
        )


def test_result_data_redacts_sensitive_keys_and_private_locations() -> None:
    safe = sanitize_bridge_result_data(
        {
            "project": "demo",
            "token": "super-secret",
            "nested": {
                "endpoint": "https://private.example.invalid/api",
                "details": "/private/location",
                "repository": "owner/project",
                "community": "self-hosted",
            },
        }
    )

    assert safe == {
        "project": "demo",
        "token": "[redacted]",
        "nested": {
            "endpoint": "[redacted]",
            "details": "[redacted]",
            "repository": "owner/project",
            "community": "self-hosted",
        },
    }


def test_result_data_rejects_unsupported_types() -> None:
    with pytest.raises(BridgeProtocolError, match="unsupported value type"):
        sanitize_bridge_result_data({"raw": object()})


def test_result_size_is_bounded_after_serialization() -> None:
    result = BridgeResult.model_validate(
        {
            "request_id": "req-105",
            "action": "list_projects",
            "state": "completed",
            "data": {"items": ["x" * 2_048] * 20},
        }
    )

    with pytest.raises(BridgeProtocolError, match="size limit"):
        serialize_bridge_result(result)


def test_result_summary_rejects_control_characters() -> None:
    with pytest.raises(ValueError):
        BridgeResult.model_validate(
            {
                "request_id": "req-106",
                "action": "list_projects",
                "state": "completed",
                "summary": "line one\nline two",
            }
        )


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_standard_json_numbers_are_rejected(constant: str) -> None:
    with pytest.raises(BridgeProtocolError, match="non-standard JSON constant"):
        parse_bridge_result(
            '{"request_id":"req-107","action":"list_projects",'
            '"state":"completed","data":{"value":' + constant + '}}'
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_result_sanitizer_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(BridgeProtocolError, match="non-finite number"):
        sanitize_bridge_result_data({"value": value})


def test_run_tests_bridge_translates_public_profile_to_runner_suite() -> None:
    request = parse_bridge_request(
        '{"request_id":"req-suite-map","action":"run_tests","project":"demo","profile":"unit"}'
    )

    tool_name, arguments = bridge_tool_call(request)

    assert tool_name == "run_tests"
    assert arguments == {"project": "demo", "suite": "unit"}
    assert "profile" not in arguments


def test_bridge_result_serialization_normalizes_unknown_types() -> None:
    result = BridgeResult.model_construct(
        request_id="req-serialization",
        action=BridgeAction.LIST_PROJECTS,
        state=BridgeResultState.COMPLETED,
        data={"result": object()},
        error_code=None,
        summary=None,
    )

    with pytest.raises(BridgeProtocolError, match="unsupported value type"):
        serialize_bridge_result(result)



def test_sync_project_requires_full_commit_and_maps_safely() -> None:
    commit = "a" * 40
    request = parse_bridge_request(
        json.dumps(
            {
                "request_id": "sync-001",
                "action": "sync_project",
                "project": "demo",
                "commit": commit,
            }
        )
    )
    assert bridge_tool_call(request) == (
        "sync_project",
        {"project": "demo", "commit": commit},
    )


@pytest.mark.parametrize(
    "payload",
    [
        '{"request_id":"sync-002","action":"sync_project","project":"demo"}',
        '{"request_id":"sync-003","action":"sync_project","project":"demo","commit":"main"}',
        '{"request_id":"sync-004","action":"sync_project","project":"demo","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","profile":"pytest"}',
        '{"request_id":"sync-005","action":"run_tests","project":"demo","profile":"pytest","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
    ],
)
def test_sync_and_test_requests_reject_extra_or_unpinned_input(payload: str) -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(payload)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "request_id": "ops-001",
                "action": "job_log",
                "job_id": "a" * 32,
                "offset": 10,
                "length": 25,
            },
            ("job_log", {"job_id": "a" * 32, "offset": 10, "length": 25}),
        ),
        (
            {
                "request_id": "ops-002",
                "action": "service_status",
                "project": "demo",
                "service": "web",
            },
            ("service_status", {"project": "demo", "service": "web"}),
        ),
        (
            {
                "request_id": "ops-003",
                "action": "list_backups",
                "project": "demo",
                "limit": 20,
            },
            ("list_backups", {"project": "demo", "limit": 20}),
        ),
        (
            {
                "request_id": "ops-004",
                "action": "request_action_approval",
                "project": "demo",
                "operation": "code_rollback",
            },
            (
                "request_action_approval",
                {"project": "demo", "action": "code_rollback"},
            ),
        ),
        (
            {
                "request_id": "ops-005",
                "action": "deploy_staging",
                "project": "demo",
                "approval_id": "b" * 32,
            },
            (
                "deploy_staging",
                {"project": "demo", "approval_id": "b" * 32},
            ),
        ),
        (
            {
                "request_id": "ops-006",
                "action": "deployment_status",
                "job_id": "c" * 32,
            },
            ("deployment_status", {"job_id": "c" * 32}),
        ),
        (
            {
                "request_id": "ops-007",
                "action": "list_releases",
                "project": "demo",
            },
            ("list_releases", {"project": "demo"}),
        ),
    ],
)
def test_operational_bridge_maps_only_bounded_arguments(
    payload: dict[str, object],
    expected: tuple[str, dict[str, str | int]],
) -> None:
    request = parse_bridge_request(json.dumps(payload))
    assert bridge_tool_call(request) == expected


@pytest.mark.parametrize(
    "payload",
    [
        '{"request_id":"ops-bad-01","action":"job_log","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","length":101}',
        '{"request_id":"ops-bad-02","action":"job_log","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","offset":-1}',
        '{"request_id":"ops-bad-03","action":"service_status","project":"demo","service":"../web"}',
        '{"request_id":"ops-bad-04","action":"restart_service","project":"demo","service":"web","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
        '{"request_id":"ops-bad-05","action":"request_action_approval","project":"demo","operation":"shell"}',
        '{"request_id":"ops-bad-06","action":"approval_status","approval_id":"not-an-id"}',
        '{"request_id":"ops-bad-07","action":"apply_migrations","project":"demo","approval_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","operation":"migration"}',
        '{"request_id":"ops-bad-08","action":"list_backups","project":"demo","limit":101}',
        '{"request_id":"ops-bad-09","action":"deploy_staging","project":"demo"}',
    ],
)
def test_operational_bridge_rejects_unbounded_or_extra_arguments(payload: str) -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(payload)

@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "request_id": "self-002",
                "action": "self_update",
                "commit": "a" * 40,
            },
            ("self_update", {"commit": "a" * 40}),
        ),
        (
            {
                "request_id": "self-003",
                "action": "self_update_status",
                "job_id": "b" * 32,
            },
            ("self_update_status", {"job_id": "b" * 32}),
        ),
    ],
)
def test_self_operations_map_only_fixed_arguments(
    payload: dict[str, object],
    expected: tuple[str, dict[str, str | int]],
) -> None:
    assert bridge_tool_call(parse_bridge_request(json.dumps(payload))) == expected


@pytest.mark.parametrize(
    "payload",
    [
        '{"request_id":"self-bad-02","action":"self_update","commit":"main"}',
        '{"request_id":"self-bad-03","action":"self_update","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","project":"runner-mcp"}',
        '{"request_id":"self-bad-04","action":"self_update_status","job_id":"bad"}',
        '{"request_id":"self-bad-05","action":"self_update_status","job_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","commit":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}',
        '{"request_id":"self-bad-06","action":"self_update","commit":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}',
    ],
)
def test_self_operations_reject_extra_or_unpinned_input(payload: str) -> None:
    with pytest.raises(BridgeProtocolError, match="strict validation"):
        parse_bridge_request(payload)


# Exhaustive fail-closed matrix from Task 16's adversarial protocol review.
_VALID_REQUEST_BY_ACTION: dict[BridgeAction, dict[str, object]] = {
    BridgeAction.LIST_PROJECTS: {
        "request_id": "matrix-list-projects",
        "action": "list_projects",
    },
    BridgeAction.SAFETY_STATUS: {
        "request_id": "matrix-safety-status",
        "action": "safety_status",
    },
    BridgeAction.PROJECT_STATUS: {
        "request_id": "matrix-project-status",
        "action": "project_status",
        "project": "demo",
    },
    BridgeAction.PROJECT_CAPABILITIES: {
        "request_id": "matrix-project-capabilities",
        "action": "project_capabilities",
        "project": "demo",
    },
    BridgeAction.SYNC_PROJECT: {
        "request_id": "matrix-sync-project",
        "action": "sync_project",
        "project": "demo",
        "commit": "a" * 40,
    },
    BridgeAction.LIST_TEST_PROFILES: {
        "request_id": "matrix-list-test-profiles",
        "action": "list_test_profiles",
        "project": "demo",
    },
    BridgeAction.RUN_TESTS: {
        "request_id": "matrix-run-tests",
        "action": "run_tests",
        "project": "demo",
        "profile": "unit",
    },
    BridgeAction.QUEUE_STATUS: {
        "request_id": "matrix-queue-status",
        "action": "queue_status",
    },
    BridgeAction.WORKER_STATUS: {
        "request_id": "matrix-worker-status",
        "action": "worker_status",
    },
    BridgeAction.JOB_STATUS: {
        "request_id": "matrix-job-status",
        "action": "job_status",
        "job_id": "1" * 32,
    },
    BridgeAction.CANCEL_JOB: {
        "request_id": "matrix-cancel-job",
        "action": "cancel_job",
        "job_id": "2" * 32,
    },
    BridgeAction.JOB_LOG: {
        "request_id": "matrix-job-log",
        "action": "job_log",
        "job_id": "3" * 32,
    },
    BridgeAction.LIST_SERVICES: {
        "request_id": "matrix-list-services",
        "action": "list_services",
        "project": "demo",
    },
    BridgeAction.SERVICE_STATUS: {
        "request_id": "matrix-service-status",
        "action": "service_status",
        "project": "demo",
        "service": "web",
    },
    BridgeAction.START_SERVICE: {
        "request_id": "matrix-start-service",
        "action": "start_service",
        "project": "demo",
        "service": "web",
    },
    BridgeAction.STOP_SERVICE: {
        "request_id": "matrix-stop-service",
        "action": "stop_service",
        "project": "demo",
        "service": "web",
    },
    BridgeAction.RESTART_SERVICE: {
        "request_id": "matrix-restart-service",
        "action": "restart_service",
        "project": "demo",
        "service": "web",
    },
    BridgeAction.LIST_BACKUPS: {
        "request_id": "matrix-list-backups",
        "action": "list_backups",
        "project": "demo",
    },
    BridgeAction.BACKUP_DATABASE: {
        "request_id": "matrix-backup-database",
        "action": "backup_database",
        "project": "demo",
    },
    BridgeAction.REQUEST_ACTION_APPROVAL: {
        "request_id": "matrix-request-approval",
        "action": "request_action_approval",
        "project": "demo",
        "operation": "deploy",
    },
    BridgeAction.APPROVAL_STATUS: {
        "request_id": "matrix-approval-status",
        "action": "approval_status",
        "approval_id": "4" * 32,
    },
    BridgeAction.MIGRATION_STATUS: {
        "request_id": "matrix-migration-status",
        "action": "migration_status",
        "project": "demo",
    },
    BridgeAction.APPLY_MIGRATIONS: {
        "request_id": "matrix-apply-migrations",
        "action": "apply_migrations",
        "project": "demo",
        "approval_id": "5" * 32,
    },
    BridgeAction.PLAN_DEPLOY: {
        "request_id": "matrix-plan-deploy",
        "action": "plan_deploy",
        "project": "demo",
    },
    BridgeAction.DEPLOY_STAGING: {
        "request_id": "matrix-deploy-staging",
        "action": "deploy_staging",
        "project": "demo",
        "approval_id": "6" * 32,
    },
    BridgeAction.DEPLOYMENT_STATUS: {
        "request_id": "matrix-deployment-status",
        "action": "deployment_status",
        "job_id": "7" * 32,
    },
    BridgeAction.LIST_RELEASES: {
        "request_id": "matrix-list-releases",
        "action": "list_releases",
        "project": "demo",
    },
    BridgeAction.ROLLBACK_PLAN: {
        "request_id": "matrix-rollback-plan",
        "action": "rollback_plan",
        "project": "demo",
    },
    BridgeAction.ROLLBACK_RELEASE: {
        "request_id": "matrix-rollback-release",
        "action": "rollback_release",
        "project": "demo",
        "approval_id": "8" * 32,
    },
    BridgeAction.ROLLBACK_STATUS: {
        "request_id": "matrix-rollback-status",
        "action": "rollback_status",
        "job_id": "9" * 32,
    },
    BridgeAction.RUNTIME_STATUS: {
        "request_id": "matrix-runtime-status",
        "action": "runtime_status",
    },
    BridgeAction.RUNTIME_DOCTOR: {
        "request_id": "matrix-runtime-doctor",
        "action": "runtime_doctor",
    },
    BridgeAction.SELF_UPDATE: {
        "request_id": "matrix-self-update",
        "action": "self_update",
        "commit": "b" * 40,
    },
    BridgeAction.SELF_UPDATE_STATUS: {
        "request_id": "matrix-self-update-status",
        "action": "self_update_status",
        "job_id": "a" * 32,
    },
}

_OPTIONAL_FIELD_VALUES: dict[str, object] = {
    "project": "other",
    "profile": "smoke",
    "commit": "c" * 40,
    "job_id": "b" * 32,
    "service": "api",
    "approval_id": "c" * 32,
    "operation": "migration",
    "offset": 1,
    "length": 1,
    "limit": 1,
}


def _owned_optional_fields(
    action: BridgeAction,
    payload: dict[str, object],
) -> set[str]:
    owned = set(payload) & set(_OPTIONAL_FIELD_VALUES)
    if action == BridgeAction.JOB_LOG:
        owned.update({"offset", "length"})
    if action in {BridgeAction.LIST_BACKUPS, BridgeAction.LIST_RELEASES}:
        owned.add("limit")
    return owned


_NON_OWNED_FIELD_CASES = [
    (action, field)
    for action, payload in _VALID_REQUEST_BY_ACTION.items()
    for field in _OPTIONAL_FIELD_VALUES
    if field not in _owned_optional_fields(action, payload)
]

_VALID_ACTION_VALUES = {action.value for action in BridgeAction}
_ACTION_VARIANT_CASES = [
    (action, variant)
    for action in BridgeAction
    for variant in {
        action.value.upper(),
        action.value.replace("_", "-"),
        action.value[:-1],
    }
    if variant not in _VALID_ACTION_VALUES
]


class _InvocationCounterExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def __getattr__(self, _name: str):
        def invoke(*_args: object, **_kwargs: object) -> dict[str, object]:
            self.calls += 1
            return {}

        return invoke


class _UnexpectedLedger:
    def claim(self, _request: BridgeRequest):
        raise AssertionError("invalid request reached replay ledger")


class _UnexpectedSink:
    def persist_result(self, _request_id: str, _result_json: str) -> None:
        raise AssertionError("invalid request reached result sink")


def _assert_rejected_before_execution(
    payload: str,
    *,
    match: str = "strict validation",
) -> None:
    executor = _InvocationCounterExecutor()
    processor = BridgeProcessor(
        ledger=_UnexpectedLedger(),
        executor=executor,
        result_sink=_UnexpectedSink(),
    )

    with pytest.raises(BridgeProtocolError, match=match):
        processor.process(payload)

    assert executor.calls == 0


def test_adversarial_matrix_has_valid_fixture_for_every_bridge_action() -> None:
    assert set(_VALID_REQUEST_BY_ACTION) == set(BridgeAction)

    for action, payload in _VALID_REQUEST_BY_ACTION.items():
        request = parse_bridge_request(json.dumps(payload))
        assert request.action == action
        tool_name, _arguments = bridge_tool_call(request)
        assert tool_name == action.value


@pytest.mark.parametrize(("action", "field"), _NON_OWNED_FIELD_CASES)
def test_every_action_rejects_every_non_owned_optional_field_before_execution(
    action: BridgeAction,
    field: str,
) -> None:
    payload = dict(_VALID_REQUEST_BY_ACTION[action])
    payload[field] = _OPTIONAL_FIELD_VALUES[field]

    _assert_rejected_before_execution(json.dumps(payload))


@pytest.mark.parametrize(("action", "variant"), _ACTION_VARIANT_CASES)
def test_action_case_hyphen_and_prefix_variants_fail_before_execution(
    action: BridgeAction,
    variant: str,
) -> None:
    payload = dict(_VALID_REQUEST_BY_ACTION[action])
    payload["action"] = variant

    _assert_rejected_before_execution(json.dumps(payload))


@pytest.mark.parametrize("field", ["command", "cwd", "env"])
def test_unknown_execution_shaping_fields_fail_before_execution(field: str) -> None:
    payload: dict[str, object] = {
        "request_id": f"matrix-extra-{field}",
        "action": "list_projects",
        field: {"TOKEN": "secret"} if field == "env" else "/srv/private",
    }

    _assert_rejected_before_execution(json.dumps(payload))


def test_duplicate_request_id_fails_before_execution() -> None:
    _assert_rejected_before_execution(
        '{"request_id":"matrix-dup-a","request_id":"matrix-dup-b",'
        '"action":"list_projects"}',
        match="duplicate JSON keys",
    )


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_request_non_standard_json_constants_fail_before_execution(
    constant: str,
) -> None:
    _assert_rejected_before_execution(
        '{"request_id":"matrix-constant","action":"job_log",'
        '"job_id":"dddddddddddddddddddddddddddddddd","offset":'
        + constant
        + "}",
        match="non-standard JSON constant",
    )


def test_uppercase_self_update_commit_fails_before_execution() -> None:
    payload = dict(_VALID_REQUEST_BY_ACTION[BridgeAction.SELF_UPDATE])
    payload["commit"] = "A" * 40

    _assert_rejected_before_execution(json.dumps(payload))
