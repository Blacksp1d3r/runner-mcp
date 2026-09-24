import json
import stat
from pathlib import Path

import pytest
from pydantic import ValidationError

from runner_mcp.config import (
    DatabaseConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
)
from runner_mcp.database_manager import DatabaseManager, DatabaseManagerError
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)

SECRET_DSN = "postgresql://private-user:private-password@db.example.invalid/app"


def make_executable(path: Path, body: str) -> Path:
    path.write_text("#!/bin/sh\nset -eu\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def make_registry(
    root: Path,
    *,
    environment: str = "staging",
    status_script: Path | None = None,
    apply_script: Path | None = None,
    timeout_seconds: int = 5,
    max_output_bytes: int = 4096,
) -> ProjectRegistry:
    root.mkdir(parents=True, exist_ok=True)
    migrations = None
    if status_script is not None and apply_script is not None:
        migrations = MigrationConfig(
            status_argv=[str(status_script)],
            apply_argv=[str(apply_script)],
            dsn_target_env="DATABASE_URL",
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment=environment,
                root=root,
                database=DatabaseConfig(
                    dsn_env="RUNNER_MCP_DB_DEMO",
                    migrations=migrations,
                ),
            )
        }
    )


def make_guard(tmp_path: Path, *, stopped: bool = False) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def make_pg_dump(tmp_path: Path) -> Path:
    return make_executable(tmp_path / "pg_dump", "exit 0")


def fake_backup_run(secret: str, seen: list[dict]):
    def _run(arguments, **kwargs):
        seen.append({"arguments": arguments, "kwargs": kwargs})
        assert secret not in " ".join(arguments)
        assert kwargs["env"]["PGDATABASE"] == secret
        assert kwargs["shell"] is False
        assert kwargs["stderr"] is not None
        kwargs["stdout"].write(b"fake-postgresql-custom-backup")
        return __import__("subprocess").CompletedProcess(arguments, 0)

    return _run


def make_pg_restore(tmp_path: Path, body: str = "exit 0") -> Path:
    return make_executable(tmp_path / "pg_restore", body)


def write_restore_backup(
    backup_root: Path,
    *,
    project: str = "demo",
    kind: str = "manual",
    content: bytes = b"fake-postgresql-custom-backup",
) -> tuple[str, Path, Path]:
    backup_root.mkdir(mode=0o700, exist_ok=True)
    backup_root.chmod(0o700)
    project_dir = backup_root / project
    project_dir.mkdir(mode=0o700, exist_ok=True)
    project_dir.chmod(0o700)
    backup_id = "20260924T050000Z-" + ("a" * 12)
    dump = project_dir / f"{backup_id}.dump"
    metadata = project_dir / f"{backup_id}.json"
    dump.write_bytes(content)
    dump.chmod(0o600)
    metadata.write_text(
        json.dumps(
            {
                "backup_id": backup_id,
                "project": project,
                "kind": kind,
                "created_at": "2026-09-24T05:00:00+00:00",
                "size_bytes": len(content),
                "engine": "postgresql",
            }
        ),
        encoding="utf-8",
    )
    metadata.chmod(0o600)
    return backup_id, dump, metadata


class ExplodingSecrets:
    def get(self, _name: str):
        raise AssertionError("restore preflight must not read database credentials")


def test_database_dsn_variable_must_use_dedicated_prefix() -> None:
    with pytest.raises(ValidationError, match="RUNNER_MCP_DB_"):
        DatabaseConfig(dsn_env="RUNNER_MCP_BEARER_TOKEN")


