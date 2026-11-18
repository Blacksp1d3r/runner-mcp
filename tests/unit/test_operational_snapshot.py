"""#269: one bounded view must never mistake an idle local test queue for idle Fabric."""

from __future__ import annotations

from runner_mcp.operational_snapshot import bounded_operational_snapshot

NOW = 1_000_000


def _queue(*, queued: int = 0, claimed: int = 0, running: int = 0):
    oldest = (
        {"job_id": "PRIVATE_JOB_ID", "project": "PRIVATE_PROJECT",
         "suite": "PRIVATE_SUITE", "age_seconds": 9}
        if queued else None
    )
    return {
        "queued_jobs": queued,
        "claimed_jobs": claimed,
        "running_jobs": running,
        "available_workers": 2 - claimed - running,
        "concurrency_limit": 2,
        "queue_limit": 64,
        "oldest_queued_job": oldest,
        "projects": [{"project": "PRIVATE_PROJECT", "root": "/secret/path"}],
    }


def _fabric_layer(
    *, health="healthy", queued=0, claimed=0, running=0,
    waiting_for_result=0, waiting_for_ack=0, retrying=0,
    reason_code=None,
):
    return {
        "layer": "agent-bus.relay",
        "health": health,
        "queued": queued,
        "claimed": claimed,
        "running": running,
        "waiting_for_result": waiting_for_result,
        "waiting_for_ack": waiting_for_ack,
        "retrying": retrying,
        "pending_count": (
            queued + claimed + running + waiting_for_result
            + waiting_for_ack + retrying
        ),
        "capacity_total": None,
        "capacity_available": None,
        "oldest_pending_age_seconds": None,
        "last_activity_age_seconds": None,
        "reason_code": reason_code,
    }


def _fabric(*, layers=None, busy=False, degraded=False, observed_at=NOW):
    layers = [_fabric_layer()] if layers is None else layers
    return {
        "schema_version": "runner.fabric/operational-snapshot/v1",
        "observed_at": observed_at,
        "busy": busy,
        "degraded": degraded,
        "unknown_layers": [
            item["layer"] for item in layers
            if item["health"] in {"unknown", "unavailable"}
        ],
        "layers": layers,
        "mutation_enabled": False,
        "execution_enabled": False,
    }


def _view(queue, fabric, now=NOW):
    return bounded_operational_snapshot(
        local_queue=queue, fabric_snapshot=fabric, now=now,
    )


def test_upstream_waiting_for_ack_remains_busy_when_test_queue_idle():
    view = _view(_queue(), _fabric(
        layers=[_fabric_layer(waiting_for_ack=2)], busy=True,
    ))
    assert view["busy"] is True
    assert view["degraded"] is False
    assert view["observable_layers_idle"] is False
    assert view["end_to_end_idle_verified"] is False
    assert view["layers"][0]["pending_count"] == 0
    assert view["layers"][1]["waiting_for_ack"] == 2
    assert view["layers"][1]["pending_count"] == 2
    assert view["client_session_observed"] is False
    assert view["original_host_attested"] is False


def test_known_empty_sources_observable_idle_but_not_original_client_proof():
    view = _view(_queue(), _fabric())
    assert view["busy"] is False
    assert view["degraded"] is False
    assert view["observable_layers_idle"] is True
    assert view["end_to_end_idle_verified"] is False
    assert view["unknown_layers"] == []
    assert [entry["layer"] for entry in view["layers"]] == [
        "local-test-queue", "agent-bus.relay",
    ]


def test_unknown_relay_is_never_claimed_idle_even_when_counts_zero():
    view = _view(
        _queue(),
        _fabric(
            layers=[_fabric_layer(health="unknown", reason_code="evidence-unavailable")],
            degraded=True,
        ),
    )
    assert view["busy"] is False
    assert view["degraded"] is True
    assert view["observable_layers_idle"] is False
    assert view["unknown_layers"] == ["agent-bus.relay"]


