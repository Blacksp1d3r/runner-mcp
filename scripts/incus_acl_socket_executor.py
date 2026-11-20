"""#520 — vaste Incus-ACL-intrekking aan de HOST-rootgrens.

Deze korte systemd-socket-activated uitvoerder gebruikt alleen Python stdlib.
Hij accepteert precies één vaste actie plus een niet-autoriserende replay-ID.
De bestaande, afzonderlijk verzegelde root-helper blijft de enige ACL-writer.
Een niet-gekwalificeerde installatie, peer, helper of onzekere transactie STOP.
Geen opties, shell, nieuwe credentials, fabric- of Incus-beheercommando's.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import pwd
import re
import socket
import stat
import struct
import subprocess
import sys
from pathlib import Path

_ACTION = "incus_qualification_acl_revoke"
_HELPER = Path("/usr/local/sbin/runner-mcp-incus-acl-revoke")
_INCUS_SOCKET = Path("/var/lib/incus/unix.socket")
_POLICY = Path("/etc/runner-mcp/incus-qualification-acl-policy.json")
_LEDGER_DIR = Path("/var/lib/runner-mcp/incus-acl-executor")
_LEDGER = "revoke-ledger"
_RE = re.compile(rb"RMCP520/1 ([0-9a-f]{32})\n\Z")
_SCHEMA = "runner-mcp/root-incus-qualification-acl-revoke/v1"
_OUTCOMES = {
    "INCUS_ACL_REVOKE=PASS:already_restored\n": "already_restored",
    "INCUS_ACL_REVOKE=PASS:revoke_only\n": "revoked",
}
_RECORD_RE = re.compile(
    r"([0-9a-f]{32}) "
    r"(PENDING|PASS:(?:already_restored|revoked)"
    r"(?::(?:0|[1-9][0-9]{0,19})){3})\Z"
)
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
            after = os.fstat(fd)
            seal = lambda p: (p.st_dev, p.st_ino, p.st_uid, p.st_mode,
                              p.st_size, p.st_mtime_ns, p.st_ctime_ns)
            if len(data) != item.st_size or seal(after) != seal(item):
                raise Denied("untrusted_install")
            return data
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def _binding() -> tuple[int, int, int]:
    raw = _trusted_file(_POLICY, 0o600, 4096)
    try:
        doc = json.loads(raw)
        expected_keys = {
            "schema", "host_short", "owner_name", "owner_uid", "owner_gid",
            "socket_path", "socket_gid", "installed_sha256",
        }
        if (type(doc) is not dict or set(doc) != expected_keys
                or doc["schema"] != _SCHEMA
                or doc["host_short"] != os.uname().nodename.split(".")[0]
                or doc["socket_path"] != str(_INCUS_SOCKET)):
            raise Denied("host_policy")
        uid, gid, digest = doc["owner_uid"], doc["owner_gid"], doc["installed_sha256"]
        name, socket_gid = doc["owner_name"], doc["socket_gid"]
        if (type(uid) is not int or uid < 1 or type(gid) is not int or gid < 1
                or type(socket_gid) is not int or socket_gid < 1
                or type(name) is not str
                or re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", name) is None
                or type(digest) is not str
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            raise Denied("host_policy")
        original = pwd.getpwnam(name)
        if original.pw_uid != uid or original.pw_gid != gid:
            raise Denied("host_policy")
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise Denied("host_policy") from exc
    if hashlib.sha256(_trusted_file(_HELPER, 0o500, 65536)).hexdigest() != digest:
        raise Denied("helper_digest")
    return uid, gid, socket_gid


def _start_ticks(pid: int) -> str:
    """Lees veld 22 zonder een veranderlijke procesnaam te vertrouwen."""
    value = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    tail = value.rsplit(")", 1)[1].split()
    if len(tail) < 20:
        raise Denied("peer_generation")
    return tail[19]


def _peer(conn: socket.socket, uid: int, gid: int, socket_gid: int) -> tuple[int, str]:
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
    fields = dict(line.split(":", 1) for line in status.splitlines()
                  if ":" in line)
    if (fields.get("Uid", "").split() != [str(uid)] * 4
            or fields.get("Gid", "").split() != [str(gid)] * 4
            or fields.get("NoNewPrivs", "").split() != ["1"]):
        raise Denied("peer_security")
    # Effective=0 alone is insufficient: permitted/inheritable/ambient
    # capabilities could be raised later without an exec transition.
    try:
        for cap_key in ("CapInh", "CapPrm", "CapEff", "CapAmb"):
            if int(fields.get(cap_key, "-1").strip(), 16) != 0:
                raise Denied("peer_security")
    except ValueError as exc:
        raise Denied("peer_security") from exc
    # A socket with only the base ACL may still be writable via its
    # POSIX owning group; no cached success may bypass this check.
    if ("Groups" not in fields or gid == socket_gid
            or str(socket_gid) in fields["Groups"].split()):
        raise Denied("peer_socket_group")
    # Keep the original isolated service's ONE mapped user and group;
    # admitting a broader user namespace could silently remap host root.
    for map_name, expected_id in (("uid_map", uid), ("gid_map", gid)):
        values = Path(f"/proc/{pid}/{map_name}").read_text(
            encoding="ascii"
        ).split()
        if values != [str(expected_id), str(expected_id), "1"]:
            raise Denied("peer_namespace")
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
    """Een resultaat wordt NOOIT bevestigd na slechts een gedeeltelijke write."""
    payload = (value + "\n").encode("ascii")
    os.lseek(fd, 0, os.SEEK_END)
    if os.fstat(fd).st_size + len(payload) > _MAX_LEDGER:
        raise Denied("ledger_full")
    remaining = memoryview(payload)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise Denied("ledger_io")
        remaining = remaining[written:]
    os.fsync(fd)


def _ledger_open() -> int:
    """Alleen één door systemd root-eigenaar aangemaakte private statusmap."""
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in _LEDGER_DIR.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=parent)
            os.close(parent)
            parent = next_fd
            item = os.fstat(parent)
            if item.st_uid != 0 or item.st_mode & 0o022:
                raise Denied("ledger_untrusted")
        item = os.fstat(parent)
        if stat.S_IMODE(item.st_mode) != 0o700:
            raise Denied("ledger_untrusted")
        try:
            fd = os.open(_LEDGER, os.O_RDWR | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        except FileExistsError:
            fd = os.open(_LEDGER, os.O_RDWR | os.O_NOFOLLOW,
                         dir_fd=parent)
        else:
            try:
                os.fsync(parent)  # Durable new pathname before any helper actuation.
            except OSError:
                os.close(fd)
                raise
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
    raw = os.read(fd, length + 1)
    # A partial read ending on a valid newline must not hide a later PENDING.
    if len(raw) != length:
        raise Denied("ledger_invalid")
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
    if len(entries) > _MAX_ENTRIES:
        raise Denied("ledger_full")
    return entries


def _socket_generation(expected_gid: int) -> str:
    """Hercontroleer basis-ACL en socketgeneratie vóór een (ook herhaalde) ACK.

    Het door de vaste helper bewezen schone ACL-resultaat is geen blijvend
    bewijs na een latere grant: de cached ACK is dan STALE, niet PASS.
    De afwezigheid van de Linux POSIX-ACL-xattr is na setfacl -b vereist.
    """
    before = os.lstat(_INCUS_SOCKET)
    if (not stat.S_ISSOCK(before.st_mode) or before.st_uid != 0
            or before.st_gid != expected_gid
            or stat.S_IMODE(before.st_mode) != 0o660
            or before.st_nlink != 1):
        raise Denied("socket_generation")
    try:
        os.getxattr(_INCUS_SOCKET, "system.posix_acl_access",
                    follow_symlinks=False)
    except OSError as exc:
        if exc.errno != errno.ENODATA:
            raise Denied("socket_acl_unverified") from exc
    else:
        raise Denied("socket_acl_unverified")
    after = os.lstat(_INCUS_SOCKET)
    identity = lambda row: (
        row.st_dev, row.st_ino, row.st_ctime_ns,
        row.st_mode, row.st_uid, row.st_gid, row.st_nlink,
    )
    if identity(before) != identity(after):
        raise Denied("socket_generation")
    return f"{after.st_dev}:{after.st_ino}:{after.st_ctime_ns}"


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
    uid, gid, socket_gid = _binding()
    pid, start = _peer(conn, uid, gid, socket_gid)
    conn.settimeout(3)
    data = bytearray()
    while len(data) < 80 and b"\n" not in data:
        chunk = conn.recv(80 - len(data))
        if not chunk:
            break
        data.extend(chunk)
    match = _RE.fullmatch(bytes(data))
    if match is None:
        raise Denied("request_invalid")
    token = match.group(1).decode("ascii")
    fd = _ledger_open()
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        records = _records(fd)
        # An unresolved earlier operation makes *all* cached successes
        # unsafe to acknowledge until the independent recovery process
        # resolves that transaction. Never bypass PENDING via replay.
        if any(value == "PENDING" for value in records.values()):
            raise Denied("recovery_required")
        # Recheck after acquiring the ledger lock: the authenticated MCP
        # process and its credentials must still be eligible before root work.
        new_pid, new_start = _peer(conn, uid, gid, socket_gid)
        if ((new_pid, new_start) != (pid, start)
                or not _same_peer(pid, start, uid)):
            raise Denied("peer_generation")
        replay = token in records and records[token].startswith("PASS:")
        if replay:
            _prefix, state, *generation = records[token].split(":")
            if ":".join(generation) != _socket_generation(socket_gid):
                raise Denied("stale_replay")
        else:
            if len(records) >= _MAX_ENTRIES:
                raise Denied("ledger_full")
            _append(fd, f"{token} PENDING")
            state = _helper()
            # The original process may have exited or changed privileges
            # during the helper; no durable caller ACK after such drift.
            final_pid, final_start = _peer(conn, uid, gid, socket_gid)
            if ((final_pid, final_start) != (pid, start)
                    or not _same_peer(pid, start, uid)):
                raise Denied("peer_generation")
            generation = _socket_generation(socket_gid)
            _append(fd, f"{token} PASS:{state}:{generation}")
        # Audit the fsynced result even if the client disconnects before ACK.
        # Sending bytes does NOT prove the original client consumed the ACK.
        receipt = hashlib.sha256(token.encode("ascii")).hexdigest()
        event = "RMCP520_ROOT_REPLAY" if replay else "RMCP520_ROOT_DURABLE"
        print(event + "=PASS receipt=" + receipt,
              file=sys.stderr, flush=True)
        conn.sendall(f"RMCP520/1 {token} PASS {state}\n".encode("ascii"))
        print("RMCP520_ROOT_SEND=PASS receipt=" + receipt,
              file=sys.stderr, flush=True)
    finally:
        os.close(fd)


def main() -> int:
    if len(sys.argv) != 1:
        return 2
    try:
        with socket.socket(fileno=0) as conn:
            execute(conn)
        return 0
    except Denied as exc:
        # Alleen een door onszelf uitgegeven, enumerated reason; geen hostdata.
        known = {
            "not_host_root", "untrusted_install", "host_policy", "helper_digest",
            "peer_credentials", "peer_unit", "peer_not_exclusive", "peer_security",
            "peer_process", "peer_generation", "peer_socket_group",
            "peer_namespace",
            "request_invalid", "ledger_untrusted",
            "ledger_invalid", "ledger_full", "ledger_io", "recovery_required",
            "helper_denied",
            "helper_receipt", "socket_generation", "socket_acl_unverified",
            "stale_replay",
        }
        code = str(exc) if str(exc) in known else "other"
        print(f"RMCP520_ROOT=DENIED reason={code}", file=sys.stderr, flush=True)
        return 1
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        print("RMCP520_ROOT=DENIED reason=runtime", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
