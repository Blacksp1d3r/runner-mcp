"""Same-process loaded-module observation, never an active build attestation.

This source-only, bounded, zero-argument MCP read serves ONLY the process
handling the authenticated request. sys.modules and installed metadata do
not prove a signed wheel, historical rollback, or all six managed roles.
No paths, IDs, tokens, or module source are ever returned.
"""
from __future__ import annotations

import hashlib
import marshal
import sys
from collections.abc import Mapping
from types import CodeType, FunctionType, ModuleType

_EXPECTED = ("runner_mcp", "runner_mcp.server", "runner_mcp.build_identity")
_SCHEMA = "runner-mcp/local-loaded-modules/v1"
_MAX_VERSION = 64
# Read-only in-process snapshot of selected Python function code objects; never
# a wheel signer, all-module proof, six-role attestation or source revision.
_CODE_MODULES = ("runner_mcp.server", "runner_mcp.build_identity")
_CODE_SCHEMA = "runner-mcp/selected-loaded-code-objects/v1"
_MAX_CODE_OBJECTS = 1024
_MAX_CODE_BLOB = 4 * 1024 * 1024
_MAX_NESTING = 24


def _normalized_code(code: CodeType, *, depth: int = 0) -> CodeType:
    """Normalize filenames recursively so local paths never affect the hash."""
    if depth > _MAX_NESTING:
        raise ValueError("code nesting is unavailable")
    return code.replace(
        co_filename="",
        co_consts=tuple(
            _normalized_code(value, depth=depth + 1)
            if isinstance(value, CodeType) else value
            for value in code.co_consts
        ),
    )


def _module_code_items(name: str, module: ModuleType) -> list[tuple[str, CodeType]]:
    """Inspect static module/class dictionaries, not attributes or source files."""
    result: list[tuple[str, CodeType]] = []
    for symbol, value in sorted(vars(module).items()):
        if type(symbol) is not str:
            continue
        if type(value) is FunctionType and value.__module__ == name:
            result.append((symbol, value.__code__))
        elif type(value) is type and value.__module__ == name:
            for member, descriptor in sorted(vars(value).items()):
                function: object = descriptor
                if type(descriptor) in (staticmethod, classmethod):
                    function = descriptor.__func__
                if type(function) is FunctionType and function.__module__ == name:
                    result.append((symbol + "." + member, function.__code__))
    return result


def _selected_loaded_code_digest(
    modules: Mapping[str, object],
) -> tuple[str | None, int, int]:
    """Hash actual in-memory code objects; do not read/execute module files.

    This fingerprint is an *untrusted partial observation*. It may be compared
    off-host with an independently qualified source, but cannot itself issue
    provenance, pin a live PID, attest imported data/constants outside code
    objects or authorize update/rollback.
    """
    hasher = hashlib.sha256()
    hasher.update(_CODE_SCHEMA.encode("ascii") + b"\0")
    count = 0
    observed_modules = 0
    total_size = 0
    for name in _CODE_MODULES:
        module = modules.get(name)
        if type(module) is not ModuleType or module.__name__ != name:
            return None, 0, 0
        entries = _module_code_items(name, module)
        if not entries:
            return None, 0, 0
        observed_modules += 1
        for symbol, code in entries:
            count += 1
            if count > _MAX_CODE_OBJECTS:
                return None, 0, 0
            raw = marshal.dumps(_normalized_code(code))
            total_size += len(raw)
            if total_size > _MAX_CODE_BLOB:
                return None, 0, 0
            hasher.update(name.encode("ascii") + b"\0")
            hasher.update(symbol.encode("utf-8") + b"\0")
            hasher.update(len(raw).to_bytes(4, "big"))
            hasher.update(raw)
    return hasher.hexdigest(), count, observed_modules


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
        "loadedCodeObservationSchema": _CODE_SCHEMA,
        "loadedCodeObjectDigest": None,
        "loadedCodeObjectCount": 0,
        "loadedCodeModuleCount": 0,
        "loadedCodeObservationComplete": False,
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
        digest, code_count, code_modules = _selected_loaded_code_digest(roster)
        return {
            **result,
            "state": "observed_local_only",
            "reasonCode": "current_module_roster_observed_only",
            "loadedVersionMatchesInstalled": True,
            "loadedCodeObjectDigest": digest,
            "loadedCodeObjectCount": code_count,
            "loadedCodeModuleCount": code_modules,
            "loadedCodeObservationComplete": digest is not None,
        }
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError, OverflowError):
        return result
