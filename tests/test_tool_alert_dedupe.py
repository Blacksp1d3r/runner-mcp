from __future__ import annotations

import pytest

from runner_mcp.tool_alert_dedupe import (
    ToolMismatchObservation,
    summarize_tool_mismatch_alerts,
)
from runner_mcp.tool_identity_classifier import ToolIdentityReason as R

SCOPE_A = "a" * 64
SCOPE_B = "b" * 64


def _event(second: int, reason: R = R.SCHEMA_MISMATCH, scope: str = SCOPE_A,
           tool: str = "runtime-status") -> ToolMismatchObservation:
    return ToolMismatchObservation(scope, tool, reason, second)


def test_repeated_events_within_window_are_suppressed_and_counted():
    result = summarize_tool_mismatch_alerts([
        _event(100), _event(110), _event(119), _event(159), _event(160)
    ])
    assert len(result) == 2
    assert result[0]["suppressed_count"] == 3
    assert result[1]["suppressed_count"] == 0
    assert result[1]["first_seen_second"] == 160


def test_fresh_fault_after_recovery_is_not_silenced_by_prior_cooldown():
    results = summarize_tool_mismatch_alerts([
        _event(100), _event(110, reason=R.READY), _event(111),
    ])
    assert [row["first_seen_second"] for row in results] == [100, 111]
    assert [row["suppressed_count"] for row in results] == [0, 0]


def test_recovery_resets_all_reasons_only_for_that_scope_and_tool():
    results = summarize_tool_mismatch_alerts([
        _event(100, reason=R.SCHEMA_MISMATCH),
        _event(101, reason=R.VERSION_MISMATCH),
        _event(102, scope=SCOPE_B),
        _event(103, tool="runtime-doctor"),
        _event(104, reason=R.READY),
        _event(105, reason=R.VERSION_MISMATCH),
        _event(106, reason=R.SCHEMA_MISMATCH),
        _event(107, scope=SCOPE_B),
        _event(108, tool="runtime-doctor"),
    ])
    assert len(results) == 6
    assert [row["first_seen_second"] for row in results] == [
        100, 101, 102, 103, 105, 106,
    ]
    # The unrelated scope and tool remain suppressed within their windows.
    assert results[2]["suppressed_count"] == 1
    assert results[3]["suppressed_count"] == 1


def test_ready_only_episode_does_not_emit_new_alert():
    assert summarize_tool_mismatch_alerts([
        _event(100, reason=R.READY), _event(101, reason=R.READY),
    ]) == []


def test_different_host_scope_id_and_reason_cannot_collide():
    events = [
        _event(1, scope=SCOPE_A),
        _event(2, scope=SCOPE_B),
        _event(3, tool="runtime-doctor"),
        _event(4, reason=R.VERSION_MISMATCH),
    ]
    result = summarize_tool_mismatch_alerts(events)
    assert len(result) == 4
    assert all(row["suppressed_count"] == 0 for row in result)


def test_ready_is_ignored_and_no_side_effect_or_notification_sent():
    assert summarize_tool_mismatch_alerts([_event(1, reason=R.READY)]) == []


@pytest.mark.parametrize(
    "invalid",
    [
        [_event(5), _event(4)],
        [ToolMismatchObservation("bad-scope", "runtime-status", R.UNKNOWN_TOOL, 1)],
        [ToolMismatchObservation(SCOPE_A, "../private", R.UNKNOWN_TOOL, 1)],
        [ToolMismatchObservation(SCOPE_A, "runtime-status", "UNKNOWN_TOOL", 1)],
        [ToolMismatchObservation(SCOPE_A, "runtime-status", R.UNKNOWN_TOOL, True)],
        [ToolMismatchObservation(SCOPE_A, "runtime-status", R.UNKNOWN_TOOL, -1)],
        [None],
        "fake-events",
    ],
)
def test_invalid_or_sensitive_input_fails_closed(invalid):
    with pytest.raises(ValueError):
        summarize_tool_mismatch_alerts(invalid)


@pytest.mark.parametrize("bad", [0, 86401, -1, True, "60"])
def test_invalid_cooldown_is_denied(bad):
    with pytest.raises(ValueError):
        summarize_tool_mismatch_alerts([], cooldown_seconds=bad)


def test_maximum_observations_bound():
    assert len(summarize_tool_mismatch_alerts([_event(i) for i in range(1024)])) == 18
    with pytest.raises(ValueError):
        summarize_tool_mismatch_alerts([_event(i) for i in range(1025)])
