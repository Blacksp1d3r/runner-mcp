from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from runner_mcp import fabric_bridge as fabric_bridge_module
from runner_mcp.bridge_processor import BridgeExecutionAdapterError
from runner_mcp.fabric_bridge import FabricBridgeClient, FabricBridgeConfig, FabricBridgeError

BASE = "a" * 40
COMMIT = "b" * 40


class FakeMCPClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def _call_tool(self, name: str, arguments: dict):
        self.calls.append((name, arguments))
        if not self.responses:
            raise AssertionError("unexpected Fabric tool call")
        return self.responses.pop(0)




def host_inspection_payload() -> dict:
    return {
        "schema_version": "runner.fabric/host-inspection/v1",
        "mutation_enabled": False,
        "host": {
            "id": "host:local",
            "display_name": "Runner Fabric host",
            "freshness": {
                "state": "fresh",
                "observed_at": "2026-10-04T00:00:00+00:00",
                "age_seconds": 0,
            },
            "cpu": {},
            "memory": {},
            "swap": {},
            "pressure": {},
            "filesystems": [],
            "disks": [],
            "network": [],
            "uptime_seconds": {
                "state": "available",
                "value": 1,
                "unit": "seconds",
            },
            "oom_kills": {
                "state": "available",
                "value": 0,
                "unit": "count",
            },
            "process_count": {
                "state": "available",
                "value": 1,
                "unit": "count",
            },
            "collector": {},
        },
        "browsers": [
            {
                "runtime": "chromium",
                "state": "available",
                "cache_ready": True,
                "version": "Chromium 154.0.1",
            },
            {
                "runtime": "chrome",
                "state": "unavailable",
                "cache_ready": True,
            },
            {
                "runtime": "firefox",
                "state": "unavailable",
                "cache_ready": False,
            },
            {
                "runtime": "webkit",
                "state": "unavailable",
                "cache_ready": False,
            },
        ],
    }

def external_target_preflight_payload() -> dict:
    return {
        "schemaVersion": "runner.fabric/external-target-preflight/v1",
        "ready": True,
        "targetAllocationId": "11111111-1111-4111-8111-111111111111",
        "environmentId": "22222222-2222-4222-8222-222222222222",
        "mutationEnabled": False,
        "networkChecked": False,
    }


def external_target_inspection_payload() -> dict:
    return {
        "schemaVersion": "runner.fabric/external-target-live-qualification/v1",
        "contractVersion": "runner.fabric/external-target-inspection/v1alpha1",
        "targetAllocationId": "11111111-1111-4111-8111-111111111111",
        "environmentId": "22222222-2222-4222-8222-222222222222",
        "reachability": "reachable",
        "readiness": "ready",
        "observedAt": "2026-10-04T17:30:00+00:00",
        "reasonCode": "healthy",
        "releaseRevision": "a" * 40,
        "evidenceRefs": ["external-target:fixed-readonly-adapter"],
        "liveMutationEnabled": False,
    }


def result_payload() -> dict:
    return {
        "state": "complete",
        "expected_revision": BASE,
        "commit_revision": COMMIT,
        "pushed_revision": COMMIT,
        "change_reference": "change:247",
        "report_reference": "report:247",
        "corrections_used": 0,
        "reported": True,
        "evidence": [
            {
                "stage": "reconcile",
                "outcome": "success",
                "reason_code": "reconciled",
                "attempt": 0,
                "checkpoint": "preflight",
                "revision": BASE,
                "reference": None,
            }
        ],
    }


def bridge_with_responses(*responses: object) -> tuple[FabricBridgeClient, FakeMCPClient]:
    bridge = FabricBridgeClient.__new__(FabricBridgeClient)
    fake = FakeMCPClient(list(responses))
    bridge._local = SimpleNamespace(client=fake)
    return bridge, fake


def test_bridge_uses_independent_local_mcp_clients_per_thread() -> None:
    bridge = FabricBridgeClient(
        FabricBridgeConfig(
            endpoint="http://127.0.0.1:9010/mcp",
            bearer_token="x" * 32,
        )
    )
    barrier = Barrier(2)

    def resolve_client_id() -> int:
        client = bridge._client()
        barrier.wait(timeout=2)
        return id(client)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(resolve_client_id) for _ in range(2)]
        client_ids = [future.result(timeout=3) for future in futures]

    assert client_ids[0] != client_ids[1]


