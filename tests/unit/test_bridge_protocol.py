import json

import pytest

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