def test_backup_uses_environment_not_command_line_and_writes_private_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = make_registry(tmp_path / "project")
    seen: list[dict] = []
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        fake_backup_run(SECRET_DSN, seen),
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.backup_database("demo")

    assert result["project"] == "demo"
    assert result["kind"] == "manual"
    assert result["available"] is True
    assert SECRET_DSN not in repr(result)
    assert len(seen) == 1

    project_dir = tmp_path / "backups" / "demo"
    dump = next(project_dir.glob("*.dump"))
    metadata = next(project_dir.glob("*.json"))
    assert stat.S_IMODE(dump.stat().st_mode) == 0o600
    assert stat.S_IMODE(metadata.stat().st_mode) == 0o600
    assert SECRET_DSN not in metadata.read_text(encoding="utf-8")
    assert SECRET_DSN.encode() not in dump.read_bytes()


def test_backup_failure_removes_partial_dump(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = make_registry(tmp_path / "project")

    def failed_run(arguments, **kwargs):
        kwargs["stdout"].write(b"partial")
        return __import__("subprocess").CompletedProcess(arguments, 2)

    monkeypatch.setattr("runner_mcp.database_manager.subprocess.run", failed_run)
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    with pytest.raises(DatabaseManagerError, match="backup command failed"):
        manager.backup_database("demo")

    project_dir = tmp_path / "backups" / "demo"
    assert list(project_dir.glob("*.dump")) == []
    assert list(project_dir.glob("*.json")) == []


def test_emergency_stop_blocks_new_backup(tmp_path: Path) -> None:
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path, stopped=True),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    with pytest.raises(OperatorStopActive):
        manager.backup_database("demo")


def test_list_backups_returns_metadata_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict] = []
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        fake_backup_run(SECRET_DSN, seen),
    )
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )
    manager.backup_database("demo")

    results = manager.list_backups("demo")

    assert len(results) == 1
    assert set(results[0]) == {
        "backup_id",
        "project",
        "kind",
        "created_at",
        "size_bytes",
        "engine",
        "available",
    }
    assert str(tmp_path) not in repr(results)
    assert SECRET_DSN not in repr(results)


def test_restore_preflight_is_read_only_private_and_uses_fixed_pg_restore(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_root = tmp_path / "backups"
    backup_id, dump, metadata = write_restore_backup(backup_root)
    pg_restore = make_pg_restore(tmp_path)
    before_dump = dump.read_bytes()
    before_metadata = metadata.read_bytes()
    seen: list[tuple[list[str], dict]] = []

    def fake_run(arguments, **kwargs):
        seen.append((list(arguments), dict(kwargs)))
        assert kwargs["stdin"] is __import__("subprocess").DEVNULL
        assert kwargs["stdout"] is __import__("subprocess").DEVNULL
        assert kwargs["stderr"] is __import__("subprocess").DEVNULL
        assert kwargs["shell"] is False
        assert kwargs["check"] is False
        assert kwargs["timeout"] == 60
        assert "PGDATABASE" not in kwargs["env"]
        assert SECRET_DSN not in repr(kwargs["env"])
        return __import__("subprocess").CompletedProcess(arguments, 0)

    monkeypatch.setattr("runner_mcp.database_manager.subprocess.run", fake_run)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path, stopped=True),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=pg_restore,
        prepare_storage=False,
    )

    result = manager.restore_preflight("demo", backup_id)

    assert result == {
        "project": "demo",
        "backup_id": backup_id,
        "kind": "manual",
        "created_at": "2026-09-24T05:00:00+00:00",
        "size_bytes": len(before_dump),
        "engine": "postgresql",
        "available": True,
        "eligible": True,
        "preflight_state": "eligible",
    }
    assert len(seen) == 1
    assert seen[0][0] == [str(pg_restore), "--list", str(dump)]
    assert dump.read_bytes() == before_dump
    assert metadata.read_bytes() == before_metadata
    rendered = repr(result)
    assert str(backup_root) not in rendered
    assert str(pg_restore) not in rendered
    assert SECRET_DSN not in rendered
    assert "sha256" not in rendered.lower()


