from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .config import ProjectRegistry


class KnownProjectRegistrationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class KnownProject:
    code: str
    display_name: str
    repository: str
    directory_name: str
    adapter: str = "generic"


KNOWN_PROJECTS: dict[str, KnownProject] = {
    "aifordable": KnownProject(
        code="aifordable",
        display_name="AIfordable",
        repository="Blacksp1d3r/AIfordable",
        directory_name="AIfordable",
    ),
}


def discover_known_project_root(
    registry: ProjectRegistry,
    *,
    project_id: str,
    runner=subprocess.run,
) -> tuple[KnownProject, Path]:
    if project_id not in KNOWN_PROJECTS:
        raise KnownProjectRegistrationError("Unknown managed project")
    if not callable(runner):
        raise TypeError("runner must be callable")

    project = KNOWN_PROJECTS[project_id]
    candidates: list[Path] = []

    for configured in registry.projects.values():
        anchor = _trusted_existing_root(configured.root)
        candidate = anchor.parent / project.directory_name
        if not candidate.exists():
            continue
        if candidate.is_symlink():
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if not resolved.is_dir():
            continue
        if _repository_for(resolved, runner=runner) != project.repository:
            continue
        if resolved not in candidates:
            candidates.append(resolved)

    if not candidates:
        raise KnownProjectRegistrationError(
            "Known project clone was not found beside a configured project"
        )
    if len(candidates) != 1:
        raise KnownProjectRegistrationError(
            "Known project clone discovery is ambiguous"
        )
    return project, candidates[0]


def _trusted_existing_root(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute():
        raise KnownProjectRegistrationError("Configured project root is invalid")
    if path.is_symlink():
        raise KnownProjectRegistrationError("Configured project root is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise KnownProjectRegistrationError(
            "Configured project root is unavailable"
        ) from exc
    if not resolved.is_dir():
        raise KnownProjectRegistrationError("Configured project root is unsafe")
    return resolved


def _repository_for(root: Path, *, runner) -> str | None:
    try:
        result = runner(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if not isinstance(result, subprocess.CompletedProcess):
        return None
    if result.returncode != 0 or not isinstance(result.stdout, str):
        return None
    if len(result.stdout.encode("utf-8")) > 4096:
        return None
    return _normalize_repository(result.stdout.strip())


def _normalize_repository(value: str) -> str | None:
    if not value or "\x00" in value or "\n" in value:
        return None

    if value.startswith("git@github.com:"):
        path = value.removeprefix("git@github.com:")
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "ssh", "git"}:
            return None
        if (parsed.hostname or "").lower() != "github.com":
            return None
        path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"
