import json
import stat

import pytest

from runner_mcp.bridge_protocol import parse_bridge_request
from runner_mcp.bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayDecision,
    ReplayState,
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
    assert first.state == ReplayState.CLAIMED
    assert second.decision == ReplayDecision.DUPLICATE
    assert second.state == ReplayState.CLAIMED
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

    assert set(stored["req-204"]) == {"fingerprint", "action", "state", "seen_at"}
    assert stored["req-204"]["action"] == "run_tests"
    assert stored["req-204"]["state"] == "claimed"
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


def test_ledger_symlink_is_rejected(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    path = tmp_path / "replay.json"
    path.symlink_to(target)
    request = parse_bridge_request(
        '{"request_id":"req-210","action":"list_projects"}'
    )

    with pytest.raises(BridgeReplayError, match="could not be opened"):
        BridgeReplayLedger(path).claim(request)

    assert target.read_text(encoding="utf-8") == "{}"


def test_ledger_rejects_tampered_entry(tmp_path) -> None:
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            {
                "req-211": {
                    "fingerprint": "not-a-sha256",
                    "action": "list_projects",
                    "seen_at": "2026-09-20T00:00:00+00:00",
                }
            }
        ),
        encoding="utf-8",
    )
    request = parse_bridge_request(
        '{"request_id":"req-212","action":"list_projects"}'
    )

    with pytest.raises(BridgeReplayError, match="invalid entry"):
        BridgeReplayLedger(path).claim(request)


def test_claim_complete_and_duplicate_preserve_completed_state(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-213","action":"run_tests","project":"demo","profile":"unit"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    claim = ledger.claim(request)
    completed = ledger.complete(request)
    duplicate = ledger.claim(request)

    assert claim.state == ReplayState.CLAIMED
    assert completed.state == ReplayState.COMPLETED
    assert completed.completed_at is not None
    assert duplicate.decision == ReplayDecision.DUPLICATE
    assert duplicate.state == ReplayState.COMPLETED


def test_complete_is_idempotent_without_changing_timestamp(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-214","action":"list_projects"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    ledger.claim(request)
    first = ledger.complete(request)
    second = ledger.complete(request)

    assert first == second


def test_complete_requires_prior_claim(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-215","action":"list_projects"}'
    )

    with pytest.raises(BridgeReplayError, match="must be claimed"):
        BridgeReplayLedger(tmp_path / "replay.json").complete(request)


def test_inspect_reports_lifecycle_without_mutation(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-216","action":"project_status","project":"demo"}'
    )
    ledger = BridgeReplayLedger(tmp_path / "replay.json")

    assert ledger.inspect(request) is None
    ledger.claim(request)
    claimed = ledger.inspect(request)
    assert claimed is not None
    assert claimed.state == ReplayState.CLAIMED
    assert claimed.completed_at is None

    ledger.complete(request)
    completed = ledger.inspect(request)
    assert completed is not None
    assert completed.state == ReplayState.COMPLETED
    assert completed.completed_at is not None


def test_legacy_entry_without_state_is_treated_as_claimed(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-217","action":"list_projects"}'
    )
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            {
                "req-217": {
                    "fingerprint": bridge_request_fingerprint(request),
                    "action": "list_projects",
                    "seen_at": "2026-09-20T00:00:00+00:00",
                }
            }
        ),
        encoding="utf-8",
    )

    record = BridgeReplayLedger(path).inspect(request)

    assert record is not None
    assert record.state == ReplayState.CLAIMED
    assert record.completed_at is None


def test_completed_entry_requires_completed_timestamp(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-218","action":"list_projects"}'
    )
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            {
                "req-218": {
                    "fingerprint": bridge_request_fingerprint(request),
                    "action": "list_projects",
                    "state": "completed",
                    "seen_at": "2026-09-20T00:00:00+00:00",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BridgeReplayError, match="lacks timestamp"):
        BridgeReplayLedger(path).inspect(request)


def test_replay_timestamps_must_include_timezone(tmp_path) -> None:
    request = parse_bridge_request(
        '{"request_id":"req-219","action":"list_projects"}'
    )
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            {
                "req-219": {
                    "fingerprint": bridge_request_fingerprint(request),
                    "action": "list_projects",
                    "state": "claimed",
                    "seen_at": "2026-09-20T00:00:00",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BridgeReplayError, match="timezone"):
        BridgeReplayLedger(path).inspect(request)