def test_restore_preflight_rejects_invalid_id_before_backup_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_root = tmp_path / "backups"
    backup_root.mkdir(mode=0o700)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )
    monkeypatch.setattr(
        manager,
        "_restore_project_dir",
        lambda _project: (_ for _ in ()).throw(
            AssertionError("filesystem traversal reached")
        ),
    )

    with pytest.raises(DatabaseManagerError, match="Invalid backup identifier"):
        manager.restore_preflight("demo", "../private")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("project", "other", "identity mismatch"),
        ("engine", "mysql", "engine"),
        ("kind", "other", "kind"),
        ("size_bytes", 0, "size"),
    ],
)
def test_restore_preflight_rejects_tampered_metadata(
    tmp_path: Path,
    field: str,
    value,
    message: str,
) -> None:
    backup_root = tmp_path / "backups"
    backup_id, _dump, metadata = write_restore_backup(backup_root)
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    payload[field] = value
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    metadata.chmod(0o600)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match=message):
        manager.restore_preflight("demo", backup_id)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_restore_preflight_rejects_nonstandard_metadata_json(
    tmp_path: Path,
    constant: str,
) -> None:
    backup_root = tmp_path / "backups"
    backup_id, _dump, metadata = write_restore_backup(backup_root)
    text = metadata.read_text(encoding="utf-8").replace(
        '"size_bytes": 29',
        f'"size_bytes": {constant}',
    )
    metadata.write_text(text, encoding="utf-8")
    metadata.chmod(0o600)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="non-standard JSON"):
        manager.restore_preflight("demo", backup_id)


def test_restore_preflight_rejects_duplicate_metadata_keys(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_id, _dump, metadata = write_restore_backup(backup_root)
    text = metadata.read_text(encoding="utf-8").replace(
        '"engine": "postgresql"',
        '"engine": "postgresql", "engine": "postgresql"',
    )
    metadata.write_text(text, encoding="utf-8")
    metadata.chmod(0o600)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="duplicate keys"):
        manager.restore_preflight("demo", backup_id)


@pytest.mark.parametrize("target", ["metadata", "dump"])
def test_restore_preflight_rejects_symlink_files_without_following_referent(
    tmp_path: Path,
    target: str,
) -> None:
    backup_root = tmp_path / "backups"
    backup_id, dump, metadata = write_restore_backup(backup_root)
    victim = metadata if target == "metadata" else dump
    original = victim.read_bytes()
    referent = tmp_path / f"outside-{target}"
    referent.write_bytes(original)
    referent.chmod(0o600)
    victim.unlink()
    victim.symlink_to(referent)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="unsafe"):
        manager.restore_preflight("demo", backup_id)

    assert referent.read_bytes() == original


@pytest.mark.parametrize("target", ["metadata", "dump"])
def test_restore_preflight_rejects_broad_file_permissions(
    tmp_path: Path,
    target: str,
) -> None:
    backup_root = tmp_path / "backups"
    backup_id, dump, metadata = write_restore_backup(backup_root)
    (metadata if target == "metadata" else dump).chmod(0o640)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="permissions"):
        manager.restore_preflight("demo", backup_id)


def test_restore_preflight_rejects_dump_size_mismatch(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_id, dump, _metadata = write_restore_backup(backup_root)
    dump.write_bytes(dump.read_bytes() + b"tamper")
    dump.chmod(0o600)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="size"):
        manager.restore_preflight("demo", backup_id)


def test_restore_preflight_rejects_untrusted_pg_restore_path(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_id, _dump, _metadata = write_restore_backup(backup_root)
    executable = make_pg_restore(tmp_path)
    link = tmp_path / "pg_restore-link"
    link.symlink_to(executable)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=link,
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="pg_restore"):
        manager.restore_preflight("demo", backup_id)


def test_restore_preflight_rejects_non_executable_pg_restore(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_id, _dump, _metadata = write_restore_backup(backup_root)
    executable = tmp_path / "pg_restore"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o600)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=executable,
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError, match="pg_restore"):
        manager.restore_preflight("demo", backup_id)


