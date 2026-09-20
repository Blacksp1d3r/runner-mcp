from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp.operational_safety import (
    ActionClass,
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
    SafetyConfigurationError,
)


def test_operator_actions_fail_closed_until_stop_mechanism_is_configured() -> None:
    guard = OperatorSafetyGuard(stop_file=None, retention=RetentionPolicy())

    guard.assert_action_allowed(ActionClass.READ_ONLY)
    guard.assert_action_allowed(ActionClass.CANCEL)

    with pytest.raises(SafetyConfigurationError, match="must be configured"):
        guard.assert_action_allowed(ActionClass.TEST)


def test_external_stop_file_blocks_operator_actions(tmp_path: Path) -> None:
    stop_file = tmp_path / "operator.stop"
    guard = OperatorSafetyGuard(stop_file=stop_file, retention=RetentionPolicy())

    guard.assert_action_allowed(ActionClass.DEPLOY)
    stop_file.write_text("stop\n", encoding="utf-8")

    status = guard.status()
    assert status.configured is True
    assert status.stop_active is True
    assert status.mode == "read_only_emergency_stop"

    guard.assert_action_allowed(ActionClass.READ_ONLY)
    guard.assert_action_allowed(ActionClass.CANCEL)
    with pytest.raises(OperatorStopActive):
        guard.assert_action_allowed(ActionClass.DEPLOY)


def test_only_one_code_rollback_step_is_allowed() -> None:
    guard = OperatorSafetyGuard(stop_file=None, retention=RetentionPolicy())

    guard.assert_code_rollback_steps(1)
    for steps in (0, 2, 5):
        with pytest.raises(SafetyConfigurationError, match="one release"):
            guard.assert_code_rollback_steps(steps)


def test_database_restore_always_requires_explicit_approval() -> None:
    with pytest.raises(SafetyConfigurationError, match="explicit human approval"):
        OperatorSafetyGuard.assert_database_restore_approved(explicit_approval=False)

    OperatorSafetyGuard.assert_database_restore_approved(explicit_approval=True)


def test_release_deletion_requires_both_count_and_age_thresholds() -> None:
    now = datetime(2026, 9, 20, tzinfo=UTC)
    policy = RetentionPolicy(
        min_releases_to_keep=20,
        min_release_age_days=90,
        pitr_retention_days=30,
        pre_migration_backup_days=180,
    )

    old = now - timedelta(days=120)
    recent = now - timedelta(days=20)

    assert policy.release_is_deletable(
        release_rank_from_newest=19,
        deployed_at=old,
        now=now,
    ) is False
    assert policy.release_is_deletable(
        release_rank_from_newest=20,
        deployed_at=recent,
        now=now,
    ) is False
    assert policy.release_is_deletable(
        release_rank_from_newest=20,
        deployed_at=old,
        now=now,
    ) is True


def test_pre_migration_backup_retention_is_age_based() -> None:
    now = datetime(2026, 9, 20, tzinfo=UTC)
    policy = RetentionPolicy(pre_migration_backup_days=180)

    assert policy.pre_migration_backup_is_deletable(
        created_at=now - timedelta(days=179),
        now=now,
    ) is False
    assert policy.pre_migration_backup_is_deletable(
        created_at=now - timedelta(days=180),
        now=now,
    ) is True


def test_retention_policy_cannot_enable_automatic_production_restore() -> None:
    with pytest.raises(ValueError, match="prohibited"):
        RetentionPolicy(automatic_production_database_restore=True)


def test_retention_policy_cannot_disable_restore_approval() -> None:
    with pytest.raises(ValueError, match="explicit approval"):
        RetentionPolicy(database_restore_requires_explicit_approval=False)


def test_unconfirmed_retention_keeps_operator_actions_read_only(tmp_path: Path) -> None:
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=False,
    )

    status = guard.status()
    assert status.mode == "read_only_until_retention_is_confirmed"
    guard.assert_action_allowed(ActionClass.READ_ONLY)

    with pytest.raises(SafetyConfigurationError, match="explicitly confirmed"):
        guard.assert_action_allowed(ActionClass.TEST)


def test_mutating_project_actions_are_staging_only(tmp_path: Path) -> None:
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    guard.assert_project_action_allowed(
        ActionClass.TEST,
        environment="staging",
    )
    guard.assert_project_action_allowed(
        ActionClass.READ_ONLY,
        environment="production",
    )
    with pytest.raises(SafetyConfigurationError, match="only for staging"):
        guard.assert_project_action_allowed(
            ActionClass.BACKUP,
            environment="production",
        )
    with pytest.raises(SafetyConfigurationError, match="only for staging"):
        guard.assert_project_action_allowed(
            ActionClass.SERVICE,
            environment="production",
        )