def test_config_requires_strong_token_and_loopback_mcp_endpoint() -> None:
    config = FabricBridgeConfig(
        endpoint="http://127.0.0.1:9010/mcp",
        bearer_token="x" * 32,
    )

    assert config.to_mcp_config().endpoint == "http://127.0.0.1:9010/mcp"

    with pytest.raises(ValueError, match="at least 32"):
        FabricBridgeConfig(
            endpoint="http://127.0.0.1:9010/mcp",
            bearer_token="short",
        )

    with pytest.raises(ValueError, match="loopback"):
        FabricBridgeConfig(
            endpoint="https://fabric.example.invalid/mcp",
            bearer_token="x" * 32,
        ).to_mcp_config()


def test_run_work_unit_forwards_only_bounded_coarse_arguments() -> None:
    bridge, fake = bridge_with_responses(result_payload())

    result = bridge.run_work_unit(
        work_unit_id="wu:247",
        project_id="project:runner-fabric",
        work_item_id="issue:247",
        expected_revision=BASE,
        change_plan_id="plan:247",
    )

    assert result["state"] == "complete"
    assert fake.calls == [
        (
            "run_work_unit",
            {
                "work_unit_id": "wu:247",
                "project_id": "project:runner-fabric",
                "work_item_id": "issue:247",
                "expected_revision": BASE,
                "change_plan_id": "plan:247",
                "validation_profile": "foundation",
                "correction_budget": 1,
                "landing_mode": "managed_branch_push",
            },
        )
    ]


def test_run_work_unit_rejects_mismatched_expected_revision() -> None:
    payload = result_payload()
    payload["expected_revision"] = "c" * 40
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError, match="mismatched expected revision"):
        bridge.run_work_unit(
            work_unit_id="wu:247",
            project_id="project:runner-fabric",
            work_item_id="issue:247",
            expected_revision=BASE,
            change_plan_id="plan:247",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("validation_profile", "shell"),
        ("landing_mode", "push_anywhere"),
        ("correction_budget", 4),
    ],
)
def test_run_work_unit_rejects_unbounded_execution_options(
    field: str,
    value: object,
) -> None:
    bridge, fake = bridge_with_responses(result_payload())
    kwargs = {
        "work_unit_id": "wu:247",
        "project_id": "project:runner-fabric",
        "work_item_id": "issue:247",
        "expected_revision": BASE,
        "change_plan_id": "plan:247",
    }
    kwargs[field] = value

    with pytest.raises(FabricBridgeError):
        bridge.run_work_unit(**kwargs)  # type: ignore[arg-type]

    assert fake.calls == []


def test_status_and_cancel_forward_only_work_unit_id() -> None:
    view = {
        "work_unit_id": "wu:247",
        "project_id": "project:runner-fabric",
        "work_item_id": "issue:247",
        "status": "running",
        "result": None,
    }
    bridge, fake = bridge_with_responses(view, view)

    assert bridge.get_work_unit("wu:247") == view
    assert bridge.cancel_work_unit("wu:247") == view
    assert fake.calls == [
        ("get_work_unit", {"work_unit_id": "wu:247"}),
        ("cancel_work_unit", {"work_unit_id": "wu:247"}),
    ]


@pytest.mark.parametrize(
    "view",
    [
        {
            "work_unit_id": "wu:other",
            "project_id": "project:runner-fabric",
            "work_item_id": "issue:247",
            "status": "running",
            "result": None,
        },
        {
            "work_unit_id": "wu:247",
            "project_id": "project:runner-fabric",
            "work_item_id": "issue:247",
            "status": "running",
            "result": result_payload(),
        },
        {
            "work_unit_id": "wu:247",
            "project_id": "project:runner-fabric",
            "work_item_id": "issue:247",
            "status": "complete",
            "result": None,
        },
        {
            "work_unit_id": "wu:247",
            "project_id": "project:runner-fabric",
            "work_item_id": "issue:247",
            "status": "complete",
            "result": {**result_payload(), "state": "failed"},
        },
    ],
)
def test_work_unit_view_identity_and_state_relationships_fail_closed(view: dict) -> None:
    bridge, _ = bridge_with_responses(view)

    with pytest.raises(FabricBridgeError):
        bridge.get_work_unit("wu:247")


