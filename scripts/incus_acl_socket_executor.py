#!/usr/bin/python3
"""#520 — vaste Incus-ACL-intrekking aan de HOST-rootgrens.

Deze korte systemd-socket-activated uitvoerder gebruikt alleen Python stdlib.
Hij accepteert precies één vaste actie plus een niet-autoriserende replay-ID.
De bestaande, afzonderlijk verzegelde root-helper blijft de enige ACL-writer.
Een niet-gekwalificeerde installatie, peer, helper of onzekere transactie STOP.
Geen opties, shell, nieuwe credentials, fabric- of Incus-beheercommando's.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import socket
import stat
import struct
import subprocess
import sys
from pathlib import Path

_ACTION = "incus_qualification_acl_revoke"
_HELPER = Path("/usr/local/sbin/runner-mcp-incus-acl-revoke")
_POLICY = Path("/etc/runner-mcp/incus-qualification-acl-policy.json")
_LEDGER_DIR = Path("/var/lib/runner-mcp/incus-acl-executor")
_LEDGER = "revoke-ledger"
_RE = re.compile(rb"RMCP520/1 ([0-9a-f]{32})\n\Z")
_SCHEMA = "runner-mcp/root-incus-qualification-acl-revoke/v1"
_OUTCOMES = {
    "INCUS_ACL_REVOKE=PASS:already_restored\n": "already_restored",
    "INCUS_ACL_REVOKE=PASS:revoke_only\n": "revoked",
}
_RECORD_RE = re.compile(r"([0-9a-f]{32}) (PENDING|PASS:already_restored|PASS:revoked)\Z")
_MAX_LEDGER = 65536
_MAX_ENTRIES = 512


class Denied(Exception):
    """Een begrensde weigering zonder gevoelige informatie."""


def _root_only() -> None:
    """Een echte systeem-root, nooit de overflow-UID van een user namespace."""
    if os.geteuid() != 0:
        raise Denied("not_host_root")
    if os.stat("/proc/self/ns/user").st_ino != os.stat("/proc/1/ns/user").st_ino:
        raise Denied("not_host_root")
    if os.lstat("/").st_uid != 0:
        raise Denied("not_host_root")


def _trusted_file(path: Path, mode: int, limit: int) -> bytes:
    """Lees een door root beheerd pad, zonder wijzigbare ouder of symlink."""
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                          dir_fd=directory)
            os.close(directory)
            directory = new
            item = os.fstat(directory)
            if item.st_uid != 0 or item.st_mode & 0o022:
                raise Denied("untrusted_install")
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        try:
            item = os.fstat(fd)
            if (not stat.S_ISREG(item.st_mode) or item.st_uid != 0
                    or stat.S_IMODE(item.st_mode) != mode
                    or item.st_nlink != 1 or not 0 < item.st_size <= limit):
                raise Denied("untrusted_install")
            data = os.read(fd, limit + 1)
            if len(data) != item.st_size or os.fstat(fd) != item:
                raise Denied("untrusted_install")
            return data
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def _binding() -> tuple[int, int]:
    raw = _trusted_file(_POLICY, 0o600, 4096)
    try:
        doc = json.loads(raw)
        if (type(doc) is not dict or doc.get("schema") != _SCHEMA
                or doc.get("host_short") != os.uname().nodename.split(".")[0]):
            raise Denied("host_policy")
        uid, gid, digest = doc["owner_uid"], doc["owner_gid"], doc["installed_sha256"]
        if (type(uid) is not int or uid < 1 or type(gid) is not int or gid < 1
                or type(digest) is not str
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            raise Denied("host_policy")
    except (ValueError, KeyError, TypeError) as exc:
        raise Denied("host_policy") from exc
    if hashlib.sha256(_trusted_file(_HELPER, 0o500, 65536)).hexdigest() != digest:
        raise Denied("helper_digest")
    return uid, gid


def _start_ticks(pid: int) -> str:
    """Lees veld 22 zonder een veranderlijke procesnaam te vertrouwen."""
    value = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    tail = value.rsplit(")", 1)[1].split()
    if len(tail) < 20:
        raise Denied("peer_generation")
    return tail[19]


def _peer(conn: socket.socket, uid: int, gid: int) -> tuple[int, str]:
    """SO_PEERCRED + exact één proces in de oorspronkelijke user-unit."""
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    pid, peer_uid, peer_gid = struct.unpack("3i", raw)
    if pid <= 1 or peer_uid != uid or peer_gid != gid:
        raise Denied("peer_credentials")
    cgroup = (
        f"/user.slice/user-{uid}.slice/user@{uid}.service/"
        "app.slice/runner-mcp.service"
    )
    expected = f"0::{cgroup}"
    if Path(f"/proc/{pid}/cgroup").read_text(encoding="ascii").strip() != expected:
        raise Denied("peer_unit")
    members = Path("/sys/fs/cgroup" + cgroup + "/cgroup.procs").read_text(
        encoding="ascii"
    ).split()
    if members != [str(pid)]:
        raise Denied("peer_not_exclusive")
    status = Path(f"/proc/{pid}/status").read_text(encoding="ascii")
    expected_ids = f"{uid}\t{uid}\t{uid}\t{uid}"
    expected_groups = f"{gid}\t{gid}\t{gid}\t{gid}"
    if (re.search(r"^Uid:\s*(.+)$", status, re.M).group(1) != expected_ids
            or re.search(r"^Gid:\s*(.+)$", status, re.M).group(1) != expected_groups
            or re.search(r"^NoNewPrivs:\s*(\d+)$", status, re.M).group(1) != "1"):
        raise Denied("peer_security")
    if Path(f"/proc/{pid}/comm").read_text(encoding="ascii").strip() != "runner-mcp":
        raise Denied("peer_process")
    return pid, _start_ticks(pid)


def _same_peer(pid: int, start: str, uid: int) -> bool:
    try:
        expected = (
            f"0::/user.slice/user-{uid}.slice/user@{uid}.service/"
            "app.slice/runner-mcp.service"
        )
        return (_start_ticks(pid) == start
                and Path(f"/proc/{pid}/cgroup").read_text().strip() == expected)
    except (OSError, IndexError, ValueError):
        return False


def _append(fd: int, value: str) -> None:
    os.lseek(fd, 0, os.SEEK_END)
    if os.fstat(fd).st_size + len(value) + 1 > _MAX_LEDGER:
        raise Denied("ledger_full")
    os.write(fd, (value + "\n").encode("ascii"))
    os.fsync(fd)


def _ledger_open() -> int:
    """Alleen één door systemd root-eigenaar aangemaakte private statusmap."""
    info = _LEDGER_DIR.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != 0
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise Denied("ledger_untrusted")
    parent = os.open(_LEDGER_DIR, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(_LEDGER, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
    finally:
        os.close(parent)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
        os.close(fd)
        raise Denied("ledger_untrusted")
    return fd


def _records(fd: int) -> dict[str, str]:
    length = os.fstat(fd).st_size
    if length > _MAX_LEDGER:
        raise Denied("ledger_full")
    os.lseek(fd, 0, os.SEEK_SET)
    raw = os.read(fd, _MAX_LEDGER + 1)
    try:
        lines = raw.decode("ascii").splitlines(keepends=True)
    except UnicodeError as exc:
        raise Denied("ledger_invalid") from exc
    entries: dict[str, str] = {}
    for line in lines:
        if not line.endswith("\n"):
            raise Denied("ledger_invalid")
        match = _RECORD_RE.fullmatch(line[:-1])
        if match is None:
            raise Denied("ledger_invalid")
        key, state = match.groups()
        if key in entries and (entries[key] != "PENDING"
                               or not state.startswith("PASS:")):
            raise Denied("ledger_invalid")
        if key not in entries and state != "PENDING":
            raise Denied("ledger_invalid")
        entries[key] = state
    if len(entries) >= _MAX_ENTRIES:
        raise Denied("ledger_full")
    return entries


def _helper() -> str:
    result = subprocess.run(
        ("/usr/bin/python3", "-I", "-S", str(_HELPER)),
        shell=False, check=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        cwd="/", text=True, timeout=18,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
             "LANG": "C", "LC_ALL": "C"},
    )
    if result.returncode != 0:
        raise Denied("helper_denied")
    state = _OUTCOMES.get(result.stdout)
    if state is None:
        raise Denied("helper_receipt")
    return state


def execute(conn: socket.socket) -> None:
    """Eén aanvraag; onderbroken PENDING voorkomt dubbele onzekere uitvoering."""
    _root_only()
    uid, gid = _binding()
    pid, start = _peer(conn, uid, gid)
    conn.settimeout(3)
    data = conn.recv(80)
    match = _RE.fullmatch(data)
    if match is None:
        raise Denied("request_invalid")
    token = match.group(1).decode("ascii")
    fd = _ledger_open()
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        records = _records(fd)
        if token in records and records[token].startswith("PASS:"):
            state = records[token][5:]
        else:
            if any(value == "PENDING" for value in records.values()):
                raise Denied("recovery_required")
            _append(fd, f"{token} PENDING")
            state = _helper()
            if not _same_peer(pid, start, uid):
                raise Denied("peer_generation")
            _append(fd, f"{token} PASS:{state}")
        # Een succesbewijs bestaat pas na een fsync van de root-owned ontvangst.
        conn.sendall(f"RMCP520/1 {token} PASS {state}\n".encode("ascii"))
        print("RMCP520_ROOT_ACK=PASS", file=sys.stderr, flush=True)
    finally:
        os.close(fd)


def main() -> int:
    if len(sys.argv) != 1:
        return 2
    try:
        with socket.socket(fileno=0) as conn:
            execute(conn)
        return 0
    except (Denied, OSError, ValueError, IndexError, subprocess.SubprocessError):
        # Nooit stdout, stderr van helper, padwaarden of interne fouten tonen.
        print("RMCP520_ROOT=DENIED", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
