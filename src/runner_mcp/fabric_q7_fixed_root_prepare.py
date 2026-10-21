"""One narrow owner-only first-host Q7 private custody-root preparation.

No caller-selected path, mounting, chmod, chown, cleanup, or generic directory
manager. Does not qualify a publisher signer, authenticate Black or install
Fabric. Existing safe complete roots are adopted; partial state fails closed.
"""
from __future__ import annotations

import fcntl
import os
import stat
from pathlib import Path

from .fabric_release_private_custody import _private_root_fd


class Q7FixedRootUnqualified(ValueError):
    """Never reveal owner HOME or storage coordinates."""


def _deny() -> None:
    raise Q7FixedRootUnqualified("fabric_q7_fixed_root_unqualified")


def _child_status(fd: int, name: str) -> bool:
    """Is this fixed leaf already a private owner-controlled directory?"""
    try:
        st = os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError:
        _deny()
    if (
        not stat.S_ISDIR(st.st_mode)
        or st.st_uid != os.geteuid()
        or stat.S_IMODE(st.st_mode) != 0o700
    ):
        _deny()
    return True


def _open_private_child(fd: int, name: str) -> int:
    try:
        result = os.open(
            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=fd,
        )
        info = os.fstat(result)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            os.close(result)
            _deny()
        return result
    except OSError:
        _deny()


def _prepare_fixed_q7_root_under(base: Path) -> dict[str, object]:
    """Internal isolated fixture root: only the two fixed child names."""
    if os.geteuid() == 0:
        _deny()
    outer = _private_root_fd(base)
    mid = -1
    try:
        try:
            fcntl.flock(outer, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            _deny()
        first = _child_status(outer, "runner-fabric")
        if first:
            mid = _open_private_child(outer, "runner-fabric")
            second = _child_status(mid, "control-plane-update")
            if not second:
                _deny()  # observed partial root, no automatic repair
            final = _open_private_child(mid, "control-plane-update")
            os.close(final)
            return {
                "state": "already_private",
                "roots_private": True,
                "physical_independence_verified": False,
                "bundle_imported": False,
                "install_authorized": False,
            }
        # Under the existing 0700 owner state anchor, both named descendants
        # are absent. Exclusive mkdir and nofollow descriptor checks only.
        os.mkdir("runner-fabric", 0o700, dir_fd=outer)
        os.fsync(outer)
        mid = _open_private_child(outer, "runner-fabric")
        if _child_status(mid, "control-plane-update"):
            _deny()
        os.mkdir("control-plane-update", 0o700, dir_fd=mid)
        os.fsync(mid)
        final = _open_private_child(mid, "control-plane-update")
        os.close(final)
        return {
            "state": "fixed_root_prepared",
            "roots_private": True,
            "physical_independence_verified": False,
            "bundle_imported": False,
            "install_authorized": False,
        }
    except (OSError, ValueError):
        # Preserve partial state; caller cannot auto-repair or overwrite.
        _deny()
    finally:
        if mid >= 0:
            os.close(mid)
        os.close(outer)


def prepare_black_q7_private_root() -> dict[str, object]:
    """Exactly one hardcoded owner-local Black path; no generic host control."""
    import socket

    if socket.gethostname().split(".")[0] != "black" or os.geteuid() == 0:
        _deny()
    return _prepare_fixed_q7_root_under(Path.home() / ".local/state")
