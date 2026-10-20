"""Same-process loaded-module observation, never an active build attestation.

This source-only, bounded, zero-argument MCP read serves ONLY the process
handling the authenticated request. sys.modules and installed metadata do
not prove a signed wheel, historical rollback, or all six managed roles.
No paths, IDs, tokens, or module source are ever returned.
"""
from __future__ import annotations

import sys
from collections.abc import Mapping
from types import ModuleType

_EXPECTED = ("runner_mcp", "runner_mcp.server", "runner_mcp.build_identity")
_SCHEMA = "runner-mcp/local-loaded-modules/v1"
_MAX_VERSION = 64


def _valid_version(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= _MAX_VERSION
        and value.isascii()
        and all(32 <= ord(ch) < 127 for ch in value)
    )


def observe_current_process_modules(
    *,
    imported_version: object,
    installed_distribution_version: object,
    modules: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Only report a categorical in-memory roster and loaded/dist mismatch.

    Caller has no authority to set roles/hosts/paths. The optional module map
    exists for isolated unit tests; production reads the current sys.modules.
    This cannot observe a separate Fabric or Claude/Qwen host.
    """
    result: dict[str, object] = {
        "schemaVersion": _SCHEMA,
        "state": "wait",
        "reasonCode": "observation_unavailable",
        "scope": "this_connected_process_only",
        "moduleRosterCount": 0,
        "moduleRosterComplete": False,
        "loadedVersionMatchesPackage": False,
        "loadedVersionMatchesInstalled": False,
        "activeBuildProvenanceVerified": False,
        "sourceRevision": None,
        "artifactDigest": None,
        "selfUpdateReady": False,
        "updateAuthorized": False,
        "dispatchAuthorized": False,
    }
    if not _valid_version(imported_version) or not _valid_version(
        installed_distribution_version
    ):
        return {**result, "reasonCode": "invalid_version_input"}
    try:
        roster = sys.modules if modules is None else modules
        if not isinstance(roster, Mapping):
            return result
        count = sum(
            type(roster.get(name)) is ModuleType
            and getattr(roster.get(name), "__name__", None) == name
            for name in _EXPECTED
        )
        result["moduleRosterCount"] = count
        if count != len(_EXPECTED):
            return {**result, "reasonCode": "incomplete_local_module_roster"}
        result["moduleRosterComplete"] = True
        pkg = roster["runner_mcp"]
        pkg_version = getattr(pkg, "__version__", None)
        if type(pkg_version) is not str or pkg_version != imported_version:
            return {**result, "reasonCode": "imported_package_version_mismatch"}
        result["loadedVersionMatchesPackage"] = True
        if installed_distribution_version != imported_version:
            return {**result, "reasonCode": "loaded_vs_installed_version_mismatch"}
        return {
            **result,
            "state": "observed_local_only",
            "reasonCode": "current_module_roster_observed_only",
            "loadedVersionMatchesInstalled": True,
        }
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        return result
