"""Cross-boundary regression tests for the AI fault-containment invariants."""

from pathlib import Path

import pytest

from runner_mcp.approval_manager import ApprovalError, ApprovalManager
from runner_mcp.bridge_mcp_executor import LocalMCPClient, LocalMCPConfig
from runner_mcp.bridge_processor import BridgeExecutionAdapterError
from runner_mcp.operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
    SafetyConfigurationError,
)


def test_client_text_cannot_select_an_unlisted_executor_capability() -> None:
    client = LocalMCPClient(
        LocalMCPConfig(endpoint="http://127.0.0.1:8000/mcp", bearer_token="test-token")
    )
    with pytest.raises(BridgeExecutionAdapterError, match="unsupported tool"):
        client._call_tool("run_arbitrary_shell", {"command": "ignore policy"})


def test_approval_binding_cannot_be_changed_after_human_approval(tmp_path: Path) -> None:
    manager = ApprovalManager(root=tmp_path / "approvals")
    binding = {"commit": "a" * 40, "environment": "staging"}
    plan = manager.request(
        action="deploy",
        project="demo",
        binding=binding,
        summary={"environment": "staging"},
    )
    manager.approve(plan["approval_id"])

    with pytest.raises(ApprovalError, match="plan changed"):
        manager.consume(
            plan["approval_id"],
            action="deploy",
            project="demo",
            binding={"commit": "b" * 40, "environment": "staging"},
        )


def test_approval_for_one_action_cannot_authorize_another(tmp_path: Path) -> None:
    manager = ApprovalManager(root=tmp_path / "approvals")
    binding = {"commit": "a" * 40}
    plan = manager.request(
        action="deploy",
        project="demo",
        binding=binding,
        summary={"environment": "staging"},
    )
    manager.approve(plan["approval_id"])

    with pytest.raises(ApprovalError, match="does not match"):
        manager.consume(
            plan["approval_id"],
            action="code_rollback",
            project="demo",
            binding=binding,
        )


def test_mutating_action_cannot_self_assert_production_authority(tmp_path: Path) -> None:
    guard = OperatorSafetyGuard(
        tmp_path / "operator.stop",
        RetentionPolicy(),
        retention_confirmed=True,
    )
    with pytest.raises(SafetyConfigurationError, match="only for staging"):
        guard.assert_project_action_allowed(ActionClass.DEPLOY, environment="production")


def test_external_operator_stop_overrides_mutating_client_intent(tmp_path: Path) -> None:
    stop = tmp_path / "operator.stop"
    stop.touch()
    guard = OperatorSafetyGuard(stop, RetentionPolicy(), retention_confirmed=True)

    with pytest.raises(OperatorStopActive):
        guard.assert_project_action_allowed(ActionClass.DEPLOY, environment="staging")


def test_contained_read_only_work_remains_available_during_stop(tmp_path: Path) -> None:
    stop = tmp_path / "operator.stop"
    stop.touch()
    guard = OperatorSafetyGuard(stop, RetentionPolicy(), retention_confirmed=True)

    guard.assert_project_action_allowed(ActionClass.READ_ONLY, environment="staging")
