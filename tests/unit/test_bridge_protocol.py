import json

import pytest

from runner_mcp.bridge_protocol import (
    MAX_BRIDGE_REQUEST_BYTES,
    BridgeProtocolError,
    BridgeRequest,
    bridge_tool_call,
    parse_bridge_request,
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
            ("run_tests", {"project": "demo", "profile": "unit"}),
        ),
    ],
)
def test_bridge_request_maps_only_to_allow_listed_tool_calls(
    payload: dict[str, object],
    expected: tuple[str, dict[str, str]],
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