def test_fabric_failure_retains_known_local_queue_counts_without_false_green():
    view = _view(_queue(queued=1), None)
    assert view["busy"] is True
    assert view["degraded"] is True
    assert view["unknown_layers"] == ["fabric-bridge"]
    assert view["layers"][0]["queued"] == 1
    assert view["layers"][0]["oldest_pending_age_seconds"] == 9
    serialized = repr(view)
    assert "PRIVATE_" not in serialized
    assert "/secret/path" not in serialized


def test_local_test_queue_unavailable_must_not_look_idle():
    view = _view(None, _fabric())
    assert view["busy"] is False
    assert view["degraded"] is True
    assert view["observable_layers_idle"] is False
    assert view["unknown_layers"] == ["local-test-queue"]


def test_invalid_local_count_and_capacity_fail_closed():
    for bad in (
        {"queued_jobs": True},
        {**_queue(), "running_jobs": 99},
        {**_queue(), "available_workers": -1},
        {**_queue(), "oldest_queued_job": {"age_seconds": -1}},
    ):
        view = _view(bad, _fabric())
        assert view["degraded"] is True
        assert view["unknown_layers"] == ["local-test-queue"]
        assert view["observable_layers_idle"] is False


def test_invalid_fabric_payload_is_sanitized_not_echoed():
    poison = {
        **_fabric(),
        "private_token": "NEVER_EXPOSE",
    }
    view = _view(_queue(), poison)
    assert view["degraded"] is True
    assert view["unknown_layers"] == ["fabric-bridge"]
    assert "NEVER_EXPOSE" not in repr(view)


def test_stale_or_future_fabric_peer_is_unavailable_not_idle():
    for timestamp in (NOW - 301, NOW + 61):
        view = _view(_queue(), _fabric(observed_at=timestamp))
        assert view["degraded"] is True
        assert view["unknown_layers"] == ["fabric-bridge"]
        assert view["observable_layers_idle"] is False


def test_fabric_layer_collision_refused_without_double_counting():
    layer = {**_fabric_layer(), "layer": "local-test-queue"}
    view = _view(_queue(), _fabric(layers=[layer]))
    assert view["degraded"] is True
    assert view["unknown_layers"] == ["fabric-bridge"]
    assert [item["layer"] for item in view["layers"]] == [
        "local-test-queue", "fabric-bridge",
    ]


def test_claimed_unknown_layer_cannot_be_advertised_as_healthy_idle():
    peer = _fabric()
    peer["unknown_layers"] = ["agent-bus.relay"]
    view = _view(_queue(), peer)
    assert view["busy"] is False
    assert view["degraded"] is True
    assert view["observable_layers_idle"] is False
    assert view["unknown_layers"] == ["fabric-bridge"]
    assert view["fabric_observed_at"] is None


def test_missing_or_duplicated_peer_unknown_list_is_invalid():
    layer = _fabric_layer(health="unknown", reason_code="evidence-unavailable")
    for unknown in ([], ["agent-bus.relay", "agent-bus.relay"]):
        peer = _fabric(layers=[layer], degraded=True)
        peer["unknown_layers"] = unknown
        view = _view(_queue(), peer)
        assert view["degraded"] is True
        assert view["unknown_layers"] == ["fabric-bridge"]
        assert view["observable_layers_idle"] is False


def test_local_available_worker_count_must_match_claimed_and_running():
    for claimed, running, available in ((0, 0, 1), (1, 0, 2), (0, 1, 2)):
        queue = _queue(claimed=claimed, running=running)
        queue["available_workers"] = available
        view = _view(queue, _fabric())
        assert view["degraded"] is True
        assert view["unknown_layers"] == ["local-test-queue"]
        assert view["observable_layers_idle"] is False


def test_waiting_ack_remains_busy_when_peer_busy_flag_is_inconsistent():
    # Never rely only on a remote summary flag; the validated counts matter.
    peer = _fabric(layers=[_fabric_layer(waiting_for_ack=2)], busy=False)
    view = _view(_queue(), peer)
    assert view["busy"] is True
    assert view["layers"][1]["waiting_for_ack"] == 2
    assert view["observable_layers_idle"] is False


def test_read_only_presentation_never_grants_dispatch():
    view = _view(_queue(running=1), _fabric())
    assert view["busy"] is True
    assert view["mutation_enabled"] is False
    assert view["execution_enabled"] is False