def test_fabric_response_unknown_field_fails_closed() -> None:
    payload = result_payload()
    payload["private_path"] = "/secret"
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError, match="invalid work-unit result"):
        bridge.run_work_unit(
            work_unit_id="wu:247",
            project_id="project:runner-fabric",
            work_item_id="issue:247",
            expected_revision=BASE,
            change_plan_id="plan:247",
        )


def test_fabric_evidence_rejects_raw_or_unknown_shape() -> None:
    payload = result_payload()
    payload["evidence"][0]["raw_log"] = "token=secret"
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError, match="stage evidence"):
        bridge.run_work_unit(
            work_unit_id="wu:247",
            project_id="project:runner-fabric",
            work_item_id="issue:247",
            expected_revision=BASE,
            change_plan_id="plan:247",
        )


def test_host_inspect_forwards_no_arguments_and_validates_result() -> None:
    payload = host_inspection_payload()
    bridge, fake = bridge_with_responses(payload)

    result = bridge.host_inspect()

    assert result == payload
    assert fake.calls == [("host_inspect", {})]


def test_external_target_reads_forward_no_arguments_and_validate_results() -> None:
    preflight = external_target_preflight_payload()
    inspection = external_target_inspection_payload()
    bridge, fake = bridge_with_responses(preflight, inspection)

    assert bridge.external_target_preflight() == preflight
    assert bridge.external_target_inspect() == inspection
    assert fake.calls == [
        ("external_target_preflight", {}),
        ("external_target_inspect", {}),
    ]


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        (
            "external_target_preflight",
            {**external_target_preflight_payload(), "mutationEnabled": True},
        ),
        (
            "external_target_preflight",
            {**external_target_preflight_payload(), "private_path": "/secret"},
        ),
        (
            "external_target_inspect",
            {**external_target_inspection_payload(), "liveMutationEnabled": True},
        ),
        (
            "external_target_inspect",
            {**external_target_inspection_payload(), "endpoint": "https://private.invalid"},
        ),
    ],
)
def test_external_target_reads_reject_mutation_or_private_detail(
    method: str,
    payload: dict,
) -> None:
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        getattr(bridge, method)()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/tmp"}),
        lambda payload: payload.update({"mutation_enabled": True}),
        lambda payload: payload["host"].update({"endpoint": "https://private.invalid"}),
        lambda payload: payload["browsers"].append(
            {
                "runtime": "chromium",
                "state": "available",
                "cache_ready": False,
                "version": "duplicate",
            }
        ),
    ],
)
def test_host_inspect_rejects_unbounded_or_invalid_result(mutator) -> None:
    payload = host_inspection_payload()
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        bridge.host_inspect()



def synthetic_probe_status_payload(
    *,
    available: bool = True,
    age_seconds: int = 30,
    interval_seconds: int = 60,
    outcome: str = "success",
    failure_layer: str | None = None,
    reason_code: str = "probe_succeeded",
) -> dict:
    if not available:
        return {
            "schemaVersion": "runner.fabric/agent-bus-synthetic-probe-status/v1",
            "available": False,
            "observed_at": None,
            "age_seconds": None,
            "interval_seconds": None,
            "outcome": None,
            "failure_layer": None,
            "reason_code": "probe_status_unavailable",
            "qualification_id": None,
            "trace_id": None,
            "outcome_evidence_id": None,
            "cycle_evidence_id": None,
        }
    return {
        "schemaVersion": "runner.fabric/agent-bus-synthetic-probe-status/v1",
        "available": True,
        "observed_at": 1_200,
        "age_seconds": age_seconds,
        "interval_seconds": interval_seconds,
        "outcome": outcome,
        "failure_layer": failure_layer,
        "reason_code": reason_code,
        "qualification_id": "probe:fleet:14",
        "trace_id": "1" * 32,
        "outcome_evidence_id": "agent-bus-probe-abc123",
        "cycle_evidence_id": "agent-bus-cycle-def456",
    }


