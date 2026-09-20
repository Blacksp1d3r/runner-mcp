from pathlib import Path

import pytest

from runner_mcp.onboarding import (
    OnboardingError,
    SetupAnswers,
    disable_operator_stop,
    enable_operator_stop,
    install_private_configuration,
    operator_stop_status,
    run_doctor,
)


def installed(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "private-config",
        answers=SetupAnswers(
            resource_url="https://mcp.example.invalid/mcp",
            auth_issuer="https://auth.example.invalid/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project_root,
        ),
    )
    return paths


def test_emergency_stop_activation_and_unlock(tmp_path: Path) -> None:
    paths = installed(tmp_path)

    enable_operator_stop(paths.config_dir)
    _, guard = operator_stop_status(paths.config_dir)
    assert guard.status().stop_active is True

    with pytest.raises(OnboardingError, match="UNLOCK"):
        disable_operator_stop(paths.config_dir, confirmation="yes")

    assert paths.stop_file.exists()
    disable_operator_stop(paths.config_dir, confirmation="UNLOCK")
    assert not paths.stop_file.exists()


def test_doctor_reports_active_stop_as_warning(tmp_path: Path) -> None:
    paths = installed(tmp_path)
    enable_operator_stop(paths.config_dir)

    checks = run_doctor(paths.config_dir)
    emergency = next(check for check in checks if check.name == "operator emergency stop")

    assert emergency.status == "WARN"
    assert "active" in emergency.detail


def test_emergency_stop_refuses_symlink(tmp_path: Path) -> None:
    paths = installed(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("unchanged\n", encoding="utf-8")
    paths.stop_file.symlink_to(outside)

    with pytest.raises(OnboardingError, match="symlink"):
        enable_operator_stop(paths.config_dir)

    assert outside.read_text(encoding="utf-8") == "unchanged\n"
