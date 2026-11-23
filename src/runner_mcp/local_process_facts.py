"""Linux-only read-only identity for the current Runner-MCP process.

This adapter reads kernel-owned /proc evidence without shell, systemd, network,
privilege elevation or service changes. It does not verify a remote client route,
loaded artifact, service ownership, or independent witness identity. The
canonical AF asset/service binding must be supplied by AIfordable authority.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_BOOT_ID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
# /proc/<pid>/ns/net is a kernel-managed symlink. Never follow it: only read
# the fixed net:[inode] label for the current process.
_NETNS = re.compile(r"^net:\[([1-9][0-9]{0,19})\]$")


class LocalProcessFactsUnavailable(RuntimeError):
    """Kernel process identity cannot be measured; must never imply healthy."""


@dataclass(frozen=True, slots=True)
class LinuxProcessFacts:
    boot_id: str
    process_id: int
    start_ticks: int
    source: str = "linux:procfs"
    platform: str = "linux"
    network_namespace_inode: int | None = None

    @property
    def generation(self) -> str:
        """Boot plus kernel start ticks distinguishes PID reuse across reboot."""
        return f"{self.boot_id}:{self.process_id}:{self.start_ticks}"


def _start_ticks(stat: str, pid: int) -> int:
    """Parse kernel stat field 22 without trusting a parenthesized comm field."""
    boundary = stat.rfind(")")
    if boundary < 1 or not stat[:boundary].startswith(f"{pid} ("):
        raise ValueError("invalid process stat header")
    remainder = stat[boundary + 1:].split()
    if len(remainder) < 20:
        raise ValueError("process stat has too few fields")
    value = int(remainder[19])
    if value < 1:
        raise ValueError("invalid process start ticks")
    return value


def _read_netns_inode(proc: Path, pid: int) -> int | None:
    """Read only the kernel namespace label; missing capability stays unknown.

    No globbing, namespace traversal, peer inspection or socket scanning. A
    missing/invalid label does not bind any observation to a listening port.
    """
    try:
        label = os.readlink(proc / str(pid) / "ns/net")
    except (OSError, ValueError, TypeError):
        return None
    match = _NETNS.fullmatch(label)
    if match is None:
        return None
    inode = int(match.group(1))
    return inode if inode <= (2**64 - 1) else None


def read_current_linux_process(
    *,
    proc: Path = Path("/proc"),
    getpid: Callable[[], int] = os.getpid,
) -> LinuxProcessFacts:
    """Read only the *current* process' kernel identity, never a remote PID.

    The proc and getpid parameters only support isolated fixture tests. Do not
    expose them as MCP arguments or turn them into caller-selected host paths.
    """
    try:
        pid = getpid()
        if type(pid) is not int or pid < 1:
            raise ValueError("invalid PID")
        if not isinstance(proc, Path):
            raise TypeError("invalid proc root")
        boot = (proc / "sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
        if not _BOOT_ID.fullmatch(boot):
            raise ValueError("invalid boot identifier")
        stat_path = proc / str(pid) / "stat"
        ticks = _start_ticks(stat_path.read_text(encoding="ascii"), pid)
        # A reused PID must not combine two different process generations.
        netns_inode = _read_netns_inode(proc, pid)
        if _start_ticks(stat_path.read_text(encoding="ascii"), pid) != ticks:
            raise ValueError("process generation changed during observation")
        return LinuxProcessFacts(
            boot_id=boot,
            process_id=pid,
            start_ticks=ticks,
            network_namespace_inode=netns_inode,
        )
    except (OSError, UnicodeError, ValueError, OverflowError, TypeError) as exc:
        raise LocalProcessFactsUnavailable("current process identity unavailable") from exc
