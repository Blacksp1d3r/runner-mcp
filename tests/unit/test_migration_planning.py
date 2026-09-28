from pathlib import Path

import pytest

from runner_mcp import migration_planning as migration_planning_module
from runner_mcp.config import (
    DatabaseConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
)
from runner_mcp.migration_planning import (
    ASYNC_MIGRATION_EXECUTION_MODE,
    async_migration_approval_material,
    migration_binding_fingerprint,
    migration_plan_material,
)

COMMIT = "a" * 40


def registry(
    tmp_path: Path,
    *,
    environment: str = "staging",
    with_migrations: bool = True,
) -> ProjectRegistry:
    root = tmp_path / "project"
    root.mkdir()
    database = DatabaseConfig(
        dsn_env="RUNNER_MCP_DB_DEMO",
        migrations=(
            MigrationConfig(
                status_argv=["/bin/true"],
                apply_argv=["/bin/true"],
                dsn_target_env="DATABASE_URL",
            )
            if with_migrations
            else None
        ),
    )
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment=environment,
                root=root,
                database=database,
            )
        }
    )


def test_migration_plan_material_preserves_approval_binding_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        migration_planning_module,
        "clean_head",
        lambda _root: {"commit": COMMIT, "clean": True},
    )
    current = registry(tmp_path)

    binding, summary = migration_plan_material(current, "demo")

    config = current.projects["demo"]
    assert binding == {
        "environment": "staging",
        "repository": "example/demo",
        "database": config.database.model_dump(mode="json"),
        "source": {"commit": COMMIT, "clean": True},
    }
    assert summary == {
        "action": "migration",
        "environment": "staging",
        "commit": COMMIT,
        "pre_migration_backup_required": True,
        "automatic_database_restore": False,
    }
    assert len(migration_binding_fingerprint(binding)) == 64


def test_migration_plan_material_rejects_non_staging(
    tmp_path: Path,
) -> None:
    current = registry(tmp_path, environment="production")

    with pytest.raises(ValueError, match="staging"):
        migration_plan_material(current, "demo")


def test_migration_plan_material_requires_migration_profile(
    tmp_path: Path,
) -> None:
    current = registry(tmp_path, with_migrations=False)

    with pytest.raises(ValueError, match="Migration profile"):
        migration_plan_material(current, "demo")


def test_async_migration_approval_material_wraps_canonical_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        migration_planning_module,
        "clean_head",
        lambda _root: {"commit": COMMIT, "clean": True},
    )
    current = registry(tmp_path)

    migration_binding, approval_binding, summary = (
        async_migration_approval_material(current, "demo")
    )

    assert approval_binding == {
        "migration": migration_binding,
        "execution_mode": "durable_async_v1",
    }
    assert ASYNC_MIGRATION_EXECUTION_MODE == "durable_async_v1"
    assert summary["action"] == "migration_async"
    assert summary["execution_mode"] == "durable_async_v1"
    assert summary["asynchronous"] is True
    assert summary["commit"] == COMMIT
    assert summary["pre_migration_backup_required"] is True
    assert summary["automatic_database_restore"] is False
