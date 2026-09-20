import os
import stat
from pathlib import Path

import pytest

from runner_mcp.config_manager import (
    ConfigManagerError,
    add_project,
    add_test_profile,
    list_projects,
    list_test_profiles,
    remove_project,
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
