from __future__ import annotations

import os
import subprocess
from pathlib import Path


class SourceControlError(RuntimeError):
    pass


def _git_executable() -> Path:
    for candidate in (Path("/usr/bin/git"), Path("/bin/git")):
        if (
            candidate.exists()
            and candidate.is_file()
            and not candidate.is_symlink()
            and os.access(candidate, os.X_OK)
        ):
            return candidate
    raise SourceControlError("git is unavailable")


def _run_git(root: Path, arguments: list[str]) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise SourceControlError("Project root is unavailable") from exc
    if not resolved.is_dir() or resolved.is_symlink():
        raise SourceControlError("Project root is unsafe")

    command = [
        str(_git_executable()),
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-C",
        str(resolved),
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
            env={
                "HOME": "/nonexistent",
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_OPTIONAL_LOCKS": "0",
            },
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceControlError("Git source-state check failed") from exc
    if completed.returncode != 0:
        raise SourceControlError("Project must be a Git working tree")
    return completed.stdout.strip()


def clean_head(root: Path) -> dict[str, str | bool]:
    inside = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if inside != "true":
        raise SourceControlError("Project must be a Git working tree")

    dirty = _run_git(
        root,
        ["status", "--porcelain=v1", "--untracked-files=normal"],
    )
    if dirty:
        raise SourceControlError(
            "Project working tree must be clean before high-risk approval"
        )

    commit = _run_git(root, ["rev-parse", "--verify", "HEAD"])
    if len(commit) != 40 or any(
        char not in "0123456789abcdefABCDEF" for char in commit
    ):
        raise SourceControlError("Git HEAD did not resolve to a full commit")
    return {"commit": commit.lower(), "clean": True}
