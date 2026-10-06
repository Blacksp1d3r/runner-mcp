from __future__ import annotations

import base64
import os
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .config import ProjectRegistry, load_project_registry
from .known_project_local_source import (
    KnownProjectLocalSourceError,
    materialize_known_project_local_source,
    resolve_known_project_local_source,
)
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
    "runner-fabric": KnownProject(
        code="runner-fabric",
        display_name="Runner Fabric",
        repository="Blacksp1d3r/Runner-Fabric",
        directory_name="Runner-Fabric",
        adapter="python",
    ),
    "bewind": KnownProject(
        code="bewind",
        display_name="Bewind",
        repository="Blacksp1d3r/bewind",
        directory_name="bewind",
        adapter="python",
    ),
    "enercue": KnownProject(
        code="enercue",
        display_name="EnerCue",
        repository="Blacksp1d3r/EnerCue",
        directory_name="EnerCue",
    ),
    "patrimai": KnownProject(
        code="patrimai",
        display_name="PatrimAI",
        repository="Blacksp1d3r/PatrimAI",
        directory_name="PatrimAI",
    ),
    "unifiedesg": KnownProject(
        code="unifiedesg",
        display_name="UnifiedESG",
        repository="Blacksp1d3r/UnifiedESG",
        directory_name="UnifiedESG",
        adapter="python",
    ),
    "pastentrance": KnownProject(
        code="pastentrance",
        display_name="PastEntrance",
        repository="Blacksp1d3r/PastEntrance",
        directory_name="PastEntrance",
    ),
    "safety": KnownProject(
        code="safety",
        display_name="Safety!",
        repository="Blacksp1d3r/safety",
        directory_name="safety",
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



def _github_clone_environment(github_token: str | None) -> dict[str, str]:
    environment = _git_environment(network=True)
    if github_token is None:
        return environment
    if not isinstance(github_token, str):
        raise KnownProjectRegistrationError("GitHub clone credential is invalid")
    token = github_token.strip()
    if not token or any(char in token for char in ("\x00", "\r", "\n")):
        raise KnownProjectRegistrationError("GitHub clone credential is invalid")
    credential = base64.b64encode(
        f"x-access-token:{token}".encode()
    ).decode("ascii")
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {credential}",
        }
    )
    return environment



def preflight_known_project_source(
    *,
    project_id: str,
    github_token: str | None,
    local_source_bindings_raw: str | None = None,
    runner=subprocess.run,
) -> dict[str, str | bool]:
    """Return bounded source reachability for one fixed catalogued project."""

    project = KNOWN_PROJECTS.get(project_id)
    if project is None:
        raise KnownProjectRegistrationError("Unknown managed project")
    if not callable(runner):
        raise TypeError("runner must be callable")

    try:
        local_source = resolve_known_project_local_source(
            raw=local_source_bindings_raw,
            project_id=project.code,
            expected_repository=project.repository,
        )
    except KnownProjectLocalSourceError as exc:
        raise KnownProjectRegistrationError(
            "Trusted local project source configuration is invalid"
        ) from exc
    if local_source is not None:
        return {
            "code": project.code,
            "repository": project.repository,
            "credential_configured": bool(
                isinstance(github_token, str) and github_token.strip()
            ),
            "source_reachable": True,
            "main_ref_available": True,
            "reason_code": "local-source-ready",
        }

    credential_configured = bool(
        isinstance(github_token, str) and github_token.strip()
    )
    if not credential_configured:
        return {
            "code": project.code,
            "repository": project.repository,
            "credential_configured": False,
            "source_reachable": False,
            "main_ref_available": False,
            "reason_code": "credential-unconfigured",
        }

    repository_url = f"https://github.com/{project.repository}.git"
    try:
        local_source = resolve_known_project_local_source(
            raw=local_source_bindings_raw,
            project_id=project.code,
            expected_repository=project.repository,
        )
    except KnownProjectLocalSourceError as exc:
        raise KnownProjectRegistrationError(
            "Trusted local project source configuration is invalid"
        ) from exc

    if local_source is not None:
        try:
            materialize_known_project_local_source(
                binding=local_source,
                destination=temporary,
                canonical_origin=repository_url,
                runner=runner,
            )
            if not temporary.is_dir() or temporary.is_symlink():
                raise KnownProjectRegistrationError(
                    "Known project local materialization is invalid"
                )
            if (
                _repository_for(temporary.resolve(strict=True), runner=runner)
                != project.repository
            ):
                raise KnownProjectRegistrationError(
                    "Known project local materialization verification failed"
                )
            temporary.replace(target)
        except KnownProjectLocalSourceError as exc:
            raise KnownProjectRegistrationError(
                "Known project local materialization failed"
            ) from exc
        except OSError as exc:
            raise KnownProjectRegistrationError(
                "Known project local materialization failed"
            ) from exc
        finally:
            if temporary.exists() and temporary != target:
                shutil.rmtree(temporary, ignore_errors=True)
        return {
            "code": project.code,
            "name": project.display_name,
            "repository": project.repository,
            "state": "prepared-local",
        }

    try:
        result = runner(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "ls-remote",
                "--heads",
                "--",
                repository_url,
                "refs/heads/main",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=20.0,
            check=False,
            shell=False,
            env=_github_clone_environment(github_token),
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "code": project.code,
            "repository": project.repository,
            "credential_configured": True,
            "source_reachable": False,
            "main_ref_available": False,
            "reason_code": "source-unreachable-or-unauthorized",
        }

    if not isinstance(result, subprocess.CompletedProcess) or result.returncode != 0:
        return {
            "code": project.code,
            "repository": project.repository,
            "credential_configured": True,
            "source_reachable": False,
            "main_ref_available": False,
            "reason_code": "source-unreachable-or-unauthorized",
        }

    stdout = result.stdout if isinstance(result.stdout, str) else ""
    main_ref_available = "refs/heads/main" in stdout
    return {
        "code": project.code,
        "repository": project.repository,
        "credential_configured": True,
        "source_reachable": True,
        "main_ref_available": main_ref_available,
        "reason_code": "ready" if main_ref_available else "main-ref-unavailable",
    }

def prepare_known_project(
    registry: ProjectRegistry,
    *,
    project_id: str,
    runner=subprocess.run,
    github_token: str | None = None,
    local_source_bindings_raw: str | None = None,
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
    if not os.access(parent, os.W_OK | os.X_OK):
        raise KnownProjectRegistrationError(
            "Known project destination is not writable"
        )
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

    repository_url = f"https://github.com/{project.repository}.git"
    try:
        result = runner(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "clone",
                "--origin",
                "origin",
                "--no-tags",
                "--no-checkout",
                "--branch",
                "main",
                "--single-branch",
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
            env=_github_clone_environment(github_token),
        )
        if not isinstance(result, subprocess.CompletedProcess):
            raise KnownProjectRegistrationError(
                "Known project clone result is invalid"
            )
        if result.returncode != 0:
            raise KnownProjectRegistrationError("Known project clone failed")
        checkout = runner(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-C",
                str(temporary),
                "checkout",
                "--detach",
                "origin/main",
            ],
            cwd=str(parent),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60.0,
            check=False,
            shell=False,
            env=_git_environment(network=False),
        )
        if (
            not isinstance(checkout, subprocess.CompletedProcess)
            or checkout.returncode != 0
        ):
            raise KnownProjectRegistrationError(
                "Known project checkout failed"
            )
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
    if not os.access(parent, os.W_OK | os.X_OK):
        return {
            "code": project.code,
            "repository": project.repository,
            "state": "parent-not-writable",
        }
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
