from __future__ import annotations

import pytest

from runner_mcp.fabric_bridge import (
    FabricBridgeClient,
    FabricBridgeConfig,
    FabricBridgeError,
)


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
    bridge._client = fake
    return bridge, fake


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
