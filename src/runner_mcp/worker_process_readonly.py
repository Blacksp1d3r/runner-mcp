"""Validate fixed worker process read-only evidence from existing Fabric MCP.

Never claim host identity/provenance authority from caller/source-controlled data.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

_SCHEMA = "runner.fabric/worker-process-readonly/v1"
_ASSETS = {
    "claude": ("AF-SVC-0011", "AF-VM-0001"),
    "qwen": ("AF-SVC-0019", "AF-VM-0003"),
}
_WAITS = frozenset({
    "host_observer_not_configured", "host_observer_unavailable",
    "worker_process_not_observed", "host_observation_invalid",
    "worker_host_identity_mismatch", "host_clock_unavailable",
    "host_observation_from_future", "host_observation_stale",
    "fabric_read_unavailable", "fabric_read_invalid",
})
_SHA = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


class WorkerProcessBridgeError(ValueError):
    """Sanitized invalid/untrusted first-party worker observation."""


def bounded_worker_wait(worker: str, reason: str) -> dict[str, object]:
    if type(worker) is not str or worker not in _ASSETS or reason not in _WAITS:
        raise WorkerProcessBridgeError("worker observation request invalid")
    asset, host = _ASSETS[worker]
    return {
        "schemaVersion": _SCHEMA,
        "worker": worker,
        "serviceAssetId": asset,
        "hostAssetId": host,
        "state": "wait",
        "reasonCode": reason,
        "observedAt": None,
        "ageSeconds": None,
        "pid": None,
        "uid": None,
        "processStartTicks": None,
        "packageVersion": None,
        "sourceRevision": None,
        "artifactSha256": None,
        "buildProvenanceVerified": False,
        "mutationEnabled": False,
        "dispatchAuthorized": False,
    }


def validate_worker_observation(worker: str, value: object) -> dict[str, object]:
    """Cross-check every byte of the fixed Fabric tool projection, fail closed."""
    blank = bounded_worker_wait(worker, "fabric_read_invalid")
    if type(value) is not dict or set(value) != set(blank):
        raise WorkerProcessBridgeError("worker observation invalid")
    if any(type(value[k]) is not str or value[k] != blank[k]
           for k in ("schemaVersion", "worker", "serviceAssetId", "hostAssetId")):
        raise WorkerProcessBridgeError("worker observation identity mismatch")
    if any(value[k] is not False for k in (
        "buildProvenanceVerified", "mutationEnabled", "dispatchAuthorized"
    )):
        raise WorkerProcessBridgeError("worker observation attempted authority")
    if value["state"] == "wait":
        if type(value["reasonCode"]) is not str or value["reasonCode"] not in _WAITS:
            raise WorkerProcessBridgeError("worker observation reason invalid")
        if any(value[k] is not None for k in (
            "observedAt", "ageSeconds", "pid", "uid", "processStartTicks",
            "packageVersion", "sourceRevision", "artifactSha256",
        )):
            raise WorkerProcessBridgeError("worker observation wait is contradictory")
        return dict(value)
    if (
        type(value["state"]) is not str
        or value["state"] != "observed_unverified"
        or type(value["reasonCode"]) is not str
        or value["reasonCode"] != "host_process_observed_unverified"
    ):
        raise WorkerProcessBridgeError("worker observation state invalid")
    if (type(value["observedAt"]) is not int or value["observedAt"] < 0
            or type(value["ageSeconds"]) is not int
            or not 0 <= value["ageSeconds"] <= 120
            or any(type(value[k]) is not int or value[k] < 1
                   for k in ("pid", "uid", "processStartTicks"))):
        raise WorkerProcessBridgeError("worker observation freshness invalid")
    for field, pattern in (
        ("packageVersion", _VERSION),
        ("sourceRevision", _SHA),
        ("artifactSha256", _DIGEST),
    ):
        item = value[field]
        if item is not None and (
            type(item) is not str or pattern.fullmatch(item) is None
        ):
            raise WorkerProcessBridgeError("worker software identity claim invalid")
    return dict(value)
