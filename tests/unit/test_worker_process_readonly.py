from __future__ import annotations

from dataclasses import replace

import pytest

from runner_mcp.worker_process_readonly import (
    WorkerProcessBridgeError,
    bounded_worker_wait,
    validate_worker_observation,
)


def good(worker="claude"):
    return {
        **bounded_worker_wait(worker, "host_observer_not_configured"),
        "state": "observed_unverified",
        "reasonCode": "host_process_observed_unverified",
        "observedAt": 1000,
        "ageSeconds": 10,
        "pid": 2275,
        "uid": 1002,
        "processStartTicks": 123,
        "packageVersion": None,
        "sourceRevision": None,
        "artifactSha256": None,
    }


@pytest.mark.parametrize("worker", ["claude", "qwen"])
def test_expected_worker_observation_is_never_dispatch_authority(worker):
    result = validate_worker_observation(worker, good(worker))
    assert result["worker"] == worker
    assert result["state"] == "observed_unverified"
    assert result["buildProvenanceVerified"] is False
    assert result["dispatchAuthorized"] is False


def test_missing_host_reader_is_explicit_wait():
    value = bounded_worker_wait("claude", "host_observer_not_configured")
    assert validate_worker_observation("claude", value) == value
    assert value["pid"] is None


@pytest.mark.parametrize("field,broken", [
    ("worker", "qwen"),
    ("serviceAssetId", "AF-SVC-0019"),
    ("hostAssetId", "AF-VM-0003"),
    ("schemaVersion", "other/v1"),
    ("state", "ready"),
    ("reasonCode", "ready"),
    ("buildProvenanceVerified", True),
    ("mutationEnabled", True),
    ("dispatchAuthorized", True),
    ("pid", False),
    ("uid", 0),
    ("processStartTicks", -1),
    ("ageSeconds", 121),
    ("packageVersion", "../../secret"),
    ("sourceRevision", "a" * 39),
    ("artifactSha256", "b" * 63),
])
def test_bad_worker_payload_never_crosses_existing_bridge(field, broken):
    payload = good()
    payload[field] = broken
    with pytest.raises(WorkerProcessBridgeError):
        validate_worker_observation("claude", payload)


def test_wait_cannot_carry_positive_process_evidence():
    payload = bounded_worker_wait("qwen", "worker_process_not_observed")
    payload["pid"] = 1
    with pytest.raises(WorkerProcessBridgeError):
        validate_worker_observation("qwen", payload)


class EqualString(str):
    def __eq__(self, _other):
        return True


def test_forged_equality_does_not_change_host():
    payload = good()
    payload["hostAssetId"] = EqualString("AF-VM-0003")
    with pytest.raises(WorkerProcessBridgeError):
        validate_worker_observation("claude", payload)


def test_reject_unknown_worker_and_host_arguments():
    for worker in ("root", "admin", "runner:primary", "../"):
        with pytest.raises(WorkerProcessBridgeError):
            bounded_worker_wait(worker, "fabric_read_unavailable")
