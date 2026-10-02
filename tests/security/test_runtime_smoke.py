from __future__ import annotations

import subprocess
from pathlib import Path

import runner_mcp.runtime_smoke as smoke


class FakeRunner:
    def __init__(self, *, fail_at: int | None = None) -> None:
        self.fail_at = fail_at
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        code = 1 if self.fail_at == len(self.calls) else 0
        return subprocess.CompletedProcess(argv, code, stdout=b"", stderr=b"")


def executable(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.write_bytes(b"placeholder")
    return path


def test_smoke_runs_fixed_32_import_and_8_cli_processes(tmp_path: Path) -> None:
    python = executable(tmp_path, "python")
    launcher = executable(tmp_path, "runner-mcp")
    runner = FakeRunner()

    assert smoke.run_autostart_runtime_smoke(
        python_executable=python,
        runner_mcp_executable=launcher,
        runner=runner,
    )
    assert len(runner.calls) == 40
    assert all(
        call[0] == [str(python), "-B", "-X", "faulthandler", "-"]
        for call in runner.calls[:32]
    )
    assert all(call[0] == [str(launcher), "--help"] for call in runner.calls[32:])
    assert all(call[1]["timeout"] == 10 for call in runner.calls)
    assert all(call[1]["stdout"] is subprocess.DEVNULL for call in runner.calls)
    assert all(call[1]["stderr"] is subprocess.DEVNULL for call in runner.calls)


def test_smoke_preserves_validated_symlink_execution_paths(tmp_path: Path) -> None:
    system_python = executable(tmp_path, "python3.12")
    system_launcher = executable(tmp_path, "runner-mcp.real")
    venv = tmp_path / "venv" / "bin"
    venv.mkdir(parents=True)
    python = venv / "python"
    launcher = venv / "runner-mcp"
    python.symlink_to(system_python)
    launcher.symlink_to(system_launcher)
    runner = FakeRunner()

    assert smoke.run_autostart_runtime_smoke(
        python_executable=python,
        runner_mcp_executable=launcher,
        runner=runner,
    )
    assert all(
        call[0] == [str(python), "-B", "-X", "faulthandler", "-"]
        for call in runner.calls[:32]
    )
    assert all(call[0] == [str(launcher), "--help"] for call in runner.calls[32:])


def test_first_failure_stops_without_retry_loop(tmp_path: Path) -> None:
    python = executable(tmp_path, "python")
    launcher = executable(tmp_path, "runner-mcp")
    runner = FakeRunner(fail_at=3)

    assert not smoke.run_autostart_runtime_smoke(
        python_executable=python,
        runner_mcp_executable=launcher,
        runner=runner,
    )
    assert len(runner.calls) == 3


def test_cli_failure_stops_immediately(tmp_path: Path) -> None:
    python = executable(tmp_path, "python")
    launcher = executable(tmp_path, "runner-mcp")
    runner = FakeRunner(fail_at=33)

    assert not smoke.run_autostart_runtime_smoke(
        python_executable=python,
        runner_mcp_executable=launcher,
        runner=runner,
    )
    assert len(runner.calls) == 33


def test_missing_runtime_fails_without_process(tmp_path: Path) -> None:
    runner = FakeRunner()
    assert not smoke.run_autostart_runtime_smoke(
        python_executable=tmp_path / "missing-python",
        runner_mcp_executable=tmp_path / "missing-runner-mcp",
        runner=runner,
    )
    assert runner.calls == []


def test_relative_runtime_path_fails_without_process(tmp_path: Path) -> None:
    runner = FakeRunner()
    assert not smoke.run_autostart_runtime_smoke(
        python_executable=Path("python"),
        runner_mcp_executable=Path("runner-mcp"),
        runner=runner,
    )
    assert runner.calls == []


def test_spawn_error_fails_without_leaking_or_retrying(tmp_path: Path) -> None:
    python = executable(tmp_path, "python")
    launcher = executable(tmp_path, "runner-mcp")
    calls = 0

    def fail(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise OSError("/private/path secret-token")

    assert not smoke.run_autostart_runtime_smoke(
        python_executable=python,
        runner_mcp_executable=launcher,
        runner=fail,
    )
    assert calls == 1