def test_synthetic_probe_status_is_zero_arg_and_freshness_bounded() -> None:
    fresh = synthetic_probe_status_payload()
    stale = synthetic_probe_status_payload(age_seconds=61)
    bridge, fake = bridge_with_responses(fresh, fresh, stale)

    assert bridge.synthetic_probe_status() == fresh
    assert bridge.synthetic_probe_fresh_success() is True
    assert bridge.synthetic_probe_fresh_success() is False
    assert fake.calls == [
        ("synthetic_probe_status", {}),
        ("synthetic_probe_status", {}),
        ("synthetic_probe_status", {}),
    ]


def test_synthetic_probe_failure_and_unavailable_are_not_routable() -> None:
    failed = synthetic_probe_status_payload(
        outcome="failure",
        failure_layer="transport",
        reason_code="relay_transport_unavailable",
    )
    unavailable = synthetic_probe_status_payload(available=False)
    bridge, _ = bridge_with_responses(failed, unavailable)

    assert bridge.synthetic_probe_fresh_success() is False
    assert bridge.synthetic_probe_fresh_success() is False


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/secret"}),
        lambda payload: payload.update({"trace_id": "0" * 32}),
        lambda payload: payload.update({"failure_layer": "transport"}),
        lambda payload: payload.update({"age_seconds": -1}),
        lambda payload: payload.update({"interval_seconds": 29}),
        lambda payload: payload.update({"interval_seconds": 121}),
        lambda payload: payload.update({"reason_code": "/private"}),
        lambda payload: payload.update({"qualification_id": "../probe"}),
    ],
)
def test_synthetic_probe_status_rejects_invalid_or_private_payload(mutator) -> None:
    payload = synthetic_probe_status_payload()
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError, match="synthetic probe status"):
        bridge.synthetic_probe_status()


def operational_snapshot_payload() -> dict:
    return {
        "schema_version": "runner.fabric/operational-snapshot/v1",
        "observed_at": 100,
        "busy": True,
        "degraded": False,
        "unknown_layers": [],
        "layers": [
            {
                "layer": "agent-bus.relay",
                "health": "healthy",
                "queued": 1,
                "claimed": 0,
                "running": 0,
                "waiting_for_result": 0,
                "waiting_for_ack": 0,
                "retrying": 0,
                "pending_count": 1,
                "capacity_total": None,
                "capacity_available": None,
                "oldest_pending_age_seconds": 5,
                "last_activity_age_seconds": 1,
                "reason_code": "pending-relay-work",
            }
        ],
        "mutation_enabled": False,
        "execution_enabled": False,
    }


def test_operational_snapshot_forwards_no_arguments_and_validates_result() -> None:
    payload = operational_snapshot_payload()
    bridge, fake = bridge_with_responses(payload)

    result = bridge.operational_snapshot()

    assert result == payload
    assert fake.calls == [("operational_snapshot", {})]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/tmp"}),
        lambda payload: payload.update({"mutation_enabled": True}),
        lambda payload: payload["layers"][0].update({"pending_count": 2}),
        lambda payload: payload["layers"][0].update({"health": "green"}),
        lambda payload: payload["layers"][0].update({"endpoint": "https://private.invalid"}),
    ],
)
def test_operational_snapshot_rejects_invalid_or_private_result(mutator) -> None:
    payload = operational_snapshot_payload()
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        bridge.operational_snapshot()


def ci_guest_payload(
    *,
    operation: str = "status",
    state: str = "ready",
    registered: bool = False,
    running: bool = False,
) -> dict:
    return {
        "contract_version": (
            "runner.fabric/ci-runner-guest-execution/v1alpha1"
        ),
        "operation": operation,
        "state": state,
        "runner_name": "aifordable-lab-ci",
        "registered": registered,
        "running": running,
        "isolation_green": True,
        "network_green": True,
        "mutation_enabled": True,
    }