def test_readonly_manager_refuses_broad_storage_without_chmod(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_root.mkdir(mode=0o750)
    backup_root.chmod(0o750)

    with pytest.raises(DatabaseManagerError, match="0700"):
        DatabaseManager(
            registry=make_registry(tmp_path / "project"),
            safety=make_guard(tmp_path),
            backup_root=backup_root,
            secret_values=ExplodingSecrets(),
            pg_restore_path=make_pg_restore(tmp_path),
            prepare_storage=False,
        )

    assert stat.S_IMODE(backup_root.stat().st_mode) == 0o750


def test_restore_preflight_failure_is_bounded_and_hides_private_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_root = tmp_path / "sensitive-backups"
    backup_id, _dump, _metadata = write_restore_backup(backup_root)
    pg_restore = make_pg_restore(tmp_path)
    sensitive = str(tmp_path / "private-pg-error")

    def fail_run(_arguments, **_kwargs):
        raise OSError(sensitive)

    monkeypatch.setattr("runner_mcp.database_manager.subprocess.run", fail_run)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=pg_restore,
        prepare_storage=False,
    )

    with pytest.raises(DatabaseManagerError) as captured:
        manager.restore_preflight("demo", backup_id)

    assert str(captured.value) == "Database restore preflight command failed"
    assert sensitive not in str(captured.value)
    assert str(backup_root) not in str(captured.value)


def test_restore_preflight_production_is_ineligible_without_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_root = tmp_path / "backups"
    backup_root.mkdir(mode=0o700)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project", environment="production"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("pg_restore must not run")
        ),
    )

    result = manager.restore_preflight(
        "demo",
        "20260924T050000Z-" + ("b" * 12),
    )

    assert result == {
        "project": "demo",
        "backup_id": "20260924T050000Z-" + ("b" * 12),
        "eligible": False,
        "preflight_state": "ineligible_environment",
    }


def test_restore_preflight_refuses_concurrent_database_operation(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_root.mkdir(mode=0o700)
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=backup_root,
        secret_values=ExplodingSecrets(),
        pg_restore_path=make_pg_restore(tmp_path),
        prepare_storage=False,
    )
    lock = manager._lock_for("demo")
    assert lock.acquire(blocking=False)
    try:
        with pytest.raises(DatabaseManagerError, match="already in progress"):
            manager.restore_preflight(
                "demo",
                "20260924T050000Z-" + ("c" * 12),
            )
    finally:
        lock.release()


def test_migration_status_is_read_only_and_redacts_dsn_and_paths(tmp_path: Path) -> None:
    status_script = make_executable(
        tmp_path / "status.sh",
        'printf "%s\\n" "$DATABASE_URL"; pwd; printf "password=super-secret-value\\n"',
    )
    apply_script = make_executable(tmp_path / "apply.sh", 'printf "applied\\n"')
    registry = make_registry(
        tmp_path / "project",
        status_script=status_script,
        apply_script=apply_script,
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path, stopped=True),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.migration_status("demo")

    assert result["status"] == "ok"
    assert SECRET_DSN not in result["output"]
    assert str(tmp_path / "project") not in result["output"]
    assert "super-secret-value" not in result["output"]
    assert "[REDACTED]" in result["output"]
    assert "[PRIVATE_PATH]" in result["output"]


