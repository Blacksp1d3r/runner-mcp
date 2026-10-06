from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .source_control import _git_environment

_SCHEMA = "runner-mcp/known-project-local-sources/v1"
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_CONFIG_BYTES = 65_536


class LocalSourceBindingError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LocalSourceBinding:
    repository: str
    source: Path
    expected_revision: str


def load_local_source_binding(
    *,
    raw: str | None,
    project_id: str,
    expected_repository: str,
) -> LocalSourceBinding | None:
    if raw is None or not raw.strip():
        return None
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > _MAX_CONFIG_BYTES:
        raise LocalSourceBindingError("Local source configuration is invalid")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LocalSourceBindingError(
            "Local source configuration is invalid"
        ) from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schemaVersion", "projects"}
        or payload.get("schemaVersion") != _SCHEMA
        or not isinstance(payload.get("projects"), dict)
    ):
        raise LocalSourceBindingError("Local source configuration is invalid")

    item = payload["projects"].get(project_id)
    if item is None:
        return None
    if not isinstance(item, dict) or set(item) != {
        "repository",
        "source",
        "expectedRevision",
    }:
        raise LocalSourceBindingError("Local source configuration is invalid")
    if item["repository"] != expected_repository:
        raise LocalSourceBindingError("Local source repository mismatch")

    source_raw = item["source"]
    revision = item["expectedRevision"]
    if (
        not isinstance(source_raw, str)
        or not source_raw
        or "\x00" in source_raw
    ):
        raise LocalSourceBindingError("Local source is invalid")
    source = Path(source_raw)
    if not source.is_absolute() or source.is_symlink():
        raise LocalSourceBindingError("Local source is invalid")
    try:
        source = source.resolve(strict=True)
    except OSError as exc:
        raise LocalSourceBindingError("Local source is unavailable") from exc
    if not source.is_dir():
        raise LocalSourceBindingError("Local source is unavailable")
    if not isinstance(revision, str) or _REVISION_RE.fullmatch(revision) is None:
        raise LocalSourceBindingError("Local source revision is invalid")
    return LocalSourceBinding(
        repository=expected_repository,
        source=source,
        expected_revision=revision,
    )


def materialize_local_source(
    *,
    binding: LocalSourceBinding,
    destination: Path,
    canonical_origin: str,
    runner=subprocess.run,
) -> None:
    if not isinstance(binding, LocalSourceBinding):
        raise LocalSourceBindingError("Local source binding is invalid")
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise LocalSourceBindingError("Local destination is invalid")

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
            "--",
            str(binding.source),
            str(destination),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=180.0,
        check=False,
        shell=False,
        env=_git_environment(network=False),
    )
    if not isinstance(result, subprocess.CompletedProcess) or result.returncode != 0:
        raise LocalSourceBindingError("Local source materialization failed")

    checkout = runner(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(destination),
            "checkout",
            "--detach",
            binding.expected_revision,
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60.0,
        check=False,
        shell=False,
        env=_git_environment(network=False),
    )
    if not isinstance(checkout, subprocess.CompletedProcess) or checkout.returncode != 0:
        raise LocalSourceBindingError("Local source revision is unavailable")

    verify = runner(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
        shell=False,
        env=_git_environment(network=False),
    )
    observed = (
        verify.stdout.strip()
        if isinstance(verify, subprocess.CompletedProcess)
        and verify.returncode == 0
        and isinstance(verify.stdout, str)
        else ""
    )
    if observed != binding.expected_revision:
        raise LocalSourceBindingError("Local source revision verification failed")

    remote = runner(
        ["git", "-C", str(destination), "remote", "set-url", "origin", canonical_origin],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
        shell=False,
        env=_git_environment(network=False),
    )
    if not isinstance(remote, subprocess.CompletedProcess) or remote.returncode != 0:
        raise LocalSourceBindingError(
            "Local source repository identity normalization failed"
        )
