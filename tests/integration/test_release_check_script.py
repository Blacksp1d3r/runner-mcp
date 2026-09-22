import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "release-check.sh"


def _write_fake(bin_dir: Path, name: str, body: str) -> None:
    path = bin_dir / name
    path.write_text("#!/bin/bash\nset -euo pipefail\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _release_env(tmp_path: Path, *, failing_ruff: bool = False) -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands.log"

    _write_fake(bin_dir, "python", 'printf "python %s\\n" "$*" >>"$RELEASE_LOG"\n')
    _write_fake(
        bin_dir,
        "ruff",
        (
            'printf "ruff %s\\n" "$*" >>"$RELEASE_LOG"\n'
            + ("exit 23\n" if failing_ruff else "")
        ),
    )
    _write_fake(bin_dir, "pytest", 'printf "pytest %s\\n" "$*" >>"$RELEASE_LOG"\n')
    _write_fake(
        bin_dir,
        "git",
        """
printf "git %s\\n" "$*" >>"$RELEASE_LOG"
if [[ "$1" == "merge-base" ]]; then
  printf "base-commit\\n"
fi
""",
    )
    _write_fake(bin_dir, "bash", 'printf "bash %s\\n" "$*" >>"$RELEASE_LOG"\n')

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "RELEASE_LOG": str(log),
            "RUNNER_MCP_RELEASE_PYTHON": "python",
            "RUNNER_MCP_RELEASE_RUFF": "ruff",
            "RUNNER_MCP_RELEASE_PYTEST": "pytest",
            "RUNNER_MCP_RELEASE_BASE": "origin/main",
        }
    )
    return env, log


def test_release_check_runs_validation_in_fail_closed_order(tmp_path: Path) -> None:
    env, log = _release_env(tmp_path)

    completed = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [
        "python -m compileall -q src tests",
        "ruff check .",
        "pytest -q",
        "git merge-base HEAD origin/main",
        "git diff --check base-commit..HEAD",
        "git diff --check",
        "git diff --cached --check",
        "bash scripts/release-artifact-smoke.sh",
        "bash scripts/demo-smoke.sh",
    ]
    assert "GitHub CI remains authoritative" in completed.stdout


def test_release_check_stops_at_first_failed_component(tmp_path: Path) -> None:
    env, log = _release_env(tmp_path, failing_ruff=True)

    completed = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 23
    assert log.read_text(encoding="utf-8").splitlines() == [
        "python -m compileall -q src tests",
        "ruff check .",
    ]
    assert "Pytest" not in completed.stdout
