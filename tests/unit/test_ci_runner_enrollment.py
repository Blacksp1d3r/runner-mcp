from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp.ci_runner_enrollment import (
    CIRunnerEnrollmentError,
    CIRunnerEnrollmentManager,
)
from runner_mcp.ci_runner_github import (
    CIRunnerGitHubController,
    GitHubRunnerState,
    _ShortLivedRunnerToken,
)
from runner_mcp.ci_runner_lifecycle import CIRunnerSpec
from runner_mcp.github_mailbox import GitHubApiSession


class DummySession(GitHubApiSession):
    def __init__(self) -> None:
        super().__init__(token="t" * 40)


class FakeGitHub(CIRunnerGitHubController):
    def __init__(self) -> None:
        super().__init__(DummySession())
        self.states: list[GitHubRunnerState | None] = []
        self.token_calls = 0

    def status(self, spec):
        assert isinstance(spec, CIRunnerSpec)
        if self.states:
            return self.states.pop(0)
        return None

    def create_registration_token(self, spec):
        assert isinstance(spec, CIRunnerSpec)
        self.token_calls += 1
        return _ShortLivedRunnerToken("r" * 40)


def setup_spec(tmp_path: Path) -> CIRunnerSpec:
    root = tmp_path / "runner"
    root.mkdir()
    work = root / "_work"
    script = root / "config.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    script.chmod(0o700)
    return CIRunnerSpec(
        alias="aifordable-lab-ci",
        repository="Blacksp1d3r/AIfordable",
        runner_name="aifordable-lab-ci",
        runner_root=root,
        work_root=work,
        labels=("aifordable-ci",),
    )


def remote(*, online: bool = False) -> GitHubRunnerState:
    return GitHubRunnerState(
        runner_id=42,
        online=online,
        busy=False,
        custom_labels=("aifordable-ci",),
    )


def test_enrollment_uses_fixed_non_shell_config_command(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    github = FakeGitHub()
    github.states.extend([None, remote()])
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run_process(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        (spec.runner_root / ".runner").write_text("private", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout="configured",
            stderr="",
        )

    manager = CIRunnerEnrollmentManager(
        github=github,
        run_process=run_process,
        uid_provider=lambda: 1000,
        sleeper=lambda _seconds: None,
        environment={
            "HOME": "/home/runner",
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "PRIVATE_SECRET": "must-not-pass",
        },
    )

    result = manager.enroll(spec)

    assert result.state == "registered"
    assert result.custom_labels == ("aifordable-ci",)
    assert github.token_calls == 1
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [
        str(spec.runner_root / "config.sh"),
        "--unattended",
        "--url",
        "https://github.com/Blacksp1d3r/AIfordable",
        "--token",
        "r" * 40,
        "--name",
        "aifordable-lab-ci",
        "--labels",
        "aifordable-ci",
        "--work",
        "_work",
        "--disableupdate",
    ]
    assert kwargs["shell"] is False
    assert kwargs["cwd"] == str(spec.runner_root)
    assert kwargs["timeout"] == 120.0
    assert kwargs["env"] == {
        "HOME": "/home/runner",
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    assert spec.work_root.is_dir()


def test_enrollment_refuses_root_without_fetching_token(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    github = FakeGitHub()

    with pytest.raises(CIRunnerEnrollmentError, match="refuses root"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 0,
        ).enroll(spec)

    assert github.token_calls == 0


def test_existing_local_and_remote_registration_is_idempotent(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    (spec.runner_root / ".runner").write_text("private", encoding="utf-8")
    github = FakeGitHub()
    github.states.append(remote(online=True))
    calls = 0

    def run_process(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("must not execute")

    result = CIRunnerEnrollmentManager(
        github=github,
        run_process=run_process,
        uid_provider=lambda: 1000,
    ).enroll(spec)

    assert result.state == "already-registered"
    assert result.online is True
    assert calls == 0
    assert github.token_calls == 0


def test_symlinked_existing_marker_is_rejected_before_idempotency(
    tmp_path: Path,
) -> None:
    spec = setup_spec(tmp_path)
    outside = tmp_path / "outside-marker"
    outside.write_text("not runner-owned", encoding="utf-8")
    (spec.runner_root / ".runner").symlink_to(outside)
    github = FakeGitHub()
    github.states.append(remote(online=True))

    with pytest.raises(CIRunnerEnrollmentError, match="marker is unsafe"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 1000,
        ).enroll(spec)

    assert github.token_calls == 0
    assert outside.read_text(encoding="utf-8") == "not runner-owned"


def test_existing_registration_refuses_unexpected_remote_labels(
    tmp_path: Path,
) -> None:
    spec = setup_spec(tmp_path)
    (spec.runner_root / ".runner").write_text("private", encoding="utf-8")
    github = FakeGitHub()
    github.states.append(
        GitHubRunnerState(
            runner_id=42,
            online=True,
            busy=False,
            custom_labels=("unapproved-label",),
        )
    )

    with pytest.raises(CIRunnerEnrollmentError, match="labels do not match"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 1000,
        ).enroll(spec)

    assert github.token_calls == 0


def test_remote_identity_without_local_marker_fails_closed(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    github = FakeGitHub()
    github.states.append(remote())

    with pytest.raises(CIRunnerEnrollmentError, match="already exists on GitHub"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 1000,
        ).enroll(spec)

    assert github.token_calls == 0


def test_local_marker_without_remote_identity_fails_closed(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    (spec.runner_root / ".runner").write_text("private", encoding="utf-8")
    github = FakeGitHub()
    github.states.append(None)

    with pytest.raises(CIRunnerEnrollmentError, match="not present on GitHub"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 1000,
        ).enroll(spec)


def test_failure_does_not_expose_process_output_or_token(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    github = FakeGitHub()
    github.states.append(None)

    def run_process(argv, **kwargs):
        return subprocess.CompletedProcess(
            args=argv,
            returncode=1,
            stdout="private response",
            stderr="token=" + "r" * 40,
        )

    with pytest.raises(CIRunnerEnrollmentError, match="was rejected") as exc:
        CIRunnerEnrollmentManager(
            github=github,
            run_process=run_process,
            uid_provider=lambda: 1000,
        ).enroll(spec)

    rendered = str(exc.value)
    assert "private response" not in rendered
    assert "r" * 40 not in rendered


def test_symlink_config_script_is_rejected_before_token_fetch(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    real = spec.runner_root / "real-config.sh"
    real.write_text("#!/bin/sh\n", encoding="utf-8")
    real.chmod(0o700)
    (spec.runner_root / "config.sh").unlink()
    (spec.runner_root / "config.sh").symlink_to(real)
    github = FakeGitHub()

    with pytest.raises(CIRunnerEnrollmentError, match="script is unavailable"):
        CIRunnerEnrollmentManager(
            github=github,
            uid_provider=lambda: 1000,
        ).enroll(spec)

    assert github.token_calls == 0


def test_registration_must_become_visible(tmp_path: Path) -> None:
    spec = setup_spec(tmp_path)
    github = FakeGitHub()
    github.states.extend([None] * 6)

    def run_process(argv, **kwargs):
        (spec.runner_root / ".runner").write_text("private", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    with pytest.raises(CIRunnerEnrollmentError, match="did not become visible"):
        CIRunnerEnrollmentManager(
            github=github,
            run_process=run_process,
            uid_provider=lambda: 1000,
            sleeper=lambda _seconds: None,
        ).enroll(spec)