def test_migration_output_truncation_does_not_leak_partial_dsn(tmp_path: Path) -> None:
    long_secret = "postgresql://" + ("s" * 5000) + "@db.example.invalid/app"
    status_script = make_executable(
        tmp_path / "status.sh",
        'printf "prefix-%s-suffix\\n" "$DATABASE_URL"',
    )
    apply_script = make_executable(tmp_path / "apply.sh", "exit 0")
    registry = make_registry(
        tmp_path / "project",
        status_script=status_script,
        apply_script=apply_script,
        max_output_bytes=4096,
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": long_secret},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.migration_status("demo")

    assert long_secret not in result["output"]
    assert "s" * 1000 not in result["output"]
    assert result["output_truncated"] is False
    assert "[REDACTED]" in result["output"]


def test_apply_migrations_creates_pre_migration_backup_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_script = make_executable(tmp_path / "status.sh", "exit 0")
    apply_script = make_executable(
        tmp_path / "apply.sh",
        'printf "migration-applied\\n"',
    )
    registry = make_registry(
        tmp_path / "project",
        status_script=status_script,
        apply_script=apply_script,
    )
    seen: list[dict] = []
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        fake_backup_run(SECRET_DSN, seen),
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.apply_migrations("demo")

    assert result["status"] == "applied"
    assert result["pre_migration_backup"]["kind"] == "pre_migration"
    assert result["database_restore_performed"] is False
    assert "migration-applied" in result["output"]
    backups = manager.list_backups("demo")
    assert backups[0]["kind"] == "pre_migration"


def test_failed_migration_keeps_backup_and_does_not_restore(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_script = make_executable(tmp_path / "status.sh", "exit 0")
    apply_script = make_executable(
        tmp_path / "apply.sh",
        'printf "migration failed\\n"; exit 9',
    )
    registry = make_registry(
        tmp_path / "project",
        status_script=status_script,
        apply_script=apply_script,
    )
    monkeypatch.setattr(
        "runner_mcp.database_manager.subprocess.run",
        fake_backup_run(SECRET_DSN, []),
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.apply_migrations("demo")

    assert result["status"] == "failed"
    assert result["exit_code"] == 9
    assert result["database_restore_performed"] is False
    assert manager.list_backups("demo")[0]["available"] is True


def test_migration_timeout_terminates_process(tmp_path: Path) -> None:
    status_script = make_executable(tmp_path / "status.sh", "sleep 30")
    apply_script = make_executable(tmp_path / "apply.sh", "exit 0")
    registry = make_registry(
        tmp_path / "project",
        status_script=status_script,
        apply_script=apply_script,
        timeout_seconds=1,
    )
    manager = DatabaseManager(
        registry=registry,
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
        terminate_grace_seconds=0.2,
    )

    result = manager.migration_status("demo")

    assert result["status"] == "timed_out"
    assert result["exit_code"] is not None


def test_database_credential_never_comes_from_process_environment_by_accident(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNNER_MCP_DB_DEMO", "wrong-external-value")
    status_script = make_executable(
        tmp_path / "status.sh",
        'printf "%s\\n" "$DATABASE_URL"',
    )
    apply_script = make_executable(tmp_path / "apply.sh", "exit 0")
    manager = DatabaseManager(
        registry=make_registry(
            tmp_path / "project",
            status_script=status_script,
            apply_script=apply_script,
        ),
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )

    result = manager.migration_status("demo")

    assert "wrong-external-value" not in result["output"]
    assert SECRET_DSN not in result["output"]


def test_tampered_backup_metadata_is_ignored(tmp_path: Path) -> None:
    manager = DatabaseManager(
        registry=make_registry(tmp_path / "project"),
        safety=make_guard(tmp_path),
        backup_root=tmp_path / "backups",
        secret_values={"RUNNER_MCP_DB_DEMO": SECRET_DSN},
        pg_dump_path=make_pg_dump(tmp_path),
    )
    project_dir = tmp_path / "backups" / "demo"
    project_dir.mkdir(parents=True)
    bad_id = "20260920T080000Z-" + ("a" * 12)
    (project_dir / f"{bad_id}.json").write_text(
        json.dumps(
            {
                "backup_id": bad_id,
                "project": "other",
                "kind": "manual",
                "created_at": "2026-09-20T08:00:00+00:00",
                "size_bytes": 123,
                "engine": "postgresql",
            }
        ),
        encoding="utf-8",
    )

    assert manager.list_backups("demo") == []
