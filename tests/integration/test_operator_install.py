from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_operator_installer_creates_working_local_wrapper(tmp_path: Path) -> None:
    service_user = subprocess.run(
        ["id", "-un"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    fake_runner = tmp_path / "fake-runner"
    fake_runner.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n",
        encoding="utf-8",
    )
    fake_runner.chmod(0o755)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    operator_bin = tmp_path / "operator-bin"

    env = os.environ.copy()
    env["RUNNER_MCP_SERVICE_BIN"] = str(fake_runner)
    env["RUNNER_MCP_SERVICE_CONFIG_DIR"] = str(config_dir)
    env["RUNNER_MCP_OPERATOR_BIN_DIR"] = str(operator_bin)

    subprocess.run(
        ["bash", "install-operator.sh", service_user],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    wrapper = operator_bin / "runner-mcp"
    assert wrapper.exists()
    assert wrapper.stat().st_mode & 0o777 == 0o700

    result = subprocess.run(
        [str(wrapper), "guide"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.splitlines() == [
        "--config-dir",
        str(config_dir),
        "guide",
    ]


def test_operator_installer_rejects_invalid_service_user(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["RUNNER_MCP_OPERATOR_BIN_DIR"] = str(tmp_path / "bin")
    result = subprocess.run(
        ["bash", "install-operator.sh", "../bad-user"],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "invalid service-user" in result.stderr


def _existing_account_other_than_self() -> str:
    """Find a real Linux account, resolvable through getent, that differs from
    the current account. Common low-numbered system accounts exist on
    virtually every Linux host regardless of container/CI flavor."""
    current = subprocess.run(
        ["id", "-un"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    for candidate in ("root", "daemon", "nobody", "bin", "sys"):
        if candidate == current:
            continue
        lookup = subprocess.run(
            ["getent", "passwd", candidate],
            check=False,
            capture_output=True,
            text=True,
        )
        if lookup.returncode == 0 and lookup.stdout.strip():
            return candidate
    pytest.skip("no distinct system account available to exercise the cross-account path")


def test_operator_installer_requires_sudo_for_a_different_account(tmp_path: Path) -> None:
    """Deterministically exercises the missing-sudo failure without depending
    on whether sudo actually happens to be installed on the machine running
    this test: the check is forced by shrinking PATH to a directory that
    contains every binary the installer needs up to that check, minus sudo."""
    other_account = _existing_account_other_than_self()

    restricted_bin = tmp_path / "restricted-bin"
    restricted_bin.mkdir()
    for tool in ("bash", "getent", "cut", "id"):
        real_path = shutil.which(tool)
        assert real_path is not None, f"{tool} must be available to run this test"
        (restricted_bin / tool).symlink_to(real_path)

    env = {
        "PATH": str(restricted_bin),
        "HOME": str(tmp_path / "home"),
        "RUNNER_MCP_OPERATOR_BIN_DIR": str(tmp_path / "bin"),
    }

    result = subprocess.run(
        ["bash", "install-operator.sh", other_account],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "sudo is required" in result.stderr
    assert not (tmp_path / "bin").exists()