def test_ci_guest_bridge_forwards_only_bounded_arguments() -> None:
    status = ci_guest_payload()
    enrolled = ci_guest_payload(
        operation="enroll",
        state="registered",
        registered=True,
    )
    started = ci_guest_payload(
        operation="start",
        state="running",
        registered=True,
        running=True,
    )
    stopped = ci_guest_payload(
        operation="stop",
        state="stopped",
        registered=True,
    )
    bridge, fake = bridge_with_responses(
        status,
        enrolled,
        started,
        stopped,
    )
    handoff_id = "ab" * 16

    assert bridge.ci_runner_guest_status() == status
    assert bridge.ci_runner_guest_enroll(handoff_id) == enrolled
    assert bridge.ci_runner_guest_start() == started
    assert bridge.ci_runner_guest_stop() == stopped

    assert fake.calls == [
        ("ci_runner_guest_status", {}),
        ("ci_runner_guest_enroll", {"handoff_id": handoff_id}),
        ("ci_runner_guest_start", {}),
        ("ci_runner_guest_stop", {}),
    ]


@pytest.mark.parametrize(
    "handoff_id",
    [
        "",
        "short",
        "../" + "a" * 29,
        "g" * 32,
        "a" * 31,
        "a" * 33,
    ],
)
def test_ci_guest_enroll_rejects_invalid_handoff_before_transport(
    handoff_id: str,
) -> None:
    bridge, fake = bridge_with_responses(ci_guest_payload())

    with pytest.raises(FabricBridgeError, match="handoff id"):
        bridge.ci_runner_guest_enroll(handoff_id)

    assert fake.calls == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/secret"}),
        lambda payload: payload.update({"token": "secret"}),
        lambda payload: payload.update({"state": "unknown"}),
        lambda payload: payload.update({"operation": "shell"}),
        lambda payload: payload.update({"running": True}),
        lambda payload: payload.update({"runner_name": "../runner"}),
    ],
)
def test_ci_guest_result_rejects_private_or_invalid_shape(mutator) -> None:
    payload = ci_guest_payload()
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError, match="CI guest result"):
        bridge.ci_runner_guest_status()


def test_ci_guest_enroll_has_no_secret_argument_surface() -> None:
    enrolled = ci_guest_payload(
        operation="enroll",
        state="registered",
        registered=True,
    )
    bridge, fake = bridge_with_responses(enrolled)
    secret = "registration-secret-must-not-cross-mcp"

    result = bridge.ci_runner_guest_enroll("ab" * 16)

    assert result["registered"] is True
    assert secret not in repr(fake.calls)
    assert set(fake.calls[0][1]) == {"handoff_id"}


def a6_prepare_payload(candidate: str = "2" * 40) -> dict:
    return {
        "schemaVersion": "runner.fabric/a6-update-qualification/v1",
        "state": "prepared",
        "correlation_id": f"fleet-a6:{'1' * 40}:{candidate}",
        "target_revision": "1" * 40,
        "candidate_revision": candidate,
        "off_target": True,
        "journal_storage_domain": "control:evidence",
        "target_storage_domain": "target:runner-mcp",
    }


def a6_finalize_payload(
    *,
    correlation_id: str,
    job_id: str,
) -> dict:
    return {
        "schemaVersion": "runner.fabric/a6-update-qualification/v1",
        "state": "qualified",
        "correlation_id": correlation_id,
        "target_revision": "1" * 40,
        "candidate_revision": "2" * 40,
        "update_job_id": job_id,
        "update_outcome": "succeeded",
        "reconnect_outcome": "succeeded",
        "probe_outcome": "succeeded",
        "record_count": 4,
        "off_target": True,
        "journal_storage_domain": "control:evidence",
        "target_storage_domain": "target:runner-mcp",
    }


