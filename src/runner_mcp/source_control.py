from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .config import ProjectRegistry
from .operational_safety import ActionClass, OperatorSafetyGuard


class SourceControlError(RuntimeError):
    pass


_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SCP_GITHUB_RE = re.compile(
    r"^git@github\.com:(?P<repository>[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+?)(?:\.git)?$"
)


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


def _safe_root(root: Path) -> Path:
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise SourceControlError("Project root is unavailable") from exc
    if not resolved.is_dir() or resolved.is_symlink():
        raise SourceControlError("Project root is unsafe")
    return resolved


def _git_environment(*, network: bool) -> dict[str, str]:
    environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }
    if network:
        home = os.environ.get("HOME", "").strip()
        if home and Path(home).is_absolute():
            environment["HOME"] = home
        ssh_auth_sock = os.environ.get("SSH_AUTH_SOCK", "").strip()
        if ssh_auth_sock and Path(ssh_auth_sock).is_absolute():
            environment["SSH_AUTH_SOCK"] = ssh_auth_sock
    else:
        environment["HOME"] = "/nonexistent"
    return environment


def _run_git(
    root: Path,
    arguments: list[str],
    *,
    timeout: int = 30,
    network: bool = False,
) -> str:
    resolved = _safe_root(root)
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
            timeout=timeout,
            check=False,
            shell=False,
            env=_git_environment(network=network),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceControlError("Git source-state operation failed") from exc
    if completed.returncode != 0:
        raise SourceControlError("Git source-state operation failed")
    return completed.stdout.strip()


def _normalized_github_repository(remote: str) -> str | None:
    scp = _SCP_GITHUB_RE.fullmatch(remote.strip())
    if scp:
        return scp.group("repository").lower()

    try:
        parsed = urlsplit(remote.strip())
    except ValueError:
        return None
    if parsed.username not in {None, "git"} or parsed.password is not None:
        return None
    if parsed.hostname != "github.com":
        return None
    if parsed.scheme not in {"https", "ssh"}:
        return None
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or path.count("/") != 1:
        return None
    return path.lower()


def _require_configured_origin(root: Path, repository: str) -> None:
    remote = _run_git(root, ["remote", "get-url", "origin"])
    if _normalized_github_repository(remote) != repository.lower():
        raise SourceControlError(
            "Project origin does not match the configured repository"
        )


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


class SourceSynchronizer:
    """Commit-pinned staging checkout synchronizer for trusted project testing."""

    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        tests=None,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.tests = tests

    def sync_project(self, project: str, commit: str) -> dict[str, str | bool]:
        config = self.registry.projects.get(project)
        if config is None:
            raise SourceControlError("Unknown or disabled project")
        if not _COMMIT_RE.fullmatch(commit):
            raise SourceControlError("Commit must be a full Git object ID")

        self.safety.assert_project_action_allowed(
            ActionClass.TEST,
            environment=config.environment,
        )
        if self.tests is not None and self.tests.project_has_work(project):
            raise SourceControlError(
                "Project source sync is blocked while tests are queued or active"
            )

        root = _safe_root(config.root)
        if (root / ".gitmodules").exists():
            raise SourceControlError(
                "Project source sync does not support submodule worktrees"
            )

        before = clean_head(root)["commit"]
        assert isinstance(before, str)
        _require_configured_origin(root, config.repository)

        _run_git(
            root,
            ["fetch", "--prune", "--no-tags", "origin"],
            timeout=120,
            network=True,
        )
        resolved_commit = _run_git(
            root,
            ["rev-parse", "--verify", f"{commit}^{{commit}}"],
        ).lower()
        if resolved_commit != commit.lower():
            raise SourceControlError("Requested commit did not resolve exactly")

        containing_refs = _run_git(
            root,
            [
                "for-each-ref",
                "--format=%(refname)",
                f"--contains={resolved_commit}",
                "refs/remotes/origin/",
            ],
        ).splitlines()
        if not any(
            ref.startswith("refs/remotes/origin/")
            and ref != "refs/remotes/origin/HEAD"
            for ref in containing_refs
        ):
            raise SourceControlError(
                "Requested commit is not reachable from the configured origin"
            )

        if before != resolved_commit:
            _run_git(
                root,
                ["checkout", "--detach", "--quiet", resolved_commit],
                timeout=60,
            )

        after = clean_head(root)["commit"]
        if after != resolved_commit:
            raise SourceControlError("Project checkout did not reach requested commit")

        return {
            "project": project,
            "commit": resolved_commit,
            "changed": before != resolved_commit,
        }
