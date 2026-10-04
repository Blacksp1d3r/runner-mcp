from __future__ import annotations

import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .config import ProjectRegistry, load_project_registry
from .source_control import _git_environment


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
    "rasff-lens": KnownProject(
        code="rasff-lens",
        display_name="RASFF Lens",
        repository="Blacksp1d3r/rasff-lens",
        directory_name="rasff-lens",
        adapter="python",
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

    path = path.removesuffix(".git")
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"



def register_known_project(
    config_dir: Path,
    projects_config: Path,
    registry: ProjectRegistry,
    *,
    project_id: str,
    runner=subprocess.run,
    add_project_fn=None,
    reload_fn=load_project_registry,
) -> dict[str, str]:
    if not isinstance(config_dir, Path) or not config_dir.is_absolute():
        raise KnownProjectRegistrationError("Private configuration root is invalid")
    if not isinstance(projects_config, Path) or not projects_config.is_absolute():
        raise KnownProjectRegistrationError("Project configuration path is invalid")

    project = KNOWN_PROJECTS.get(project_id)
    if project is None:
        raise KnownProjectRegistrationError("Unknown managed project")

    existing = registry.projects.get(project.code)
    if existing is not None:
        if existing.repository != project.repository:
            raise KnownProjectRegistrationError(
                "Managed project code is already bound to another repository"
            )
        return {
            **existing.public_summary(project.code),
            "state": "already-registered",
        }

    discovered, root = discover_known_project_root(
        registry,
        project_id=project_id,
        runner=runner,
    )
    if add_project_fn is None:
        from .config_manager import add_project as add_project_impl

        add_project_fn = add_project_impl

    try:
        summary = add_project_fn(
            config_dir,
            code=discovered.code,
            display_name=discovered.display_name,
            repository=discovered.repository,
            root=root,
            adapter=discovered.adapter,
        )
        refreshed = reload_fn(projects_config)
    except (OSError, RuntimeError, ValueError) as exc:
        raise KnownProjectRegistrationError(
            "Managed project registration failed"
        ) from exc

    current = refreshed.projects.get(discovered.code)
    if current is None or current.repository != discovered.repository:
        raise KnownProjectRegistrationError(
            "Managed project registration could not be verified"
        )

    registry.projects.clear()
    registry.projects.update(refreshed.projects)
    return {**summary, "state": "registered"}



def prepare_known_project(
    registry: ProjectRegistry,
    *,
    project_id: str,
    runner=subprocess.run,
) -> dict[str, str]:
    """Prepare one catalogued clone beside an already-trusted project root."""

    if project_id not in KNOWN_PROJECTS:
        raise KnownProjectRegistrationError("Unknown managed project")
    if not callable(runner):
        raise TypeError("runner must be callable")

    project = KNOWN_PROJECTS[project_id]
    parents = {
        _trusted_existing_root(configured.root).parent
        for configured in registry.projects.values()
    }
    if len(parents) != 1:
        raise KnownProjectRegistrationError(
            "Known project clone destination is ambiguous"
        )
    parent = next(iter(parents))
    target = parent / project.directory_name

    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            raise KnownProjectRegistrationError(
                "Known project destination is occupied"
            )
        if _repository_for(target.resolve(strict=True), runner=runner) != project.repository:
            raise KnownProjectRegistrationError(
                "Known project destination has an unexpected repository"
            )
        return {
            "code": project.code,
            "name": project.display_name,
            "repository": project.repository,
            "state": "already-prepared",
        }

    temporary = parent / f".{project.code}-clone-{secrets.token_hex(8)}"
    if temporary.exists() or temporary.is_symlink():
        raise KnownProjectRegistrationError(
            "Known project temporary destination is unavailable"
        )

    repository_urls = (
        f"git@github.com:{project.repository}.git",
        f"https://github.com/{project.repository}.git",
    )
    try:
        result = None
        for repository_url in repository_urls:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)
            result = runner(
                [
                    "git",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "clone",
                    "--origin",
                    "origin",
                    "--no-tags",
                    "--",
                    repository_url,
                    str(temporary),
                ],
                cwd=str(parent),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=180.0,
                check=False,
                shell=False,
                env=_git_environment(network=True),
            )
            if (
                isinstance(result, subprocess.CompletedProcess)
                and result.returncode == 0
            ):
                break
        if not isinstance(result, subprocess.CompletedProcess):
            raise KnownProjectRegistrationError(
                "Known project clone result is invalid"
            )
        if result.returncode != 0:
            raise KnownProjectRegistrationError("Known project clone failed")
        if not temporary.is_dir() or temporary.is_symlink():
            raise KnownProjectRegistrationError("Known project clone is invalid")
        if _repository_for(temporary.resolve(strict=True), runner=runner) != project.repository:
            raise KnownProjectRegistrationError(
                "Known project clone repository verification failed"
            )
        temporary.replace(target)
    except subprocess.TimeoutExpired as exc:
        raise KnownProjectRegistrationError("Known project clone timed out") from exc
    except OSError as exc:
        raise KnownProjectRegistrationError("Known project clone failed") from exc
    finally:
        if temporary.exists() and temporary != target:
            shutil.rmtree(temporary, ignore_errors=True)

    return {
        "code": project.code,
        "name": project.display_name,
        "repository": project.repository,
        "state": "prepared",
    }



def preflight_known_project(
    registry: ProjectRegistry,
    *,
    project_id: str,
    runner=subprocess.run,
) -> dict[str, str]:
    """Return bounded destination state for one catalogued project."""

    project = KNOWN_PROJECTS.get(project_id)
    if project is None:
        raise KnownProjectRegistrationError("Unknown managed project")
    if not callable(runner):
        raise TypeError("runner must be callable")

    parents = {
        _trusted_existing_root(configured.root).parent
        for configured in registry.projects.values()
    }
    if len(parents) != 1:
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "ambiguous-parent",
        }

    parent = next(iter(parents))
    target = parent / project.directory_name
    if target.is_symlink():
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "unsafe-destination",
        }
    if not target.exists():
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "ready-to-prepare",
        }
    if not target.is_dir():
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "occupied-destination",
        }
    try:
        resolved = target.resolve(strict=True)
    except OSError:
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "unavailable-destination",
        }
    observed = _repository_for(resolved, runner=runner)
    if observed == project.repository:
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "already-prepared",
        }
    if observed is None:
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "not-a-matching-clone",
        }
    return {
        "code": project.code,
        "repository": project.repository,
        "state": "wrong-repository",
    }
