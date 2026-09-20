import json

import pytest

from runner_mcp.completion_feedback import (
    MAX_COMPLETION_EVENT_BYTES,
    CompletionEvent,
    CompletionFeedbackError,
    CompletionOperation,
    CompletionSource,
    CompletionState,
    completion_event_id,
    completion_notification_marker,
    make_completion_event,
    parse_completion_event,
    safe_completion_label,
    serialize_completion_event,
)


def test_completion_event_id_is_deterministic_and_source_scoped() -> None:
    left = completion_event_id(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-001",
    )
    right = completion_event_id(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-001",
    )
    other = completion_event_id(
        source=CompletionSource.TEST_JOB,
        source_id="req-001",
    )

    assert left == right
    assert left != other
    assert len(left) == 32


def test_run_tests_completion_round_trips() -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-002",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )

    encoded = serialize_completion_event(event)
    parsed = parse_completion_event(encoded)

    assert parsed == event
    assert parsed.requires_attention is False
    assert safe_completion_label(parsed) == "demo / unit: succeeded"


@pytest.mark.parametrize(
    ("state", "requires_attention"),
    [
        (CompletionState.SUCCEEDED, False),
        (CompletionState.FAILED, True),
        (CompletionState.CANCELLED, True),
    ],
)
def test_terminal_state_controls_attention(
    state: CompletionState,
    requires_attention: bool,
) -> None:
    event = make_completion_event(
        source=CompletionSource.TEST_JOB,
        source_id=f"job-{state.value}",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=state,
    )

    assert event.requires_attention is requires_attention
    assert json.loads(serialize_completion_event(event))["requires_attention"] is requires_attention


def test_non_test_completion_rejects_profile() -> None:
    with pytest.raises(CompletionFeedbackError, match="only run_tests"):
        make_completion_event(
            source=CompletionSource.DEPLOYMENT_JOB,
            source_id="job-001",
            operation=CompletionOperation.DEPLOY_STAGING,
            project="demo",
            profile="unit",
            state=CompletionState.SUCCEEDED,
        )


def test_run_tests_completion_requires_profile() -> None:
    with pytest.raises(CompletionFeedbackError, match="requires profile"):
        make_completion_event(
            source=CompletionSource.TEST_JOB,
            source_id="job-002",
            operation=CompletionOperation.RUN_TESTS,
            project="demo",
            state=CompletionState.FAILED,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", "../req"),
        ("source_id", "/private/path"),
        ("project", "../demo"),
        ("project", "https://private.invalid"),
        ("profile", "unit;unsafe"),
    ],
)
def test_identifiers_reject_private_or_unsafe_shapes(field: str, value: str) -> None:
    kwargs = {
        "source": CompletionSource.MAILBOX_RESULT,
        "source_id": "req-003",
        "operation": CompletionOperation.RUN_TESTS,
        "project": "demo",
        "profile": "unit",
        "state": CompletionState.SUCCEEDED,
    }
    kwargs[field] = value

    with pytest.raises(CompletionFeedbackError):
        make_completion_event(**kwargs)


def test_notification_marker_is_stable_and_contains_no_project_details() -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-004",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )

    marker = completion_notification_marker(event)

    assert marker == completion_notification_marker(event)
    assert event.event_id in marker
    assert "demo" not in marker
    assert "unit" not in marker


def test_unknown_fields_fail_closed() -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-005",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )
    raw = event.public_payload()
    raw["path"] = "/private/location"

    with pytest.raises(CompletionFeedbackError, match="unknown fields"):
        parse_completion_event(json.dumps(raw))


def test_duplicate_json_keys_fail_closed() -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-006",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )
    payload = serialize_completion_event(event).replace(
        '"state":"succeeded"',
        '"state":"succeeded","state":"failed"',
    )

    with pytest.raises(CompletionFeedbackError, match="duplicate JSON keys"):
        parse_completion_event(payload)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_standard_json_constants_fail_closed(constant: str) -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-007",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )
    payload = event.public_payload()
    text = json.dumps(payload).replace('"event_version": 1', f'"event_version": {constant}')

    with pytest.raises(CompletionFeedbackError, match="non-standard JSON constant"):
        parse_completion_event(text)


def test_requires_attention_is_not_client_controlled() -> None:
    event = make_completion_event(
        source=CompletionSource.MAILBOX_RESULT,
        source_id="req-008",
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.FAILED,
    )
    raw = event.public_payload()
    raw["requires_attention"] = False

    with pytest.raises(CompletionFeedbackError, match="does not match state"):
        parse_completion_event(json.dumps(raw))


def test_event_size_is_bounded() -> None:
    payload = b"{" + (b" " * MAX_COMPLETION_EVENT_BYTES) + b"}"

    with pytest.raises(CompletionFeedbackError, match="size limit"):
        parse_completion_event(payload)


def test_event_constructor_rejects_forged_event_id() -> None:
    with pytest.raises(CompletionFeedbackError, match="event_id"):
        CompletionEvent(
            event_id="not-a-valid-event-id",
            source=CompletionSource.TEST_JOB,
            operation=CompletionOperation.RUN_TESTS,
            project="demo",
            profile="unit",
            state=CompletionState.SUCCEEDED,
        )


def test_source_and_operation_must_match() -> None:
    with pytest.raises(CompletionFeedbackError, match="do not match"):
        make_completion_event(
            source=CompletionSource.TEST_JOB,
            source_id="job-mismatch",
            operation=CompletionOperation.DEPLOY_STAGING,
            project="demo",
            state=CompletionState.SUCCEEDED,
        )
