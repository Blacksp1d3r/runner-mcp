from __future__ import annotations

import os
import re
from collections.abc import Mapping, MutableMapping
from pathlib import Path

from .fabric_worker_qualification_provisioning import (
    FabricWorkerQualificationProvisioningError,
    _merge_private_env,
    _require_private_file,
)

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_RUNNER_MCP_BEARER_ENV = "RUNNER_MCP_BEARER_TOKEN"
_RUNNER_MCP_ENDPOINT = "http://127.0.0.1:8000/mcp"
_PROBE_ID = "fleet-a6"
_TARGET_SUBJECT = "runner:aifordable-lab"
_INTERVAL_SECONDS = "60"
_JOURNAL_DOMAIN = "control:evidence"
_TARGET_DOMAIN = "target:runner-mcp"
_JOURNAL_DIR = "a6-update-journal"
_EVIDENCE_DIR = "a6-evidence"


_A6_KEYS = (
    "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT",
    "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN",
    "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN",
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_ID",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION",
)


class FabricA6BindingRepairError(RuntimeError):
    """Sanitized fixed A6 private-binding repair failure."""


def _resolve_private_a6_path(path: Path, failure: str) -> Path:
    """Reject lexical ancestor redirects before resolving an A6 private path.

    A leaf-only symlink check is insufficient: a linked grandparent can send
    otherwise private journal and runtime configuration writes to another tree.
    This is a fixed local path, not arbitrary filesystem authority.
    """
    try:
        expanded = path.expanduser()
        if not expanded.is_absolute() or ".." in expanded.parts:
            raise FabricA6BindingRepairError(failure)
        if any(ancestor.is_symlink() for ancestor in (expanded, *expanded.parents)):
            raise FabricA6BindingRepairError(failure)
        return expanded.resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise FabricA6BindingRepairError(failure) from exc


def _resolve_a6_state_root(state_root: Path) -> Path:
    """Fail closed for linked state-root ancestors with sanitized errors."""
    return _resolve_private_a6_path(state_root, "fabric_a6_state_unsafe")


def _resolve_a6_config_dir(config_dir: Path) -> Path:
    """Reject linked config ancestors before reading or merging private keys."""
    return _resolve_private_a6_path(config_dir, "fabric_a6_runtime_config_unavailable")


def a6_state_requested(state_root: Path) -> bool:
    """Return whether the fixed local A6 state roots signal an active A6 campaign."""

    root = _resolve_a6_state_root(state_root)
    journal = root / _JOURNAL_DIR
    evidence = root / _EVIDENCE_DIR
    if journal.is_symlink() or evidence.is_symlink():
        raise FabricA6BindingRepairError("fabric_a6_state_unsafe")
    present = (journal.exists(), evidence.exists())
    if any(present) and not all(present):
        raise FabricA6BindingRepairError("fabric_a6_state_incomplete")
    return all(present)


def inspect_a6_binding_state(
    *,
    config_dir: Path,
    state_root: Path,
) -> dict[str, object]:
    """Return sanitized fixed A6 persistence state without paths or values."""

    from .onboarding import load_env_file

    config = _resolve_a6_config_dir(config_dir)
    env_path = config / "runner-mcp.env"
    try:
        _require_private_file(env_path)
        values = load_env_file(env_path)
    except (OSError, RuntimeError, UnicodeError) as exc:
        raise FabricA6BindingRepairError("fabric_a6_runtime_config_unavailable") from exc

    binding_count = sum(
        1 for key in _A6_KEYS if bool(values.get(key, "").strip())
    )
    root = _resolve_a6_state_root(state_root)
    journal = root / _JOURNAL_DIR
    evidence = root / _EVIDENCE_DIR
    if journal.is_symlink() or evidence.is_symlink():
        root_state = "unsafe"
    else:
        present = (journal.exists(), evidence.exists())
        if not any(present):
            root_state = "absent"
        elif not all(present):
            root_state = "incomplete"
        else:
            try:
                _require_private_state_dir(root, _JOURNAL_DIR)
                _require_private_state_dir(root, _EVIDENCE_DIR)
            except FabricA6BindingRepairError:
                root_state = "unsafe"
            else:
                root_state = "ready"

    return {
        "state_roots": root_state,
        "binding_count": binding_count,
        "binding_total": len(_A6_KEYS),
        "binding_complete": binding_count == len(_A6_KEYS),
    }



