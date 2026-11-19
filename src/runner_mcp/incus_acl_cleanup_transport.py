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


def _fail_closed(stage: str) -> dict[str, object]:
    """Log only an enumerated local failure class, never subprocess details."""
    if stage not in {
        "admission", "spawn_or_timeout", "command_rejected", "invalid_receipt"
    }:
        stage = "unknown"
    _LOG.warning("incus_acl_revoke_unavailable stage=%s", stage)
    return _bounded("unavailable", reason=_UNAVAILABLE)


def _root_installation_present() -> bool:
    """A quick *unprivileged* admission, not proof of the helper's own digest.

    The root-owned helper independently checks its private root-only source
    digest, exact host/socket/account, ACL, inode and post-operation denial.
    """
    try:
        if os.geteuid() == 0:
            return False
        for path in _ROOT_DIRS:
            row = path.lstat()
            if not stat.S_ISDIR(row.st_mode) or row.st_uid != 0:
                return False
            if row.st_mode & 0o022:
                return False
        row = _HELPER.lstat()
        return (
            stat.S_ISREG(row.st_mode)
            and row.st_uid == 0
            and stat.S_IMODE(row.st_mode) == 0o500
            and row.st_nlink == 1
        )
    except OSError:
        return False


def revoke_fixed_incus_qualification_acl() -> dict[str, object]:
    """Request one OS-authorized, fixed root helper invocation or fail closed.

    Even a valid helper must refuse any unknown ACL; no fallback to
    setfacl, arbitrary shell, direct Incus management or root escalation.
    """
    if not _root_installation_present():
        return _fail_closed("admission")
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
