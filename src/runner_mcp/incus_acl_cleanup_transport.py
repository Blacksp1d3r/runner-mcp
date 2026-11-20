"""#520: one fixed, revoke-only invocation of an independently root-owned helper.

The authenticated Runner-MCP server remains unprivileged.  This module
neither installs sudoers policy nor grants any socket access.  OS sudo must
independently admit the *single fixed argv* for the actual server account.
No caller-supplied host, path, command, user, sudo options or environment.
"""

from __future__ import annotations

import logging
import os
import stat
import subprocess
from pathlib import Path

_HELPER = Path("/usr/local/sbin/runner-mcp-incus-acl-revoke")
_SUDO_ARGV = (
    "/usr/bin/sudo", "-n", "--", "/usr/bin/python3", "-I", "-S",
    str(_HELPER),
)
_ROOT_DIRS = (
    Path("/"), Path("/usr"), Path("/usr/local"), Path("/usr/local/sbin"),
)
_SCHEMA = "runner-mcp/incus-qualification-acl-revoke/v1"
_UNAVAILABLE = "privileged_helper_unavailable"
_LOG = logging.getLogger(__name__)
_PASSED = {
    "INCUS_ACL_REVOKE=PASS:already_restored": "already_restored",
    "INCUS_ACL_REVOKE=PASS:revoke_only": "revoked",
}


def _bounded(state: str, *, reason: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "schemaVersion": _SCHEMA,
        "state": state,
        "normalActivationEnabled": False,
    }
    if reason is not None:
        result["reasonCode"] = reason
    return result


_ROOT_LABELS = ("root", "usr", "usr_local", "usr_local_sbin")
_ADMISSION_DETAILS = frozenset(
    {"caller_root", "helper_unavailable", "helper_invalid", "helper_mode", "helper_links"}
    | {f"{label}_{code}" for label in _ROOT_LABELS
       for code in ("unavailable", "invalid", "writable")}
)


def _fail_closed(
    stage: str, *, admission_detail: str | None = None
) -> dict[str, object]:
    """Write only fixed failure classes to the existing private service journal."""
    if stage not in {
        "admission", "spawn_or_timeout", "command_rejected", "invalid_receipt"
    }:
        stage = "unknown"
    if stage == "admission" and admission_detail in _ADMISSION_DETAILS:
        _LOG.warning(
            "incus_acl_revoke_unavailable stage=%s detail=%s",
            stage, admission_detail,
        )
    else:
        _LOG.warning("incus_acl_revoke_unavailable stage=%s", stage)
    return _bounded("unavailable", reason=_UNAVAILABLE)


def _root_installation_reason() -> str | None:
    """Enumerate only the first failed fixed admission condition.

    No stat values, inspected paths, exception messages or private details
    leave this function. None means the original root-owned checks passed.
    """
    if os.geteuid() == 0:
        return "caller_root"
    for label, path in zip(_ROOT_LABELS, _ROOT_DIRS, strict=True):
        try:
            row = path.lstat()
        except OSError:
            return f"{label}_unavailable"
        if not stat.S_ISDIR(row.st_mode) or row.st_uid != 0:
            return f"{label}_invalid"
        if row.st_mode & 0o022:
            return f"{label}_writable"
    try:
        row = _HELPER.lstat()
    except OSError:
        return "helper_unavailable"
    if not stat.S_ISREG(row.st_mode) or row.st_uid != 0:
        return "helper_invalid"
    if stat.S_IMODE(row.st_mode) != 0o500:
        return "helper_mode"
    if row.st_nlink != 1:
        return "helper_links"
    return None


def _root_installation_present() -> bool:
    """Original fail-closed gate; the root helper still checks its own digest."""
    return _root_installation_reason() is None


def revoke_fixed_incus_qualification_acl() -> dict[str, object]:
    """Request one OS-authorized, fixed root helper invocation or fail closed.

    Even a valid helper must refuse any unknown ACL; no fallback to
    setfacl, arbitrary shell, direct Incus management or root escalation.
    """
    if not _root_installation_present():
        return _fail_closed("admission", admission_detail=_root_installation_reason())
    try:
        result = subprocess.run(
            _SUDO_ARGV,
            check=False,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
            cwd="/",
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
                 "LANG": "C", "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        return _fail_closed("spawn_or_timeout")
    if result.returncode != 0:
        return _fail_closed("command_rejected")
    state = _PASSED.get(result.stdout.strip())
    if state is None or result.stdout.count("\n") != 1:
        return _fail_closed("invalid_receipt")
    return _bounded(state)
