"""Read-only source gate for future Fabric-owned local test execution.

This module is NOT a worker or execution authority. It inspects only an
already registered project's existing, local, clean Git checkout. A matching
origin URL is configuration evidence, not proof of remote authentication or
commit reachability. No guest, command or host can be chosen by callers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import PROJECT_CODE_RE, ProjectRegistry
from .source_control import (
    SourceControlError,
    _require_configured_origin,
    _run_git,
    _safe_root,
    clean_head,
)


class LocalTestSourcePreflightError(ValueError):
    """Bounded, sanitized reason for refusing local test source admission."""


def inspect_local_test_source(
    registry: ProjectRegistry,
    *,
    project: str,
    suite: str,
    expected_sha: str,
) -> dict[str, Any]:
    """Check source only; actual test dispatch is ALWAYS denied here.

    Fabric/F18 must independently prove origin reachability, an authorized
    F26 disposable guest, isolation, lease, result/ACK and teardown.
    No command, path, host, credential or guest selector is accepted here.
    """
    if not isinstance(registry, ProjectRegistry):
        raise LocalTestSourcePreflightError("invalid_project_registry")
    if (
        not isinstance(project, str)
        or not PROJECT_CODE_RE.fullmatch(project)
        or not isinstance(suite, str)
        or not PROJECT_CODE_RE.fullmatch(suite)
    ):
        raise LocalTestSourcePreflightError("invalid_project_or_profile")
    if (
        not isinstance(expected_sha, str)
        or len(expected_sha) != 40
        or any(char not in "0123456789abcdef" for char in expected_sha)
    ):
        raise LocalTestSourcePreflightError("invalid_exact_source_sha")

    config = registry.projects.get(project)
    if config is None:
        raise LocalTestSourcePreflightError("unknown_or_disabled_project")
    # An adapter default does not authorize remotely scheduled execution.
    if suite not in config.test_profiles:
        raise LocalTestSourcePreflightError("test_profile_not_registered")
    if config.environment != "staging":
        raise LocalTestSourcePreflightError("non_staging_source_not_admitted")

    try:
        # Refuse symlinked path components before resolving the root.
        # source_control._safe_root() resolves links, so check explicitly.
        if any(item.is_symlink() for item in (config.root, *config.root.parents)):
            raise SourceControlError("Symlinked project root is unsafe")
        root = _safe_root(config.root)
        # A registered project root must be the repository root, not a
        # nested folder that silently borrows the parent repository HEAD.
        top = Path(_run_git(root, ["rev-parse", "--show-toplevel"]))
        if top.resolve(strict=True) != root:
            raise SourceControlError("Project root is not its Git top-level")
        if (root / ".gitmodules").exists():
            raise SourceControlError("Submodule checkouts are not supported")
        # The configured URL is checked, NOT remote custody or authentication.
        _require_configured_origin(root, config.repository)
        evidence = clean_head(root)
    except SourceControlError:
        raise LocalTestSourcePreflightError("checkout_or_origin_not_verified") from None

    if evidence["commit"] != expected_sha:
        raise LocalTestSourcePreflightError("exact_source_sha_mismatch")

    return {
        "schema_version": "runner-mcp/local-test-source-preflight/v1",
        "state": "source_checked_wait_f26_guest",
        "project": project,
        "suite": suite,
        "source_sha": expected_sha,
        "checkout_clean": True,
        "configured_origin_matches": True,
        "remote_reachability_verified": False,
        "guest_identity_verified": False,
        "fabric_lease_verified": False,
        "dispatch_authorized": False,
        "host_local_fallback_allowed": False,
        "source_changed": False,
    }
