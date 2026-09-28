from __future__ import annotations

import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp import retention_pruning as retention_pruning_module
from runner_mcp.config import (
    DatabaseConfig,
    DeploymentConfig,
    ProjectConfig,
    ProjectRegistry,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)
from runner_mcp.release_operation_lock import acquire_release_operation_lock
from runner_mcp.retention_pruning import RetentionPruneError, RetentionPruner

NOW = datetime(2026, 9, 24, 8, 0, tzinfo=UTC)


def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def release_id(created_at: datetime, suffix: int) -> str:
    return (
        created_at.strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + ("a" * 12)
        + f"-{suffix:06x}"
    )


def write_release(
    release_root: Path,
    *,
    created_at: datetime,
    suffix: int,
    previous: str | None = None,
    migrated: bool = False,
    backup_id: str | None = None,
) -> str:
    identifier = release_id(created_at, suffix)
    directory = private_dir(release_root / "releases" / identifier)
    (directory / "payload.txt").write_text("payload\n", encoding="utf-8")
    metadata = directory / ".runner-mcp-release.json"
    metadata.write_text(
        json.dumps(
            {
                "release_id": identifier,
                "commit": "b" * 40,
                "created_at": created_at.isoformat(),
                "previous_release": previous,
                "environment": "staging",
                "migrations_applied": migrated,
                "pre_migration_backup_id": backup_id,
            }
        ),
        encoding="utf-8",
    )
    metadata.chmod(0o600)
    return identifier


def set_current(release_root: Path, identifier: str) -> None:
    current = release_root / "current"
    current.unlink(missing_ok=True)
    current.symlink_to(Path("releases") / identifier)


def write_manual_backup(backup_root: Path) -> tuple[Path, Path]:
    identifier = "20260101T000000Z-" + ("c" * 12)
    project_dir = backup_root / "demo"
    dump = project_dir / f"{identifier}.dump"
    metadata = project_dir / f"{identifier}.json"
    dump.write_bytes(b"backup-data")
    dump.chmod(0o600)
    metadata.write_text(
        json.dumps(
            {
                "backup_id": identifier,
                "project": "demo",
                "kind": "manual",
                "created_at": "2026-01-01T00:00:00+00:00",
                "size_bytes": len(b"backup-data"),
                "engine": "postgresql",
            }
        ),
        encoding="utf-8",
    )
    metadata.chmod(0o600)
    return dump, metadata


def make_registry(
    tmp_path: Path,
    *,
    environment: str = "staging",
) -> tuple[ProjectRegistry, Path, Path]:
    project_root = private_dir(tmp_path / "project")
    release_root = private_dir(tmp_path / "release-root")
    private_dir(release_root / "releases")
    private_dir(release_root / ".runtime-home")
    backup_root = private_dir(tmp_path / "backups")
    private_dir(backup_root / "demo")

    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment=environment,
                root=project_root,
                database=DatabaseConfig(dsn_env="RUNNER_MCP_DB_DEMO"),
                deployment=DeploymentConfig(
                    release_root=release_root,
                    service="web",
                ),
            )
        }
    )
    return registry, release_root, backup_root


def make_guard(
    tmp_path: Path,
    *,
    stopped: bool = False,
    min_release_age_days: int = 1,
) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(
            min_releases_to_keep=2,
            min_release_age_days=min_release_age_days,
            pre_migration_backup_days=2,
        ),
        retention_confirmed=True,
    )


def make_pruner(
    tmp_path: Path,
    *,
    environment: str = "staging",
    stopped: bool = False,
    min_release_age_days: int = 1,
) -> tuple[RetentionPruner, Path, Path]:
    config_dir = private_dir(tmp_path / "config")
    registry, release_root, backup_root = make_registry(
        tmp_path,
        environment=environment,
    )
    pruner = RetentionPruner(
        config_dir=config_dir,
        registry=registry,
        safety=make_guard(
            tmp_path,
            stopped=stopped,
            min_release_age_days=min_release_age_days,
        ),
        backup_root=backup_root,
    )
    return pruner, release_root, backup_root


