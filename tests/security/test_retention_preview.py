import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp.cli import main
from runner_mcp.config import (
    DatabaseConfig,
    DeploymentConfig,
    ProjectConfig,
    ProjectRegistry,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    RetentionPolicy,
)
from runner_mcp.retention_preview import (
    RetentionPreviewError,
    RetentionPreviewPlanner,
)


NOW = datetime(2026, 9, 24, 8, 0, tzinfo=UTC)


def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def make_registry(
    tmp_path: Path,
    *,
    environment: str = "staging",
) -> tuple[ProjectRegistry, Path, Path]:
    project_root = private_dir(tmp_path / "project")
    release_root = private_dir(tmp_path / "releases-root")
    private_dir(release_root / "releases")
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
) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(
            min_releases_to_keep=2,
            min_release_age_days=1,
            pre_migration_backup_days=2,
        ),
        retention_confirmed=True,
    )


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
    current.symlink_to(Path("releases") / identifier)


def write_backup(
    backup_root: Path,
    *,
    created_at: datetime,
    suffix: str,
    kind: str,
    content: bytes = b"backup-data",
) -> str:
    identifier = created_at.strftime("%Y%m%dT%H%M%SZ") + "-" + suffix
    project_dir = backup_root / "demo"
    dump = project_dir / f"{identifier}.dump"
    metadata = project_dir / f"{identifier}.json"
    dump.write_bytes(content)
    dump.chmod(0o600)
    metadata.write_text(
        json.dumps(
            {
                "backup_id": identifier,
                "project": "demo",
                "kind": kind,
                "created_at": created_at.isoformat(),
                "size_bytes": len(content),
                "engine": "postgresql",
            }
        ),
        encoding="utf-8",
    )
    metadata.chmod(0o600)
    return identifier


def planner(
    tmp_path: Path,
    registry: ProjectRegistry,
    backup_root: Path,
    *,
    stopped: bool = False,
) -> RetentionPreviewPlanner:
    return RetentionPreviewPlanner(
        registry=registry,
        safety=make_guard(tmp_path, stopped=stopped),
        backup_root=backup_root,
    )


def by_release(result: dict) -> dict[str, dict]:
    return {row["release_id"]: row for row in result["releases"]}


def by_backup(result: dict) -> dict[str, dict]:
    return {row["backup_id"]: row for row in result["backups"]}


def test_current_and_direct_rollback_target_are_protected_even_when_old(
    tmp_path: Path,
) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    old_target = write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    current = write_release(
        release_root,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        suffix=2,
        previous=old_target,
    )
    orphan = write_release(
        release_root,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
        suffix=3,
    )
    write_release(
        release_root,
        created_at=datetime(2026, 9, 23, tzinfo=UTC),
        suffix=4,
    )
    write_release(
        release_root,
        created_at=datetime(2026, 9, 24, tzinfo=UTC),
        suffix=5,
    )
    set_current(release_root, current)

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)
    rows = by_release(result)

    assert "current" in rows[current]["categories"]
    assert rows[current]["potentially_eligible"] is False
    assert "rollback_target" in rows[old_target]["categories"]
    assert rows[old_target]["potentially_eligible"] is False
    assert rows[orphan]["categories"] == ["potentially_eligible"]
    assert rows[orphan]["potentially_eligible"] is True
    assert result["advisory_only"] is True
    assert result["deletion_authorized"] is False


def test_retained_release_reference_closure_blocks_older_chain(
    tmp_path: Path,
) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    oldest = write_release(
        release_root,
        created_at=datetime(2025, 12, 1, tzinfo=UTC),
        suffix=1,
    )
    middle = write_release(
        release_root,
        created_at=datetime(2025, 12, 2, tzinfo=UTC),
        suffix=2,
        previous=oldest,
    )
    current = write_release(
        release_root,
        created_at=datetime(2026, 9, 24, tzinfo=UTC),
        suffix=3,
        previous=middle,
    )
    set_current(release_root, current)

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)
    rows = by_release(result)

    assert "rollback_target" in rows[middle]["categories"]
    assert "referenced_by_retained_release" in rows[oldest]["categories"]
    assert rows[oldest]["potentially_eligible"] is False


def test_manual_backup_is_never_eligible_and_old_unreferenced_pre_migration_can_be(
    tmp_path: Path,
) -> None:
    registry, _release_root, backup_root = make_registry(tmp_path)
    manual = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="1" * 12,
        kind="manual",
    )
    pre_migration = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        suffix="2" * 12,
        kind="pre_migration",
    )

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)
    rows = by_backup(result)

    assert rows[manual]["categories"] == ["manual_policy_missing"]
    assert rows[manual]["potentially_eligible"] is False
    assert rows[pre_migration]["categories"] == ["potentially_eligible"]
    assert rows[pre_migration]["potentially_eligible"] is True


