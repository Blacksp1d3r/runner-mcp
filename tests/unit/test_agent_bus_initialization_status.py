"""Read-only first-host Agent Bus base status; never auto-provision credentials."""
from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.cli import main
from runner_mcp.config_manager import ConfigManagerError, agent_bus_config_status
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


def test_missing_private_base_is_explicit_and_has_no_side_effects(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    config_dir = tmp_path / "not-yet-created"
    assert agent_bus_config_status(config_dir) == {
        "configured": False, "base_config_not_initialized": True,
    }
    before = sorted(tmp_path.iterdir())
    assert main(["--config-dir", str(config_dir), "agent-bus", "status"]) == 0
    printed = capsys.readouterr()
    assert "base_config_not_initialized" in printed.out
    assert "runner-mcp setup" in printed.out
    assert printed.err == ""
    assert sorted(tmp_path.iterdir()) == before


def test_empty_owner_private_root_is_not_initialized(tmp_path: Path) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    assert agent_bus_config_status(root)["base_config_not_initialized"]
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("mode", [0o755, 0o770])
def test_wrong_mode_empty_private_root_is_not_disguised_as_missing(
    tmp_path: Path, mode: int,
) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    root.chmod(mode)
    with pytest.raises(ConfigManagerError, match="custody is invalid"):
        agent_bus_config_status(root)


def test_symlink_private_root_is_denied(tmp_path: Path) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    link = tmp_path / "alias"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ConfigManagerError, match="symlink"):
        agent_bus_config_status(link)


def test_partial_base_files_are_denied_not_initialized(tmp_path: Path) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    (root / "runner-mcp.env").write_text("EMPTY=1\n", encoding="utf-8")
    (root / "runner-mcp.env").chmod(0o600)
    with pytest.raises(ConfigManagerError):
        agent_bus_config_status(root)
    assert not (root / "projects.yml").exists()


def test_foreign_mode_private_base_file_is_denied(tmp_path: Path) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    env = root / "runner-mcp.env"
    env.write_text("EMPTY=1\n", encoding="utf-8")
    env.chmod(0o644)
    with pytest.raises(ConfigManagerError, match="unsafe"):
        agent_bus_config_status(root)


def test_symlinked_ancestor_is_denied(tmp_path: Path) -> None:
    root = tmp_path / "real"
    root.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(ConfigManagerError, match="symlink"):
        agent_bus_config_status(alias / "nested" / "missing")


def test_cli_symlink_alias_fails_closed_without_creating_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    assert main(["--config-dir", str(alias), "agent-bus", "status"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "symlink" in output.err
    assert list(root.iterdir()) == []


def test_symlinked_base_file_is_denied(tmp_path: Path) -> None:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    (root / "runner-mcp.env").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ConfigManagerError, match="unsafe"):
        agent_bus_config_status(root)


def test_existing_valid_base_without_relay_remains_unconfigured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "private"
    project = tmp_path / "project"
    project.mkdir()
    install_private_configuration(
        config_dir=root,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    assert agent_bus_config_status(root) == {"configured": False}
    before = sorted(root.iterdir())
    assert main(["--config-dir", str(root), "agent-bus", "status"]) == 0
    assert capsys.readouterr().out.strip() == "not configured"
    assert sorted(root.iterdir()) == before
