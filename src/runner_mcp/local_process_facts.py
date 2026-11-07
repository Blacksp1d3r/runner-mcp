"""Linux-only read-only identity for the current Runner-MCP process.

This adapter reads kernel-owned /proc evidence without shell, systemd, network,
privilege elevation or service changes. It does not verify a remote client route,
loaded artifact, service ownership, or independent witness identity. The
canonical AF asset/service binding must be supplied by AIfordable authority.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_BOOT_ID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")


class LocalProcessFactsUnavailable(RuntimeError):
    """Kernel process identity cannot be measured; must never imply healthy."""


@dataclass(frozen=True, slots=True)
class LinuxProcessFacts:
    boot_id: str
    process_id: int
    start_ticks: int
    source: str = "linux:procfs"
    platform: str = "linux"

    @property
    def generation(self) -> str:
        """Boot plus kernel start ticks distinguishes PID reuse across reboot."""
        return f"{self.boot_id}:{self.process_id}:{self.start_ticks}"


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
            raise ValueError("invalid proc root")
        boot = (proc / "sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
        if not _BOOT_ID.fullmatch(boot):
            raise ValueError("invalid boot identifier")
        stat = (proc / str(pid) / "stat").read_text(encoding="ascii")
        # Process names can contain spaces and right parentheses. Field 22 is
        # the 20th token *after the final closing parenthesis* (fields 3+).
        boundary = stat.rfind(")")
        if boundary < 1 or not stat[:boundary].startswith(f"{pid} ("):
            raise ValueError("invalid process stat header")
        remainder = stat[boundary + 1:].split()
        if len(remainder) < 20:
            raise ValueError("process stat has too few fields")
        start_ticks = int(remainder[19])
        if start_ticks < 1:
            raise ValueError("invalid process start ticks")
        return LinuxProcessFacts(boot_id=boot, process_id=pid, start_ticks=start_ticks)
    except (OSError, UnicodeError, ValueError, OverflowError) as exc:
        raise LocalProcessFactsUnavailable("current process identity unavailable") from exc
