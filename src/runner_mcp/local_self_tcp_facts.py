"""Bounded Linux /proc/self TCP listener inode observation.

No socket is opened, no network request is made, and no arbitrary process or
namespace can be selected. Reads the current process's file-descriptor links
and its kernel network-namespace tables, retaining only positive inode matches.
A failed, incomplete or racing snapshot returns None (UNKNOWN), not absence.
The optional proc root is solely for synthetic fixture tests.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_SOCKET = re.compile(r"^socket:\[([1-9][0-9]{0,19})\]$")
_MAX_FDS = 512
_MAX_TABLE_BYTES = 512 * 1024
_MAX_LISTENERS = 128
_MAX_INODE = (1 << 64) - 1


def _own_socket_inodes(proc: Path) -> frozenset[int] | None:
    try:
        entries = list((proc / "self/fd").iterdir())
        if len(entries) > _MAX_FDS:
            return None
        found: set[int] = set()
        for entry in entries:
            if not entry.name.isascii() or not entry.name.isdecimal():
                return None
            label = os.readlink(entry)
            if not label.startswith("socket:"):
                continue
            match = _SOCKET.fullmatch(label)
            if match is None:
                return None
            inode = int(match.group(1))
            if inode > _MAX_INODE:
                return None
            found.add(inode)
        return frozenset(found)
    except (OSError, TypeError, ValueError, OverflowError):
        return None


def _tcp_listeners(proc: Path, inodes: frozenset[int]) -> tuple[tuple[str, int], ...] | None:
    found: set[tuple[str, int]] = set()
    try:
        for family, size, name in (
            ("tcp4", 8, "tcp"),
            ("tcp6", 32, "tcp6"),
        ):
            with (proc / "self/net" / name).open("r", encoding="ascii") as stream:
                content = stream.read(_MAX_TABLE_BYTES + 1)
            if len(content) > _MAX_TABLE_BYTES:
                return None
            lines = content.splitlines()
            if not lines or "local_address" not in lines[0]:
                return None
            for row in lines[1:]:
                columns = row.split()
                if len(columns) < 10:
                    return None
                if columns[3] != "0A":
                    continue
                raw_inode = columns[9]
                if not raw_inode.isascii() or not raw_inode.isdecimal():
                    return None
                inode = int(raw_inode)
                if inode not in inodes:
                    continue
                local = columns[1].split(":")
                if len(local) != 2:
                    return None
                address, raw_port = local
                if (
                    len(address) != size
                    or any(ch not in "0123456789ABCDEFabcdef" for ch in address)
                    or len(raw_port) != 4
                    or any(ch not in "0123456789ABCDEFabcdef" for ch in raw_port)
                ):
                    return None
                port = int(raw_port, 16)
                if port < 1:
                    return None
                found.add((family, port))
                if len(found) > _MAX_LISTENERS:
                    return None
        return tuple(sorted(found))
    except (OSError, UnicodeError, ValueError, OverflowError):
        return None


def read_current_self_tcp_listeners(
    *, proc: Path = Path("/proc")
) -> tuple[tuple[str, int], ...] | None:
    """Only own live FD inodes intersecting own netns TCP LISTEN entries.

    This positive self-process evidence is not the listening address, public
    reachability, child ownership, app health, process wheel or verification.
    """
    if not isinstance(proc, Path):
        return None
    first = _own_socket_inodes(proc)
    if first is None:
        return None
    before = _tcp_listeners(proc, first)
    if before is None:
        return None
    second = _own_socket_inodes(proc)
    if second is None or first != second:
        return None
    after = _tcp_listeners(proc, second)
    return before if after is not None and before == after else None
