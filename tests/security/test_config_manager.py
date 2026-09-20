import os
import stat
from pathlib import Path

import pytest

from runner_mcp.config_manager import (
    ConfigManagerError,
    add_project,
    add_service_config,
    add_test_profile,
    list_projects,
    list_service_configs,
    list_test_profiles,
    remove_project,
    remove_service_config,
    remove_test_profile,
)
from runner_mcp.onboarding import SetupAnswers, install_private_configuration, read_private_runtime


def installed(tmp_path: Path):
    first_root = tmp_path / "first"
    first_root.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "config",
        answers=SetupAnswers(
            resource_url="https://mcp.example.invalid/mcp",
            auth_issuer="https://auth.example.invalid/",
            project_code="first",
            project_name="First",
            repository="example/first",
            project_root=first_root,
        ),
    )
    return paths, first_root


def make_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(path, 0o755)


def test_project_add_and_list_do_not_expose_roots(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    second_root = tmp_path / "second"
    second_root.mkdir()

    added = add_project(
        paths.config_dir,
        code="second",
        display_name="Second",
        repository="example/second",
        root=second_root,
    )
    listed = list_projects(paths.config_dir)

    assert added["code"] == "second"
    assert {item["code"] for item in listed} == {"first", "second"}
    assert str(second_root) not in repr(listed)


def test_last_project_cannot_be_removed(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)

    with pytest.raises(ConfigManagerError, match="last configured"):
        remove_project(paths.config_dir, code="first")


def test_project_removal_preserves_other_project(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    second_root = tmp_path / "second"
    second_root.mkdir()
    add_project(
        paths.config_dir,
        code="second",
        display_name="Second",
        repository="example/second",
        root=second_root,
    )

    remove_project(paths.config_dir, code="first")

    listed = list_projects(paths.config_dir)
    assert [item["code"] for item in listed] == ["second"]


def test_pytest_preset_detects_project_virtual_environment(tmp_path: Path) -> None:
    paths, root = installed(tmp_path)
    make_executable(root / ".venv" / "bin" / "python")

    result = add_test_profile(
        paths.config_dir,
        project="first",
        name="unit",
        preset="pytest",
    )
    listed = list_test_profiles(paths.config_dir, project="first")

    assert result["name"] == "unit"
    assert listed[0]["name"] == "unit"
    assert ".venv" not in repr(listed)


def test_ruff_preset_detects_project_virtual_environment(tmp_path: Path) -> None:
    paths, root = installed(tmp_path)
    make_executable(root / ".venv" / "bin" / "ruff")

    result = add_test_profile(
        paths.config_dir,
        project="first",
        name="lint",
        preset="ruff",
    )

    assert result["name"] == "lint"


def test_custom_profile_keeps_arguments_as_literal_values(tmp_path: Path) -> None:
    paths, root = installed(tmp_path)
    executable = root / "tools" / "check"
    make_executable(executable)

    add_test_profile(
        paths.config_dir,
        project="first",
        name="custom",
        preset="custom",
        executable=executable,
        arguments=["literal;not-a-shell-command"],
    )

    _, _, registry = read_private_runtime(paths.config_dir)
    profile = registry.projects["first"].test_profiles["custom"]
    assert profile.argv[1] == "literal;not-a-shell-command"


def test_custom_profile_rejects_symlink_executable(tmp_path: Path) -> None:
    paths, root = installed(tmp_path)
    target = root / "tools" / "real"
    make_executable(target)
    link = root / "tools" / "link"
    link.symlink_to(target)

    with pytest.raises(ConfigManagerError, match="symlinks"):
        add_test_profile(
            paths.config_dir,
            project="first",
            name="unsafe",
            preset="custom",
            executable=link,
        )


def test_profile_removal_updates_private_config(tmp_path: Path) -> None:
    paths, root = installed(tmp_path)
    executable = root / "tools" / "check"
    make_executable(executable)
    add_test_profile(
        paths.config_dir,
        project="first",
        name="custom",
        preset="custom",
        executable=executable,
    )

    remove_test_profile(paths.config_dir, project="first", name="custom")

    assert list_test_profiles(paths.config_dir, project="first") == []


def test_project_config_remains_private_after_edits(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    second_root = tmp_path / "second"
    second_root.mkdir()

    add_project(
        paths.config_dir,
        code="second",
        display_name="Second",
        repository="example/second",
        root=second_root,
    )

    mode = stat.S_IMODE(paths.projects_file.stat().st_mode)
    assert mode == 0o600


def test_project_add_rejects_symlink_root(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    target = tmp_path / "real-project"
    target.mkdir()
    link = tmp_path / "project-link"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(ConfigManagerError, match="symlinks"):
        add_project(
            paths.config_dir,
            code="linked",
            display_name="Linked",
            repository="example/linked",
            root=link,
        )


def test_service_config_add_list_and_remove_hides_private_unit(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)

    added = add_service_config(
        paths.config_dir,
        project="first",
        name="web",
        unit="private-web.service",
        health_url="http://127.0.0.1:9999/health",
        allow_restart=True,
    )
    listed = list_service_configs(paths.config_dir, project="first")

    assert added["name"] == "web"
    assert added["can_restart"] is True
    assert listed == [added]
    assert "private-web.service" not in repr(listed)
    assert "127.0.0.1" not in repr(listed)

    remove_service_config(paths.config_dir, project="first", name="web")
    assert list_service_configs(paths.config_dir, project="first") == []


def test_service_config_is_read_only_by_default(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)

    added = add_service_config(
        paths.config_dir,
        project="first",
        name="web",
        unit="private-web.service",
    )

    assert added["can_start"] is False
    assert added["can_stop"] is False
    assert added["can_restart"] is False


def test_database_config_secret_stays_out_of_project_yaml(tmp_path: Path) -> None:
    from runner_mcp.config_manager import add_database_config, list_database_configs
    from runner_mcp.onboarding import load_env_file

    paths, _ = installed(tmp_path)
    secret = "postgresql://user:very-private@example.invalid/app"
    result = add_database_config(paths.config_dir, project="first", dsn=secret)
    listed = list_database_configs(paths.config_dir)

    assert result["configured"] is True
    assert listed[0]["configured"] is True
    assert secret not in paths.projects_file.read_text(encoding="utf-8")
    assert secret in load_env_file(paths.env_file).values()
    assert secret not in repr(result)
    assert secret not in repr(listed)


def test_database_config_removal_removes_private_secret(tmp_path: Path) -> None:
    from runner_mcp.config_manager import add_database_config, remove_database_config
    from runner_mcp.onboarding import load_env_file

    paths, _ = installed(tmp_path)
    secret = "postgresql://user:remove-me@example.invalid/app"
    add_database_config(paths.config_dir, project="first", dsn=secret)
    remove_database_config(paths.config_dir, project="first")

    assert secret not in load_env_file(paths.env_file).values()
    _, _, registry = read_private_runtime(paths.config_dir)
    assert registry.projects["first"].database is None


def test_custom_migration_config_uses_literal_argv(tmp_path: Path) -> None:
    from runner_mcp.config_manager import add_database_config, add_migration_config

    paths, root = installed(tmp_path)
    add_database_config(
        paths.config_dir,
        project="first",
        dsn="postgresql://user:secret@example.invalid/app",
    )
    status = root / "migration-status"
    apply = root / "migration-apply"
    make_executable(status)
    make_executable(apply)

    add_migration_config(
        paths.config_dir,
        project="first",
        preset="custom",
        status_executable=status,
        status_arguments=["literal;not-shell"],
        apply_executable=apply,
        apply_arguments=["upgrade", "head"],
    )

    _, _, registry = read_private_runtime(paths.config_dir)
    migration = registry.projects["first"].database.migrations
    assert migration is not None
    assert migration.status_argv[1] == "literal;not-shell"


def test_deployment_config_creates_private_storage_and_hides_path(tmp_path: Path) -> None:
    from runner_mcp.config_manager import (
        add_deployment_config,
        add_service_config,
        list_deployment_configs,
    )

    paths, _ = installed(tmp_path)
    add_service_config(
        paths.config_dir,
        project="first",
        name="web",
        unit="private-web.service",
        health_url="http://127.0.0.1:9999/health",
        allow_restart=True,
    )
    release_root = tmp_path / "staging-releases"
    result = add_deployment_config(
        paths.config_dir,
        project="first",
        release_root=release_root,
        service="web",
    )
    listed = list_deployment_configs(paths.config_dir)

    assert result["configured"] is True
    assert str(release_root) not in repr(result)
    assert str(release_root) not in repr(listed)
    assert stat.S_IMODE(release_root.stat().st_mode) == 0o700
    assert stat.S_IMODE((release_root / "releases").stat().st_mode) == 0o700
    assert stat.S_IMODE((release_root / ".runtime-home").stat().st_mode) == 0o700


def test_removing_deployment_config_preserves_release_data(tmp_path: Path) -> None:
    from runner_mcp.config_manager import (
        add_deployment_config,
        add_service_config,
        remove_deployment_config,
    )

    paths, _ = installed(tmp_path)
    add_service_config(
        paths.config_dir,
        project="first",
        name="web",
        unit="private-web.service",
        health_url="http://127.0.0.1:9999/health",
        allow_restart=True,
    )
    release_root = tmp_path / "staging-releases"
    add_deployment_config(
        paths.config_dir,
        project="first",
        release_root=release_root,
        service="web",
    )
    marker = release_root / "releases" / "keep-me"
    marker.mkdir()

    remove_deployment_config(paths.config_dir, project="first")

    assert marker.exists()
    _, _, registry = read_private_runtime(paths.config_dir)
    assert registry.projects["first"].deployment is None


def test_deployment_config_requires_restartable_health_checked_service(tmp_path: Path) -> None:
    from runner_mcp.config_manager import add_deployment_config, add_service_config

    paths, _ = installed(tmp_path)
    add_service_config(
        paths.config_dir,
        project="first",
        name="web",
        unit="private-web.service",
    )
    with pytest.raises(ConfigManagerError, match="allow restart"):
        add_deployment_config(
            paths.config_dir,
            project="first",
            release_root=tmp_path / "staging-releases",
            service="web",
        )
