from __future__ import annotations

import pytest

from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.protected_release_mirror import ProtectedReleaseMirror

A = "a" * 40
B = "b" * 40


def make_case(tmp_path, *, pins=(A, B), ready=True, existing=(), primary_ok=True,
              secondary_ok=True, fail_on=None, stopped=False):
    stop = tmp_path / "stop"
    if stopped:
        stop.write_text("stop")
    safety = OperatorSafetyGuard(stop, RetentionPolicy(), retention_confirmed=True)
    calls = []
    def mirror(revision):
        calls.append(("mirror", revision))
        if revision == fail_on:
            raise RuntimeError("/private/mirror token=never-publish")
        return {"alreadyStored": revision in existing, "separateDevice": True}
    obj = ProtectedReleaseMirror(
        safety=safety,
        readiness=lambda: {
            "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
            "configurationState": "configured",
            "ready": ready,
            "primaryCustodyReady": True,
            "mountReady": True,
            "mirrorRootReady": True,
            "distinctDeviceReady": ready,
            "mutationEnabled": False,
            "reasonCode": "ready" if ready else "mirror-mount-not-mounted",
        },
        protected_pins=lambda: pins,
        verify_primary=lambda sha: primary_ok,
        mirror_exact=mirror,
        verify_secondary=lambda sha: secondary_ok,
    )
    return obj, calls


@pytest.mark.parametrize(("existing", "copied", "already"), [
    ((), 2, 0),
    ((A, B), 0, 2),
    ((A,), 1, 1),
])
def test_protected_pair_only(tmp_path, existing, copied, already):
    obj, calls = make_case(tmp_path, existing=existing)
    result = obj.run()
    assert result["state"] == "verified"
    assert result["mirroredCount"] == copied
    assert result["alreadyStoredCount"] == already
    assert result["verifiedCount"] == 2
    assert calls == [("mirror", A), ("mirror", B)]
    assert result["restoreTriggered"] is False
    assert result["updateTriggered"] is False
    assert result["deleteTriggered"] is False


@pytest.mark.parametrize("pins", [(), (A,), (A, A), ("invalid", B), (A, B, "c" * 40)])
def test_untrusted_or_incomplete_protected_set_blocks_without_copy(tmp_path, pins):
    obj, calls = make_case(tmp_path, pins=pins)
    assert obj.run()["reasonCode"] == "protected-set-unavailable"
    assert calls == []


@pytest.mark.parametrize(("kwargs", "reason"), [
    ({"ready": False}, "independent-volume-not-ready"),
    ({"stopped": True}, "operator-safety-blocked"),
    ({"primary_ok": False}, "primary-custody-invalid"),
    ({"secondary_ok": False}, "secondary-custody-invalid"),
])
def test_admission_and_integrity_block(tmp_path, kwargs, reason):
    obj, calls = make_case(tmp_path, **kwargs)
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == reason
    if reason != "secondary-custody-invalid":
        assert calls == []


def test_second_copy_failure_preserves_first_receipt_without_false_success(tmp_path):
    obj, calls = make_case(tmp_path, fail_on=B)
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["mirroredCount"] == 1
    assert result["verifiedCount"] == 1
    assert calls == [("mirror", A), ("mirror", B)]
    assert "private" not in str(result)
    assert "token" not in str(result)


def test_repeat_is_idempotent(tmp_path):
    obj, _ = make_case(tmp_path, existing=(A, B))
    assert obj.run() == obj.run()


def test_mismatched_admission_schema_is_never_sufficient(tmp_path):
    obj, calls = make_case(tmp_path)
    obj._readiness = lambda: {"ready": True}
    assert obj.run()["reasonCode"] == "independent-volume-not-ready"
    assert calls == []


def test_pre_copy_source_recheck_blocks_race(tmp_path):
    obj, calls = make_case(tmp_path)
    observations = []
    def source_state(sha):
        observations.append(sha)
        return len(observations) < 4

    obj._verify_primary = source_state
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "primary-custody-invalid"
    assert calls == [("mirror", A)]


def test_mount_identity_drift_after_first_copy_blocks_second_copy(tmp_path):
    obj, calls = make_case(tmp_path)
    good = {
        "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
        "configurationState": "configured",
        "ready": True,
        "primaryCustodyReady": True,
        "mountReady": True,
        "mirrorRootReady": True,
        "distinctDeviceReady": True,
        "mutationEnabled": False,
        "reasonCode": "ready",
    }
    observations = 0

    def changing_readiness():
        nonlocal observations
        observations += 1
        if observations >= 3:
            return {**good, "distinctDeviceReady": False}
        return good

    obj._readiness = changing_readiness
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "independent-volume-not-ready"
    assert result["mirroredCount"] == 1
    assert result["verifiedCount"] == 1
    assert calls == [("mirror", A)]


def test_readiness_schema_change_after_preflight_prevents_first_copy(tmp_path):
    obj, calls = make_case(tmp_path)
    good = {
        "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
        "configurationState": "configured",
        "ready": True,
        "primaryCustodyReady": True,
        "mountReady": True,
        "mirrorRootReady": True,
        "distinctDeviceReady": True,
        "mutationEnabled": False,
        "reasonCode": "ready",
    }
    observations = 0

    def changing_readiness():
        nonlocal observations
        observations += 1
        if observations == 2:
            return {**good, "schemaVersion": "unknown"}
        return good

    obj._readiness = changing_readiness
    assert obj.run()["reasonCode"] == "independent-volume-not-ready"
    assert calls == []


def test_protected_pins_change_before_second_copy_blocks(tmp_path):
    obj, calls = make_case(tmp_path)
    reads = 0

    def moving_pins():
        nonlocal reads
        reads += 1
        return (A, B) if reads <= 2 else (A, "c" * 40)

    obj._pins = moving_pins
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "protected-set-changed"
    assert result["verifiedCount"] == 1
    assert calls == [("mirror", A)]


def test_protected_pins_change_after_both_copies_is_not_success(tmp_path):
    obj, calls = make_case(tmp_path)
    reads = 0

    def moving_pins():
        nonlocal reads
        reads += 1
        return (A, B) if reads <= 3 else (A, "c" * 40)

    obj._pins = moving_pins
    result = obj.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "protected-set-changed"
    assert result["verifiedCount"] == 2
    assert calls == [("mirror", A), ("mirror", B)]
