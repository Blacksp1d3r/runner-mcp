from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .source_control import _git_environment

_SCHEMA = "runner-mcp/known-project-local-sources/v1"
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_CONFIG_BYTES = 65_536


class KnownProjectLocalSourceError(RuntimeError):
    """Sanitized trusted local-source binding failure."""


@dataclass(frozen=True, slots=True)
class KnownProjectLocalSource:
    repository: str
    source: Path
    expected_revision: str


def resolve_known_project_local_source(
    *,
    raw: str | None,
    project_id: str,
    expected_repository: str,
) -> KnownProjectLocalSource | None:
    """Resolve one host-owned local source binding without caller path authority."""

    if raw is None or not raw.strip():
        return None
    if not isinstance(raw, str) or len(raw.encode()) > _MAX_CONFIG_BYTES:
        raise KnownProjectLocalSourceError("local-source-config-invalid")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KnownProjectLocalSourceError("local-source-config-invalid") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schemaVersion", "projects"}
        or payload.get("schemaVersion") != _SCHEMA
        or not isinstance(payload.get("projects"), dict)
    ):
        raise KnownProjectLocalSourceError("local-source-config-invalid")

    item = payload["projects"].get(project_id)
    if item is None:
        return None
    if not isinstance(item, dict) or set(item) != {
        "repository",
        "source",
        "expectedRevision",
    }:
        raise KnownProjectLocalSourceError("local-source-config-invalid")
    if item.get("repository") != expected_repository:
        raise KnownProjectLocalSourceError("local-source-repository-mismatch")

    source_raw = item.get("source")
    revision = item.get("expectedRevision")
    if (
        not isinstance(source_raw, str)
        or not source_raw
        or "\x00" in source_raw
        or "\n" in source_raw
        or "\r" in source_raw
    ):
        raise KnownProjectLocalSourceError("local-source-config-invalid")
    if not isinstance(revision, str) or _REVISION_RE.fullmatch(revision) is None:
        raise KnownProjectLocalSourceError("local-source-revision-invalid")

    source = Path(source_raw)
    if not source.is_absolute() or source.is_symlink():
        raise KnownProjectLocalSourceError("local-source-unsafe")
    try:
        resolved = source.resolve(strict=True)
        info = resolved.stat()
    except OSError as exc:
        raise KnownProjectLocalSourceError("local-source-unavailable") from exc
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise KnownProjectLocalSourceError("local-source-unsafe")

    return KnownProjectLocalSource(
        repository=expected_repository,
        source=resolved,
        expected_revision=revision,
    )


def materialize_known_project_local_source(
    *,
    binding: KnownProjectLocalSource,
    destination: Path,
    canonical_origin: str,
    runner=subprocess.run,
) -> None:
    """Materialize one exact local revision into an empty private destination."""

    if not isinstance(binding, KnownProjectLocalSource):
        raise KnownProjectLocalSourceError("local-source-binding-invalid")
    if not callable(runner):
        raise TypeError("runner must be callable")
    if (
        not destination.is_absolute()
        or destination.exists()
        or destination.is_symlink()
    ):
        raise KnownProjectLocalSourceError("local-source-destination-invalid")

    result = _run(
        runner,
        [
            "/usr/bin/git",
            "-c",
            "core.hooksPath=/dev/null",
            "clone",
            "--no-local",
            "--origin",
            "origin",
            "--no-tags",
            "--no-checkout",
            "--",
            str(binding.source),
            str(destination),
        ],
        timeout=180,
    )
    if result.returncode != 0:
        raise KnownProjectLocalSourceError("local-source-materialization-failed")

    checkout = _run(
        runner,
        [
            "/usr/bin/git",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(destination),
            "checkout",
            "--detach",
            binding.expected_revision,
        ],
        timeout=60,
    )
    if checkout.returncode != 0:
        raise KnownProjectLocalSourceError("local-source-revision-unavailable")

    head = _run(
        runner,
        ["/usr/bin/git", "-C", str(destination), "rev-parse", "HEAD"],
        timeout=10,
        capture=True,
    )
    if head.returncode != 0 or head.stdout.strip() != binding.expected_revision:
        raise KnownProjectLocalSourceError("local-source-revision-mismatch")

    dirty = _run(
        runner,
        ["/usr/bin/git", "-C", str(destination), "status", "--porcelain"],
        timeout=10,
        capture=True,
    )
    if dirty.returncode != 0 or dirty.stdout.strip():
        raise KnownProjectLocalSourceError("local-source-checkout-invalid")

    remote = _run(
        runner,
        [
            "/usr/bin/git",
            "-C",
            str(destination),
            "remote",
            "set-url",
            "origin",
            canonical_origin,
        ],
        timeout=10,
    )
    if remote.returncode != 0:
        raise KnownProjectLocalSourceError("local-source-origin-normalization-failed")


def _run(
    runner,
    argv: list[str],
    *,
    timeout: int,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = runner(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
            env=_git_environment(network=False),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise KnownProjectLocalSourceError("local-source-operation-failed") from exc
    if not isinstance(completed, subprocess.CompletedProcess):
        raise KnownProjectLocalSourceError("local-source-operation-invalid")
    return completed
