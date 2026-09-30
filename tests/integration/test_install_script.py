from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _fake_python(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -eu
if [[ "${1:-}" == "-m" && "${2:-}" == "venv" && "${3:-}" == "--help" ]]; then
  exit 0
fi
if [[ "${1:-}" == "-m" && "${2:-}" == "venv" ]]; then
  venv="${3}"
  mkdir -p "${venv}/bin"
  cat >"${venv}/bin/python" <<'INNER'
#!/usr/bin/env bash
set -eu
if [[ "${1:-}" == "-m" && "${2:-}" == "pip" && "${3:-}" == "--version" ]]; then
  echo "pip 24.0"
  exit 0
fi
if [[ "${1:-}" == "-m" && "${2:-}" == "pip" && "${3:-}" == "install" ]]; then
  exit 0
fi
if [[ "${1:-}" == "-" ]]; then
  source_text="$(cat)"
  if [[ "$source_text" == *"importlib.import_module"* ]]; then
    echo "ValueError: bad marshal data" >&2
    exit 1
  fi
  exit 0
fi
exit 1
INNER
  chmod +x "${venv}/bin/python"
  cat >"${venv}/bin/runner-mcp" <<'INNER'
#!/usr/bin/env bash
exit 0
INNER
  chmod +x "${venv}/bin/runner-mcp"
  exit 0
fi
if [[ "${1:-}" == "-" ]]; then
  cat >/dev/null
  exit 0
fi
exit 1
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_installer_fails_closed_on_post_install_import_corruption(tmp_path: Path) -> None:
    fake_python = tmp_path / "python3"
    _fake_python(fake_python)
    install_root = tmp_path / "install"
    bin_dir = tmp_path / "bin"
    env = os.environ.copy()
    env.update(
        {
            "RUNNER_MCP_PYTHON": str(fake_python),
            "RUNNER_MCP_INSTALL_ROOT": str(install_root),
            "RUNNER_MCP_BIN_DIR": str(bin_dir),
        }
    )

    result = subprocess.run(
        ["bash", "install.sh"],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "installation integrity check failed" in result.stderr
    assert "bad marshal data" in result.stderr
    assert "Do not enable Runner MCP autostart" in result.stderr
    assert not (bin_dir / "runner-mcp").exists()


def test_installer_rejects_unsupported_pip_before_package_install(tmp_path: Path) -> None:
    fake_python = tmp_path / "python3"
    _fake_python(fake_python)
    script = fake_python.read_text(encoding="utf-8")
    fake_python.write_text(
        script.replace('echo "pip 24.0"', 'echo "pip 22.3"'),
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    install_root = tmp_path / "install"
    bin_dir = tmp_path / "bin"
    env = os.environ.copy()
    env.update(
        {
            "RUNNER_MCP_PYTHON": str(fake_python),
            "RUNNER_MCP_INSTALL_ROOT": str(install_root),
            "RUNNER_MCP_BIN_DIR": str(bin_dir),
        }
    )

    result = subprocess.run(
        ["bash", "install.sh"],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "pip 23.2 or newer is required" in result.stderr
    assert "Installing Runner MCP..." not in result.stdout
    assert not (bin_dir / "runner-mcp").exists()
