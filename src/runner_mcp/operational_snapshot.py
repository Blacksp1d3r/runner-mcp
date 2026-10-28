"""Read-only bounded aggregation of existing local tests and Fabric observations.

This tool does NOT read the original ChatGPT client's queue/session, attest the
physical serving host or authorize any work-unit/transport operation.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from .fabric_bridge import FabricBridgeError, _validate_operational_snapshot

_MAX_COUNT = 1_000_000
_MAX_AGE = 31 * 24 * 60 * 60
_LAYER_FIELDS = (
    "layer", "health", "queued", "claimed", "running",
    "waiting_for_result", "waiting_for_ack", "retrying", "pending_count",
    "capacity_total", "capacity_available", "oldest_pending_age_seconds",
    "last_activity_age_seconds", "reason_code",
)


def _unknown_layer(name: str, reason: str) -> dict[str, object]:
    """Zero counts are placeholders; unknown health MUST preclude idle proof."""
    return {
        "layer": name,
        "health": "unknown",
        "queued": 0,
        "claimed": 0,
        "running": 0,
        "waiting_for_result": 0,
        "waiting_for_ack": 0,
        "retrying": 0,
        "pending_count": 0,
        "capacity_total": None,
        "capacity_available": None,
        "oldest_pending_age_seconds": None,
        "last_activity_age_seconds": None,
        "reason_code": reason,
    }


def _count(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_COUNT


def _local_test_layer(queue: object) -> dict[str, object]:
    if not isinstance(queue, Mapping):
        return _unknown_layer("local-test-queue", "not-configured-or-unavailable")
    try:
        queued = queue["queued_jobs"]
        claimed = queue["claimed_jobs"]
        running = queue["running_jobs"]
        limit = queue["concurrency_limit"]
        available = queue["available_workers"]
        oldest = queue["oldest_queued_job"]
    except (KeyError, TypeError):
        return _unknown_layer("local-test-queue", "invalid-local-evidence")

    if not all(_count(x) for x in (queued, claimed, running, limit, available)):
        return _unknown_layer("local-test-queue", "invalid-local-evidence")
    if limit < 1 or available > limit or claimed + running > limit:
        return _unknown_layer("local-test-queue", "invalid-local-evidence")
    if oldest is None:
        if queued:
            return _unknown_layer("local-test-queue", "invalid-local-evidence")
        oldest_age = None
    else:
        if not isinstance(oldest, Mapping):
            return _unknown_layer("local-test-queue", "invalid-local-evidence")
        oldest_age = oldest.get("age_seconds")
        if not (type(oldest_age) is int and 0 <= oldest_age <= _MAX_AGE):
            return _unknown_layer("local-test-queue", "invalid-local-evidence")
        if not queued:
            return _unknown_layer("local-test-queue", "invalid-local-evidence")
    if queued + claimed + running > _MAX_COUNT:
        return _unknown_layer("local-test-queue", "invalid-local-evidence")
    return {
        "layer": "local-test-queue",
        "health": "healthy",
        "queued": queued,
        "claimed": claimed,
        "running": running,
        "waiting_for_result": 0,
        "waiting_for_ack": 0,
        "retrying": 0,
        "pending_count": queued + claimed + running,
        "capacity_total": limit,
        "capacity_available": available,
        "oldest_pending_age_seconds": oldest_age,
        "last_activity_age_seconds": None,
        "reason_code": None,
    }


def bounded_operational_snapshot(
    *,
    local_queue: object,
    fabric_snapshot: object,
    now: int | None = None,
) -> dict[str, Any]:
    """Compose two already-authorized READS; never convert missing into idle.

    Fabric remains the owner of upstream layer counts. Only exact validated
    peer fields and selected local aggregate numbers cross the MCP boundary.
    """
    local = _local_test_layer(local_queue)
    layers = [local]
    fabric_busy = False
    fabric_degraded = True
    fabric_observed_at = None

    try:
        peer = _validate_operational_snapshot(fabric_snapshot)
        observed = int(time.time()) if now is None else now
        if (
            type(observed) is not int
            or not -60 <= observed - peer["observed_at"] <= 300
        ):
            raise FabricBridgeError("Fabric snapshot observation is stale")
        if not peer["layers"] or any(
            entry["layer"] == "local-test-queue" for entry in peer["layers"]
        ):
            raise FabricBridgeError("operational layer collision or absence")
        layers.extend(
            {key: entry[key] for key in _LAYER_FIELDS}
            for entry in peer["layers"]
        )
        fabric_busy = peer["busy"]
        fabric_degraded = peer["degraded"]
        fabric_observed_at = peer["observed_at"]
    except (FabricBridgeError, TypeError, KeyError, ValueError):
        layers.append(_unknown_layer("fabric-bridge", "peer-unavailable-or-invalid"))

    unknown_layers = [
        item["layer"]
        for item in layers
        if item["health"] in {"unknown", "unavailable"}
    ]
    degraded = fabric_degraded or any(
        item["health"] != "healthy" for item in layers
    )
    busy = fabric_busy or any(item["pending_count"] > 0 for item in layers)
    return {
        "schema_version": "runner-mcp/operational-snapshot/v1",
        "busy": bool(busy),
        "degraded": bool(degraded),
        # A zero pending count is not proof of idleness when a layer is unknown.
        "observable_layers_idle": not busy and not degraded and not unknown_layers,
        "end_to_end_idle_verified": False,
        "unknown_layers": unknown_layers,
        "layers": layers,
        "fabric_observed_at": fabric_observed_at,
        "evidence_scope": "connected-process-and-validated-peer-only",
        "client_session_observed": False,
        "original_host_attested": False,
        "mutation_enabled": False,
        "execution_enabled": False,
    }
