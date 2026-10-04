from __future__ import annotations

import fcntl
import os
import subprocess
from pathlib import Path

import pytest

from runner_mcp.ci_runner_lifecycle import CIRunnerSpec
from runner_mcp.ci_runner_supervisor import (
    CIRunnerSupervisor,
    CIRunnerSupervisorError,
)


def spec(root: Path) -> CIRunnerSpec:
    return CIRunnerSpec(
        alias="aifordable-lab-ci",
        repository="Blacksp1d3r/AIfordable",
        runner_name="aifordable-lab-ci",
        runner_root=root,
        work_root=root / "_work",
        labels=("aifordable-ci",),
    )


def prepare(tmp_path: Path) -> Path:
    root = tmp_path / "runner"
    root.mkdir()
    (root / "_work").mkdir()
    (root / ".runner").write_text("registered", encoding="utf-8")
    script = root / "run.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    script.chmod(0o700)
    return root


def test_status_reports_registered_and_inactive(tmp_path: Path) -> None:
    root = prepare(tmp_path)

    payload = CIRunnerSupervisor(environment={}).status(spec(root)).to_payload()

    assert payload == {
        "alias": "aifordable-lab-ci",
        "registered": True,
        "active": False,
    }


def test_run_once_uses_fixed_runner_script_without_shell(tmp_path: Path) -> None:
    root = prepare(tmp_path)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def runner(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        return subprocess.CompletedProcess(argv, 0, "", "")

    result = CIRunnerSupervisor(
        environment={"PATH": "/custom/bin:/usr/bin", "SECRET": "drop-me"},
        runner=runner,
    ).run_once(spec(root))

    assert result.registered is True
    assert result.active is False
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [str((root / "run.sh").resolve())]
    assert kwargs["cwd"] == str(root.resolve())
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["env"] == {
        "PATH": "/custom/bin:/usr/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def test_unregistered_runner_cannot_start(tmp_path: Path) -> None:
    root = prepare(tmp_path)
    (root / ".runner").unlink()

    with pytest.raises(
        CIRunnerSupervisorError,
        match="requires an enrolled runner",
    ):
        CIRunnerSupervisor(environment={}).run_once(spec(root))


def test_symlink_run_script_is_rejected(tmp_path: Path) -> None:
    root = prepare(tmp_path)
    (root / "run.sh").unlink()
    target = tmp_path / "target.sh"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o700)
    (root / "run.sh").symlink_to(target)

    with pytest.raises(CIRunnerSupervisorError, match="script is unsafe"):
        CIRunnerSupervisor(environment={}).run_once(spec(root))


def test_existing_lock_prevents_duplicate_listener(tmp_path: Path) -> None:
    root = prepare(tmp_path)
    lock = root / ".runner-mcp-ci.lock"
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(
            CIRunnerSupervisorError,
            match="already active",
        ):
            CIRunnerSupervisor(environment={}).run_once(spec(root))
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_nonzero_runner_exit_is_bounded(tmp_path: Path) -> None:
    root = prepare(tmp_path)

    def runner(argv, **_kwargs):
        return subprocess.CompletedProcess(
            argv,
            1,
            "private stdout",
            "private stderr",
        )

    with pytest.raises(
        CIRunnerSupervisorError,
        match="exited unsuccessfully",
    ) as exc:
        CIRunnerSupervisor(environment={}, runner=runner).run_once(spec(root))

    assert "private stdout" not in str(exc.value)
    assert "private stderr" not in str(exc.value)
