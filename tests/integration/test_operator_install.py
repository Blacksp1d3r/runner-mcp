from __future__ import annotations

import os
import subprocess
from pathlib import Path


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