def populate_eligible_release(release_root: Path) -> tuple[str, str, str]:
    candidate = write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    rollback_target = write_release(
        release_root,
        created_at=datetime(2026, 9, 23, tzinfo=UTC),
        suffix=2,
    )
    current = write_release(
        release_root,
        created_at=datetime(2026, 9, 24, tzinfo=UTC),
        suffix=3,
        previous=rollback_target,
    )
    set_current(release_root, current)
    return candidate, rollback_target, current


def confirmation(plan: dict) -> str:
    return f"PRUNE RELEASE demo {plan['candidate_release']}"


def test_plan_selects_only_oldest_eligible_release_and_is_private(
    tmp_path: Path,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    older = write_release(
        release_root,
        created_at=datetime(2025, 12, 1, tzinfo=UTC),
        suffix=4,
    )

    plan = pruner.plan("demo", now=NOW)

    assert plan["planned"] is True
    assert plan["candidate_release"] == older
    assert plan["candidate_release"] != candidate
    plan_root = tmp_path / "config" / "retention-prune-plans"
    plan_file = plan_root / f"{plan['plan_id']}.json"
    assert stat.S_IMODE(plan_root.stat().st_mode) == 0o700
    assert stat.S_IMODE(plan_file.stat().st_mode) == 0o600
    assert str(tmp_path) not in repr(plan)


def test_plan_returns_no_candidate_when_nothing_is_eligible(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    newest = write_release(
        release_root,
        created_at=datetime(2026, 9, 24, tzinfo=UTC),
        suffix=1,
    )
    older = write_release(
        release_root,
        created_at=datetime(2026, 9, 23, tzinfo=UTC),
        suffix=2,
    )
    set_current(release_root, newest)

    result = pruner.plan("demo", now=NOW)

    assert result == {
        "planned": False,
        "project": "demo",
        "candidate_release": None,
        "reason": "no_eligible_release",
    }
    assert older in {path.name for path in (release_root / "releases").iterdir()}


def test_production_cannot_create_executable_prune_plan(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(
        tmp_path,
        environment="production",
    )
    populate_eligible_release(release_root)

    with pytest.raises(RetentionPruneError, match="staging"):
        pruner.plan("demo", now=NOW)

    assert not (tmp_path / "config" / "retention-prune-plans").exists()


def test_emergency_stop_allows_plan_but_blocks_execute(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path, stopped=True)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    with pytest.raises(OperatorStopActive):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"


def test_changed_candidate_metadata_invalidates_plan_before_mutation(
    tmp_path: Path,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)
    metadata = (
        release_root
        / "releases"
        / candidate
        / ".runner-mcp-release.json"
    )
    raw = json.loads(metadata.read_text(encoding="utf-8"))
    raw["commit"] = "d" * 40
    metadata.write_text(json.dumps(raw), encoding="utf-8")
    metadata.chmod(0o600)

    with pytest.raises(RetentionPruneError, match="stale"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"


def test_changed_retention_policy_invalidates_plan(tmp_path: Path) -> None:
    pruner, release_root, backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    changed = RetentionPruner(
        config_dir=tmp_path / "config",
        registry=pruner.registry,
        safety=make_guard(tmp_path, min_release_age_days=2),
        backup_root=backup_root,
    )
    with pytest.raises(RetentionPruneError, match="stale"):
        changed.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()


def test_expired_plan_is_rejected_without_mutation(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    with pytest.raises(RetentionPruneError, match="expired"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW + timedelta(seconds=601),
        )

    assert (release_root / "releases" / candidate).is_dir()


def test_release_lock_contention_fails_before_plan_consumption(
    tmp_path: Path,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    with acquire_release_operation_lock(release_root):
        with pytest.raises(RetentionPruneError, match="release_operation_busy"):
            pruner.execute(
                "demo",
                plan["plan_id"],
                confirmation=confirmation(plan),
                now=NOW,
            )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"


def test_successful_execute_quarantines_then_deletes_one_release_only(
    tmp_path: Path,
) -> None:
    pruner, release_root, backup_root = make_pruner(tmp_path)
    candidate, rollback_target, current = populate_eligible_release(release_root)
    backup_dump, backup_metadata = write_manual_backup(backup_root)
    backup_dump_before = backup_dump.read_bytes()
    backup_metadata_before = backup_metadata.read_bytes()
    plan = pruner.plan("demo", now=NOW)

    result = pruner.execute(
        "demo",
        plan["plan_id"],
        confirmation=confirmation(plan),
        now=NOW,
    )

    assert result["state"] == "completed"
    assert result["single_release"] is True
    assert result["backup_mutation_performed"] is False
    assert not (release_root / "releases" / candidate).exists()
    assert (release_root / "releases" / rollback_target).is_dir()
    assert (release_root / "releases" / current).is_dir()
    assert not (release_root / ".prune-quarantine" / plan["plan_id"]).exists()
    transaction_path = (
        release_root / ".prune-transactions" / f"{plan['plan_id']}.json"
    )
    transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
    assert transaction["state"] == "completed"
    assert stat.S_IMODE(transaction_path.stat().st_mode) == 0o600
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "consumed"
    assert backup_dump.read_bytes() == backup_dump_before
    assert backup_metadata.read_bytes() == backup_metadata_before
    assert str(tmp_path) not in repr(result)


def test_repeated_execution_of_same_plan_is_rejected(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)
    pruner.execute(
        "demo",
        plan["plan_id"],
        confirmation=confirmation(plan),
        now=NOW,
    )

    with pytest.raises(RetentionPruneError, match="already consumed"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )


def test_missing_fd_safe_rmtree_fails_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)
    monkeypatch.setattr(
        retention_pruning_module.shutil.rmtree,
        "avoids_symlink_attacks",
        False,
    )

    with pytest.raises(RetentionPruneError, match="safe recursive"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"


def test_broad_quarantine_permissions_fail_before_plan_consumption(
    tmp_path: Path,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    quarantine = release_root / ".prune-quarantine"
    quarantine.mkdir()
    quarantine.chmod(0o755)
    plan = pruner.plan("demo", now=NOW)

    with pytest.raises(RetentionPruneError, match="permissions"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"


def test_delete_failure_after_quarantine_requires_manual_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    def fail_delete(_quarantine: Path, _plan_id: str) -> None:
        raise RetentionPruneError("simulated bounded delete failure")

    monkeypatch.setattr(
        RetentionPruner,
        "_delete_quarantined",
        staticmethod(fail_delete),
    )

    with pytest.raises(RetentionPruneError, match="manual attention"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation=confirmation(plan),
            now=NOW,
        )

    assert not (release_root / "releases" / candidate).exists()
    assert (release_root / ".prune-quarantine" / plan["plan_id"]).is_dir()
    transaction_path = (
        release_root / ".prune-transactions" / f"{plan['plan_id']}.json"
    )
    transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
    assert transaction["state"] == "manual_attention_required"
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "consumed"


def test_wrong_confirmation_fails_without_mutation(tmp_path: Path) -> None:
    pruner, release_root, _backup_root = make_pruner(tmp_path)
    candidate, _rollback_target, _current = populate_eligible_release(release_root)
    plan = pruner.plan("demo", now=NOW)

    with pytest.raises(RetentionPruneError, match="confirmation"):
        pruner.execute(
            "demo",
            plan["plan_id"],
            confirmation="PRUNE RELEASE demo wrong",
            now=NOW,
        )

    assert (release_root / "releases" / candidate).is_dir()
    assert pruner.inspect_plan(plan["plan_id"])["state"] == "pending"
