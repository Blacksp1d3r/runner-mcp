import json
import stat

import pytest

from runner_mcp.bridge_protocol import parse_bridge_request
from runner_mcp.bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayDecision,
    bridge_request_fingerprint,
)


def test_new_request_is_claimed_once(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-201","action":"project_status","project":"demo"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    first = ledger.claim(request)
    second = ledger.claim(request)

    assert first.decision == ReplayDecision.NEW
    assert second.decision == ReplayDecision.DUPLICATE
    assert first.fingerprint == second.fingerprint


def test_request_id_reuse_with_changed_content_fails_closed(tmp_path) -> None:
    first = parse_bridge_request(
        '{"request_id":"req-202","action":"project_status","project":"demo"}'
    )
    changed = parse_bridge_request(
        '{"request_id":"req-202","action":"project_status","project":"other"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    assert ledger.claim(first).decision == ReplayDecision.NEW
    with pytest.raises(BridgeReplayError, match="different request"):
        ledger.claim(changed)


def test_fingerprint_is_stable_for_equivalent_requests() -> None:
    left = parse_bridge_request(
        '{"request_id":"req-203","action":"run_tests","project":"demo","profile":"unit"}'
    )
    right = parse_bridge_request(
        '{"profile":"unit","project":"demo","action":"run_tests","request_id":"req-203"}'
    )

    assert bridge_request_fingerprint(left) == bridge_request_fingerprint(right)


def test_ledger_stores_only_safe_request_metadata(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-204","action":"run_tests","project":"demo","profile":"unit"}'
    )
    path = tmp_path / "replay.json"
    ledger = BridgeReplayLedger(path)

    ledger.claim(request)
    stored = json.loads(path.read_text(encoding="utf-8"))

    assert set(stored["req-204"]) == {"fingerprint", "action", "seen_at"}
    assert stored["req-204"]["action"] == "run_tests"
    assert "demo" not in path.read_text(encoding="utf-8")
    assert "unit" not in path.read_text(encoding="utf-8")


def test_ledger_file_permissions_are_restrictive(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-205","action":"list_projects"}'
    )
    path = tmp_path / "replay.json"

    BridgeReplayLedger(path).claim(request)

    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600


def test_ledger_requires_existing_parent_directory(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-206","action":"list_projects"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "missing" / "replay.json")

    with pytest.raises(BridgeReplayError, match="parent directory"):
        ledger.claim(request)


def test_corrupt_ledger_fails_closed(tmp_path) -> None:
    path = tmp_path / "replay.json"
    path.write_text("{not-json", encoding="utf-8")
    request = parse_bridge_request(
        '{"request_id":"req-207","action":"list_projects"}'
    )

    with pytest.raises(BridgeReplayError, match="not valid JSON"):
        BridgeReplayLedger(path).claim(request)


def test_ledger_capacity_fails_closed(tmp_path) -> None:
    ledger = BridgeReplayLedger(tmp_path / "replay.json", max_entries=1)
    first = parse_bridge_request(
        '{"request_id":"req-208","action":"list_projects"}'
    )
    second = parse_bridge_request(
        '{"request_id":"req-209","action":"safety_status"}'
    )

    assert ledger.claim(first).decision == ReplayDecision.NEW
    with pytest.raises(BridgeReplayError, match="capacity"):
        ledger.claim(second)


def test_invalid_max_entries_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="positive"):
        BridgeReplayLedger(tmp_path / "replay.json", max_entries=0)