def test_a6_qualification_proxy_forwards_only_bounded_identity_arguments() -> None:
    candidate = "2" * 40
    prepared = a6_prepare_payload(candidate)
    correlation = prepared["correlation_id"]
    job_id = "a" * 32
    finalized = a6_finalize_payload(correlation_id=correlation, job_id=job_id)
    bridge, fake = bridge_with_responses(prepared, finalized)

    assert bridge.a6_update_qualification_prepare(candidate) == prepared
    assert bridge.a6_update_qualification_finalize(correlation, job_id) == finalized
    assert fake.calls == [
        ("a6_update_qualification_prepare", {"candidate_commit": candidate}),
        (
            "a6_update_qualification_finalize",
            {"correlation_id": correlation, "job_id": job_id},
        ),
    ]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/secret"}),
        lambda payload: payload.update({"off_target": False}),
        lambda payload: payload.update({"candidate_revision": "3" * 40}),
        lambda payload: payload.update({"journal_storage_domain": "same", "target_storage_domain": "same"}),
    ],
)
def test_a6_prepare_rejects_private_or_invalid_result(mutator) -> None:
    candidate = "2" * 40
    payload = a6_prepare_payload(candidate)
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        bridge.a6_update_qualification_prepare(candidate)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/secret"}),
        lambda payload: payload.update({"state": "prepared"}),
        lambda payload: payload.update({"update_outcome": "failed"}),
        lambda payload: payload.update({"record_count": 3}),
    ],
)
def test_a6_finalize_rejects_private_or_unsuccessful_result(mutator) -> None:
    correlation = f"fleet-a6:{'1' * 40}:{'2' * 40}"
    job_id = "a" * 32
    payload = a6_finalize_payload(correlation_id=correlation, job_id=job_id)
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        bridge.a6_update_qualification_finalize(correlation, job_id)


@pytest.mark.parametrize(
    ("candidate", "correlation", "job_id"),
    [
        ("bad", f"fleet-a6:{'1' * 40}:{'2' * 40}", "a" * 32),
        ("2" * 40, "../bad", "a" * 32),
        ("2" * 40, f"fleet-a6:{'1' * 40}:{'2' * 40}", "bad"),
    ],
)
def test_a6_proxy_rejects_invalid_inputs_before_transport(
    candidate: str,
    correlation: str,
    job_id: str,
) -> None:
    bridge, fake = bridge_with_responses(a6_prepare_payload())

    if candidate != "2" * 40:
        with pytest.raises(FabricBridgeError):
            bridge.a6_update_qualification_prepare(candidate)
    else:
        with pytest.raises(FabricBridgeError):
            bridge.a6_update_qualification_finalize(correlation, job_id)

    assert fake.calls == []


class _PreflightClient:
    failure: str | None = None

    def __init__(
        self,
        _config,
        *,
        allowed_tools,
        client_name,
        compatibility_preflight,
    ) -> None:
        assert allowed_tools == frozenset(
            {"synthetic_probe_status", "a6_update_qualification_prepare"}
        )
        assert client_name == "runner-mcp-fabric-preflight"
        assert compatibility_preflight is True
        self.peer_identity = {
            "protocol_version": "2025-06-18",
            "server_name": "Runner Fabric Agent",
            "server_version": "1",
        }
        self.peer_build_identity = {
            "component_id": "runner-fabric",
            "build_version": "runner-fabric-agent-mcp",
            "source_revision": "c" * 40,
        }
        self.peer_tool_names = (
            "build_identity",
            "synthetic_probe_status",
            "a6_update_qualification_prepare",
        )

    def initialize(self) -> None:
        if self.failure is not None:
            raise BridgeExecutionAdapterError(self.failure)


def test_bridge_preflight_returns_only_bounded_peer_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _PreflightClient.failure = None
    monkeypatch.setattr(fabric_bridge_module, "LocalMCPClient", _PreflightClient)
    bridge = FabricBridgeClient(
        FabricBridgeConfig(
            endpoint="http://127.0.0.1:9010/mcp",
            bearer_token="x" * 32,
        )
    )

    result = bridge.preflight()

    assert result == {
        "schema_version": "runner-mcp/fabric-bridge-preflight/v1",
        "state": "ready",
        "reason_code": "ready",
        "protocol_version": "2025-06-18",
        "server_name": "Runner Fabric Agent",
        "server_version": "1",
        "source_revision": "c" * 40,
        "a6_prepare_available": True,
        "synthetic_probe_status_available": True,
        "mutation_enabled": False,
    }
    assert "endpoint" not in result
    assert "token" not in result
    assert "session_id" not in result


