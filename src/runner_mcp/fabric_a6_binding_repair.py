from __future__ import annotations

import os
import re
from collections.abc import MutableMapping
from pathlib import Path

from .onboarding import load_env_file
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


def a6_state_requested(state_root: Path) -> bool:
    """Return whether the fixed local A6 state roots signal an active A6 campaign."""

    root = state_root.expanduser().resolve()
    journal = root / _JOURNAL_DIR
    evidence = root / _EVIDENCE_DIR
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

    config = config_dir.expanduser().resolve()
    env_path = config / "runner-mcp.env"
    try:
        _require_private_file(env_path)
        values = load_env_file(env_path)
    except (OSError, RuntimeError, UnicodeError) as exc:
        raise FabricA6BindingRepairError("fabric_a6_runtime_config_unavailable") from exc

    binding_count = sum(
        1 for key in _A6_KEYS if bool(values.get(key, "").strip())
    )
    root = state_root.expanduser().resolve()
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

    config = config_dir.expanduser().resolve()
    env_path = config / "runner-mcp.env"
    try:
        _require_private_file(env_path)
    except (OSError, RuntimeError) as exc:
        raise FabricA6BindingRepairError("fabric_a6_runtime_config_unavailable") from exc

    root = state_root.expanduser().resolve()
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
    except OSError as exc:
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