def classify_a6_bindings_for_doctor(inspection: Mapping[str, object]) -> tuple[str, str]:
    """Classify safe A6 *configuration*, never certify A6 update authority.

    An absent, unconfigured A6 is safe for general server operation, but it
    cannot be treated as PASS by an update-readiness consumer. Real update
    admission also requires off-target journal, A7 rollback and original ACK.
    """
    if not isinstance(inspection, Mapping):
        return "warn", "unavailable"
    roots = inspection.get("state_roots")
    count = inspection.get("binding_count")
    total = inspection.get("binding_total")
    complete = inspection.get("binding_complete")
    if (
        roots not in ("ready", "absent", "incomplete", "unsafe")
        or type(count) is not int
        or type(total) is not int
        or total != len(_A6_KEYS)
        or count < 0
        or count > total
        or type(complete) is not bool
        or complete != (count == total)
    ):
        return "warn", "unavailable"
    if roots == "ready" and complete:
        # PASS confirms this narrow private configuration, not off-target
        # physical storage or protected A6/A7 update recovery.
        return "pass", f"ready_{count}_of_{total}"
    if roots == "absent" and count == 0:
        return "warn", f"not_configured_0_of_{total}"
    return "warn", f"{roots}_{count}_of_{total}"


def repair_a6_qualification_binding(
    *,
    environment: MutableMapping[str, str],
    config_dir: Path,
    state_root: Path,
    fabric_revision: str,
) -> None:
    """Restore only the fixed A6 binding when its durable state roots already exist."""

    if not isinstance(fabric_revision, str) or _COMMIT_RE.fullmatch(fabric_revision) is None:
        raise FabricA6BindingRepairError("fabric_a6_revision_invalid")

    config = _resolve_a6_config_dir(config_dir)
    env_path = config / "runner-mcp.env"
    try:
        _require_private_file(env_path)
    except (OSError, RuntimeError) as exc:
        raise FabricA6BindingRepairError("fabric_a6_runtime_config_unavailable") from exc

    root = _resolve_a6_state_root(state_root)
    if not a6_state_requested(root):
        return

    journal = _require_private_state_dir(root, _JOURNAL_DIR)
    evidence = _require_private_state_dir(root, _EVIDENCE_DIR)

    bearer = environment.get(_RUNNER_MCP_BEARER_ENV, "")
    if not _valid_secret(bearer):
        raise FabricA6BindingRepairError("fabric_a6_runner_mcp_auth_unavailable")

    updates = {
        "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": str(journal),
        "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN": _JOURNAL_DOMAIN,
        "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN": _TARGET_DOMAIN,
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": _RUNNER_MCP_ENDPOINT,
        "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": bearer,
        "RUNNER_FABRIC_SYNTHETIC_PROBE_ID": _PROBE_ID,
        "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT": _TARGET_SUBJECT,
        "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION": fabric_revision,
        "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS": _INTERVAL_SECONDS,
        "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT": str(evidence),
        "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION": fabric_revision,
    }
    try:
        _merge_private_env(env_path, updates)
    except FabricWorkerQualificationProvisioningError as exc:
        raise FabricA6BindingRepairError("fabric_a6_runtime_config_update_failed") from exc
    environment.update(updates)


def _require_private_state_dir(root: Path, name: str) -> Path:
    target = root / name
    if target.is_symlink():
        raise FabricA6BindingRepairError("fabric_a6_state_unsafe")
    try:
        resolved_root = root.resolve(strict=True)
        resolved = target.resolve(strict=True)
        stat = resolved.stat()
    except (OSError, RuntimeError) as exc:
        raise FabricA6BindingRepairError("fabric_a6_state_unavailable") from exc
    if (
        resolved.parent != resolved_root
        or not resolved.is_dir()
        or stat.st_uid != os.geteuid()
        or stat.st_mode & 0o777 != 0o700
    ):
        raise FabricA6BindingRepairError("fabric_a6_state_unsafe")
    return resolved


def _valid_secret(value: object) -> bool:
    return (
        isinstance(value, str)
        and 32 <= len(value) <= 4096
        and value.isascii()
        and all(33 <= ord(char) < 127 for char in value)
    )