@pytest.mark.parametrize(
    ("detail", "reason"),
    [
        ("Runner MCP is unavailable or rejected the request", "transport_or_auth_unavailable"),
        ("Runner MCP initialization failed", "initialization_failed"),
        ("Runner MCP protocol version is incompatible", "protocol_incompatible"),
        ("Runner MCP interface schema is incompatible", "interface_incompatible"),
        ("Runner MCP build identity is incompatible", "build_identity_incompatible"),
        ("Runner MCP server identity is invalid", "server_identity_invalid"),
        ("Runner MCP returned an invalid session identifier", "session_invalid"),
        ("Runner MCP returned an unsupported event stream", "response_invalid"),
        ("Runner MCP returned invalid JSON", "response_invalid"),
        ("Runner MCP response must be a JSON object", "response_invalid"),
        ("other bounded failure", "peer_unavailable"),
    ],
)
def test_bridge_preflight_classifies_failures_without_private_detail(
    monkeypatch: pytest.MonkeyPatch,
    detail: str,
    reason: str,
) -> None:
    _PreflightClient.failure = detail
    monkeypatch.setattr(fabric_bridge_module, "LocalMCPClient", _PreflightClient)
    bridge = FabricBridgeClient(
        FabricBridgeConfig(
            endpoint="http://127.0.0.1:9010/mcp",
            bearer_token="x" * 32,
        )
    )

    result = bridge.preflight()

    assert result["state"] == "blocked"
    assert result["reason_code"] == reason
    assert result["mutation_enabled"] is False
    assert result["protocol_version"] is None
    assert result["source_revision"] is None
    assert detail not in str(result)


def worker_qualification_payload(
    *,
    worker_id: str = "worker:aifordable-lab",
    profile: str = "bewind-ocr-qualification-v1",
    generation: int = 1,
) -> dict:
    return {
        "schemaVersion": "runner.fabric/worker-qualification-provisioning-result/v1",
        "workerId": worker_id,
        "capabilityProfile": profile,
        "state": "ready",
        "reasonCode": "ready",
        "observedGeneration": generation,
        "observedFabricRevision": "c" * 40,
        "requestFingerprint": "d" * 64,
        "managedLauncherReady": True,
        "qualificationStateReady": True,
        "normalActivationEnabled": False,
    }


def test_worker_qualification_proxy_forwards_only_semantic_arguments() -> None:
    payload = worker_qualification_payload()
    bridge, fake = bridge_with_responses(payload)

    result = bridge.worker_qualification_provision(
        "worker:aifordable-lab",
        "bewind-ocr-qualification-v1",
        1,
    )

    assert result == payload
    assert fake.calls == [
        (
            "worker_qualification_provision",
            {
                "worker_id": "worker:aifordable-lab",
                "capability_profile": "bewind-ocr-qualification-v1",
                "expected_generation": 1,
            },
        )
    ]


@pytest.mark.parametrize(
    ("worker_id", "profile", "generation"),
    [
        ("../worker", "bewind-ocr-qualification-v1", 1),
        ("worker:aifordable-lab", "arbitrary-profile", 1),
        ("worker:aifordable-lab", "bewind-ocr-qualification-v1", 0),
        ("worker:aifordable-lab", "bewind-ocr-qualification-v1", True),
    ],
)
def test_worker_qualification_proxy_rejects_invalid_input_before_transport(
    worker_id: str,
    profile: str,
    generation: int,
) -> None:
    bridge, fake = bridge_with_responses(worker_qualification_payload())

    with pytest.raises(FabricBridgeError):
        bridge.worker_qualification_provision(worker_id, profile, generation)

    assert fake.calls == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"private_path": "/secret"}),
        lambda payload: payload.update({"workerId": "worker:other"}),
        lambda payload: payload.update({"capabilityProfile": "other"}),
        lambda payload: payload.update({"observedGeneration": 2}),
        lambda payload: payload.update({"normalActivationEnabled": True}),
        lambda payload: payload.update({"requestFingerprint": "not-a-digest"}),
        lambda payload: payload.update({"state": "not-ready"}),
    ],
)
def test_worker_qualification_proxy_rejects_private_or_mismatched_result(
    mutator,
) -> None:
    payload = worker_qualification_payload()
    mutator(payload)
    bridge, _ = bridge_with_responses(payload)

    with pytest.raises(FabricBridgeError):
        bridge.worker_qualification_provision(
            "worker:aifordable-lab",
            "bewind-ocr-qualification-v1",
            1,
        )
