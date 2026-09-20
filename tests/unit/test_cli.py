from pathlib import Path

import pytest

from runner_mcp.cli import main
from runner_mcp.onboarding import (
    SetupAnswers,
    install_private_configuration,
    load_env_file,
)


def install_config(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"
    paths = install_private_configuration(
        config_dir=config_dir,
        answers=SetupAnswers(
            resource_url="https://mcp.example.invalid/mcp",
            auth_issuer="https://auth.example.invalid/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project_root,
        ),
    )
    return paths, project_root


def test_status_does_not_print_private_paths_or_bearer_value(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    token = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    result = main(["--config-dir", str(paths.config_dir), "status"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Mode: operational" in captured.out
    assert "demo: Demo" in captured.out
    assert str(project_root) not in captured.out
    assert str(paths.config_dir) not in captured.out
    assert token not in captured.out
    assert token not in captured.err


def test_doctor_command_reports_no_failures(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)

    result = main(["--config-dir", str(paths.config_dir), "doctor"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Doctor found no failures" in captured.out


def test_emergency_stop_cli_on_status_and_off(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "on"]
    ) == 0
    capsys.readouterr()

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "status"]
    ) == 0
    status_output = capsys.readouterr()
    assert status_output.out.strip() == "ACTIVE"

    monkeypatch.setattr("builtins.input", lambda _: "UNLOCK")
    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "off"]
    ) == 0
    capsys.readouterr()

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "status"]
    ) == 0
    final_output = capsys.readouterr()
    assert final_output.out.strip() == "inactive"


def test_emergency_stop_cli_refuses_wrong_unlock_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)
    main(["--config-dir", str(paths.config_dir), "emergency-stop", "on"])
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _: "yes")
    result = main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "off"]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "UNLOCK" in captured.err
    assert paths.stop_file.exists()


def test_serve_refuses_public_bind_without_explicit_override(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "serve",
            "--host",
            "0.0.0.0",
        ]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "--allow-public-bind" in captured.err


def test_setup_wizard_creates_private_configuration_without_printing_secret(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"

    answers = iter(
        [
            "",
            "demo",
            "Demo",
            "example/demo",
            str(project_root),
            "",
            "",
            "",
            "",
            "",
            "YES",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = main(["--config-dir", str(config_dir), "setup"])
    captured = capsys.readouterr()

    assert result == 0
    env_file = config_dir / "runner-mcp.env"
    assert env_file.exists()
    token = load_env_file(env_file)["RUNNER_MCP_BEARER_TOKEN"]
    assert token not in captured.out
    assert str(config_dir) not in captured.out
    assert "Configuration created successfully" in captured.out


def test_setup_wizard_cancellation_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"

    answers = iter(
        [
            "",
            "demo",
            "Demo",
            "example/demo",
            str(project_root),
            "",
            "",
            "",
            "",
            "",
            "NO",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = main(["--config-dir", str(config_dir), "setup"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Setup cancelled" in captured.out
    assert not (config_dir / "runner-mcp.env").exists()


def test_project_cli_add_and_list_is_path_safe(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)
    second_root = tmp_path / "second"
    second_root.mkdir()

    result = main([
        "--config-dir", str(paths.config_dir),
        "project", "add", "second",
        "--name", "Second",
        "--repository", "example/second",
        "--root", str(second_root),
    ])
    assert result == 0
    capsys.readouterr()

    result = main(["--config-dir", str(paths.config_dir), "project", "list"])
    captured = capsys.readouterr()
    assert result == 0
    assert "second: Second (example/second)" in captured.out
    assert str(second_root) not in captured.out


def test_test_profile_cli_custom_add_and_list_hides_executable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    executable = project_root / "check"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)

    result = main([
        "--config-dir", str(paths.config_dir),
        "test-profile", "add", "demo", "checks",
        "--preset", "custom",
        "--executable", str(executable),
    ])
    assert result == 0
    capsys.readouterr()

    result = main([
        "--config-dir", str(paths.config_dir),
        "test-profile", "list", "demo",
    ])
    captured = capsys.readouterr()
    assert result == 0
    assert "checks: timeout=300s" in captured.out
    assert str(executable) not in captured.out