def test_pre_migration_backup_referenced_by_retained_release_stays_protected(
    tmp_path: Path,
) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    backup = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="3" * 12,
        kind="pre_migration",
    )
    current = write_release(
        release_root,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        suffix=1,
        migrated=True,
        backup_id=backup,
    )
    set_current(release_root, current)

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)
    release = by_release(result)[current]
    backup_row = by_backup(result)[backup]

    assert "migration_recovery_reference" in release["categories"]
    assert "referenced_by_retained_release" in backup_row["categories"]
    assert backup_row["potentially_eligible"] is False


def test_preview_remains_available_while_emergency_stop_is_active(
    tmp_path: Path,
) -> None:
    registry, _release_root, backup_root = make_registry(tmp_path)

    result = planner(
        tmp_path,
        registry,
        backup_root,
        stopped=True,
    ).preview("demo", now=NOW)

    assert result["project"] == "demo"
    assert result["advisory_only"] is True


def test_production_project_is_read_only_for_all_candidates(tmp_path: Path) -> None:
    registry, release_root, backup_root = make_registry(
        tmp_path,
        environment="production",
    )
    candidate = write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    backup = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="4" * 12,
        kind="pre_migration",
    )

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)

    assert "environment_read_only" in by_release(result)[candidate]["categories"]
    assert by_release(result)[candidate]["potentially_eligible"] is False
    assert "environment_read_only" in by_backup(result)[backup]["categories"]
    assert by_backup(result)[backup]["potentially_eligible"] is False


def test_release_metadata_extra_field_fails_closed(tmp_path: Path) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    identifier = write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    path = release_root / "releases" / identifier / ".runner-mcp-release.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["unexpected"] = True
    path.write_text(json.dumps(raw), encoding="utf-8")
    path.chmod(0o600)

    with pytest.raises(RetentionPreviewError, match="unsupported shape"):
        planner(tmp_path, registry, backup_root).preview("demo", now=NOW)


def test_symlinked_release_metadata_fails_closed(tmp_path: Path) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    identifier = write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    metadata = release_root / "releases" / identifier / ".runner-mcp-release.json"
    outside = tmp_path / "outside.json"
    outside.write_text(metadata.read_text(encoding="utf-8"), encoding="utf-8")
    outside.chmod(0o600)
    metadata.unlink()
    metadata.symlink_to(outside)

    with pytest.raises(RetentionPreviewError, match="Release metadata is unsafe"):
        planner(tmp_path, registry, backup_root).preview("demo", now=NOW)


def test_broad_backup_metadata_permissions_fail_closed(tmp_path: Path) -> None:
    registry, _release_root, backup_root = make_registry(tmp_path)
    backup = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="5" * 12,
        kind="manual",
    )
    metadata = backup_root / "demo" / f"{backup}.json"
    metadata.chmod(0o644)

    with pytest.raises(RetentionPreviewError, match="permissions are unsafe"):
        planner(tmp_path, registry, backup_root).preview("demo", now=NOW)


def test_backup_size_mismatch_fails_closed(tmp_path: Path) -> None:
    registry, _release_root, backup_root = make_registry(tmp_path)
    backup = write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="6" * 12,
        kind="pre_migration",
    )
    dump = backup_root / "demo" / f"{backup}.dump"
    dump.write_bytes(b"changed-size")
    dump.chmod(0o600)

    with pytest.raises(RetentionPreviewError, match="size does not match"):
        planner(tmp_path, registry, backup_root).preview("demo", now=NOW)


def test_preview_output_contains_no_private_paths(tmp_path: Path) -> None:
    registry, release_root, backup_root = make_registry(tmp_path)
    write_release(
        release_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix=1,
    )
    write_backup(
        backup_root,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="7" * 12,
        kind="manual",
    )

    result = planner(tmp_path, registry, backup_root).preview("demo", now=NOW)
    rendered = repr(result)

    assert str(tmp_path) not in rendered
    assert str(release_root) not in rendered
    assert str(backup_root) not in rendered


def test_retention_cli_renders_bounded_advisory_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_path = str(tmp_path / "private")
    fake = {
        "project": "demo",
        "environment": "staging",
        "advisory_only": True,
        "deletion_authorized": False,
        "releases": [
            {
                "release_id": "20260101T000000Z-aaaaaaaaaaaa-000001",
                "created_at": "2026-01-01T00:00:00+00:00",
                "categories": ["potentially_eligible"],
                "potentially_eligible": True,
            }
        ],
        "backups": [],
    }

    class FakePlanner:
        def preview(self, project: str) -> dict:
            assert project == "demo"
            return fake

    monkeypatch.setattr(
        "runner_mcp.cli._local_retention_preview_planner",
        lambda _config_dir: FakePlanner(),
    )

    result = main(
        [
            "--config-dir",
            private_path,
            "retention",
            "preview",
            "demo",
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert "Retention preview" in captured.out
    assert "Advisory only: yes" in captured.out
    assert "Deletion authorized: no" in captured.out
    assert "potentially-eligible=yes" in captured.out
    assert "No release, backup or metadata file was changed." in captured.out
    assert private_path not in captured.out
    assert captured.err == ""
