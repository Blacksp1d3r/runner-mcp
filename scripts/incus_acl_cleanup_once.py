"""#520 — Eenmalige, root-beheerde intrekking van een tijdelijke Incus-ACL.

Zelfstandig, uitsluitend standaardbibliotheek. Alleen een onafhankelijk als
root geïnstalleerd en digest-verzegeld bestand mag worden uitgevoerd, met
een host-/account-/socketbinding uit één root-owned privéconfiguratie.

Aanroep: /usr/bin/python3 -I -S /usr/local/sbin/runner-mcp-incus-acl-revoke
Geen CLI-opties, configuratie uit omgevingsvariabelen of worker-venv-code.
De actie kan nooit rechten toekennen en activeert geen MCP-service.
"""

from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# Generieke, nog niet geactiveerde installatieplaatsen; geen echte hostbinding.
_INSTALLED: Final = Path("/usr/local/sbin/runner-mcp-incus-acl-revoke")
_POLICY: Final = Path("/etc/runner-mcp/incus-qualification-acl-policy.json")
_SCHEMA: Final = "runner-mcp/root-incus-qualification-acl-revoke/v1"
_FIELDS: Final = frozenset({
    "schema", "host_short", "owner_name", "owner_uid", "owner_gid",
    "socket_path", "socket_gid", "installed_sha256",
})
_BASE: Final = frozenset({"user::rw-", "group::rw-", "other::---"})
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_OWNER = re.compile(r"[a-z_][a-z0-9_-]{0,31}\Z")
_HOST = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\Z")
_MAX_POLICY_BYTES = 4096


class CleanupStop(Exception):
    """Sanitized, bounded refusal; error details never reach the caller."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Binding:
    """De uitsluitend root-beheerde, exacte installatiebinding."""

    host_short: str
    owner_name: str
    owner_uid: int
    owner_gid: int
    socket_path: Path
    socket_gid: int
    installed_sha256: str


@dataclass(frozen=True)
class SocketEvidence:
    """De statische socketgeneratie waarmee de ACL-operatie wordt begrensd."""

    device: int
    inode: int
    uid: int
    gid: int
    mode: int
    is_socket: bool
    links: int


class Operation:
    """Alleen NOOP of verwijdering; geen grant- of selectiehandeling."""

    NOOP = "already_restored"
    REVOKE = "revoke_only"


def _acl_action(acl_text: str, owner_uid: int) -> str:
    """Accepteer uitsluitend de basis-ACL, één named grant of een stale mask.

    Onbekende regels, dubbele records, extra named groepen en default ACL
    blokkeren de uitvoerder voordat een bevoegdheid gewijzigd wordt.
    """
    if type(acl_text) is not str or len(acl_text) > 4096:
        raise CleanupStop("acl_unexpected")
    rows = [x for x in acl_text.splitlines() if x]
    unique = set(rows)
    if len(unique) != len(rows):
        raise CleanupStop("acl_unexpected")
    named = f"user:{owner_uid}:rw-"
    if not _BASE <= unique or not unique <= (_BASE | {named, "mask::rw-"}):
        raise CleanupStop("acl_unexpected")
    extra = unique - _BASE
    if not extra:
        return Operation.NOOP
    if extra == {"mask::rw-"} or extra == {named, "mask::rw-"}:
        return Operation.REVOKE
    raise CleanupStop("acl_unexpected")


def plan_cleanup(
    *, binding: Binding, host: str, caller_euid: int,
    socket: SocketEvidence, acl_text: str,
) -> str:
    """Begrensde toelating: ook tests gebruiken exact deze pure beslissing."""
    if caller_euid != 0 or host != binding.host_short:
        raise CleanupStop("host_or_authority_mismatch")
    if (not socket.is_socket or socket.uid != 0 or
        socket.gid != binding.socket_gid or socket.mode != 0o660 or
        socket.links != 1 or socket.device <= 0 or socket.inode <= 0):
        raise CleanupStop("socket_untrusted")
    return _acl_action(acl_text, binding.owner_uid)


def _read_root_file(path: Path, *, exact_mode: int, limit: int) -> bytes:
    """Lees root-owned beleid en code zonder symlinks of schrijfbare ouders."""
    if not path.is_absolute() or ".." in path.parts:
        raise CleanupStop("root_file_untrusted")
    flags = os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW
    parent_fd = os.open("/", flags)
    fd = -1
    try:
        for part in path.parts[1:-1]:
            new_fd = os.open(part, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = new_fd
            p = os.fstat(parent_fd)
            if p.st_uid != 0 or p.st_mode & 0o022 or not stat.S_ISDIR(p.st_mode):
                raise CleanupStop("root_file_untrusted")
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=parent_fd)
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != 0 or
            stat.S_IMODE(before.st_mode) != exact_mode or before.st_nlink != 1 or
            before.st_size < 1 or before.st_size > limit):
            raise CleanupStop("root_file_untrusted")
        data = os.read(fd, limit + 1)
        after = os.fstat(fd)
        current = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if (len(data) != before.st_size or
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or
            (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino)):
            raise CleanupStop("root_file_untrusted")
        return data
    except OSError as exc:
        raise CleanupStop("root_file_untrusted") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)


def _binding() -> Binding:
    try:
        obj = json.loads(_read_root_file(_POLICY, exact_mode=0o600,
                                         limit=_MAX_POLICY_BYTES))
        if not isinstance(obj, dict) or set(obj) != _FIELDS or obj["schema"] != _SCHEMA:
            raise ValueError()
        host = obj["host_short"]
        name = obj["owner_name"]
        owner_uid = obj["owner_uid"]
        owner_gid = obj["owner_gid"]
        socket_gid = obj["socket_gid"]
        location = obj["socket_path"]
        digest = obj["installed_sha256"]
        if (type(host) is not str or not _HOST.fullmatch(host) or
            type(name) is not str or not _OWNER.fullmatch(name) or
            type(owner_uid) is not int or not 1 <= owner_uid < 2**31 or
            type(owner_gid) is not int or not 0 <= owner_gid < 2**31 or
            type(socket_gid) is not int or not 0 <= socket_gid < 2**31 or
            type(location) is not str or not location.startswith("/") or
            ".." in Path(location).parts or "\x00" in location or
            Path(location).name != "unix.socket" or
            Path(location).parent.name != "incus" or
            type(digest) is not str or not _HEX64.fullmatch(digest)):
            raise ValueError()
        account = pwd.getpwnam(name)
        if account.pw_uid != owner_uid or account.pw_gid != owner_gid:
            raise ValueError()
        return Binding(host, name, owner_uid, owner_gid, Path(location),
                       socket_gid, digest)
    except (ValueError, TypeError, KeyError, UnicodeError, OSError) as exc:
        raise CleanupStop("private_policy_invalid") from exc


def _socket(binding: Binding) -> SocketEvidence:
    """Vertrouw alleen socketpaden onder geheel root-beheerde voorouders."""
    path = binding.socket_path
    if not path.is_absolute() or ".." in path.parts:
        raise CleanupStop("socket_untrusted")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=fd)
            os.close(fd)
            fd = next_fd
            item = os.fstat(fd)
            if item.st_uid != 0 or item.st_mode & 0o022:
                raise CleanupStop("socket_untrusted")
        st = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
        return SocketEvidence(st.st_dev, st.st_ino, st.st_uid, st.st_gid,
                              stat.S_IMODE(st.st_mode), stat.S_ISSOCK(st.st_mode),
                              st.st_nlink)
    except OSError as exc:
        raise CleanupStop("socket_untrusted") from exc
    finally:
        os.close(fd)


def _run(argv: list[str], *, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, shell=False,
                              timeout=timeout, check=False, cwd="/",
                              env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
                                   "LANG": "C", "LC_ALL": "C"})
    except (OSError, subprocess.SubprocessError) as exc:
        raise CleanupStop("command_unavailable") from exc


def _acl(path: Path) -> str:
    result = _run(["/usr/bin/getfacl", "-ncp", "--", str(path)])
    if result.returncode != 0:
        raise CleanupStop("acl_unavailable")
    return result.stdout


def _owner_denied(binding: Binding) -> bool:
    """Toets actuele schrijfrechten zonder als root toegang te veronderstellen."""
    code = ("import os,sys;"
            "assert os.getuid()==int(sys.argv[2]);"
            "sys.exit(3 if os.access(sys.argv[1],os.W_OK) else 0)")
    r = _run(["/usr/sbin/runuser", "-u", binding.owner_name, "--",
              "/usr/bin/python3", "-I", "-S", "-c", code,
              str(binding.socket_path), str(binding.owner_uid)])
    return r.returncode == 0


def _verify(binding: Binding, before: SocketEvidence) -> None:
    current = _socket(binding)
    if current != before:
        raise CleanupStop("socket_generation_changed")
    if _acl(binding.socket_path).splitlines() != [
        "user::rw-", "group::rw-", "other::---",
    ]:
        raise CleanupStop("acl_baseline_not_restored")
    if not _owner_denied(binding):
        raise CleanupStop("owner_access_unverified")


def cleanup_once() -> str:
    """Één vaste intrekking. Er is nooit een ACL-grant of actor-activatie."""
    if len(sys.argv) != 1 or os.geteuid() != 0 or not (
        sys.flags.isolated and sys.flags.no_site
    ):
        raise CleanupStop("helper_runtime_untrusted")
    installed = _read_root_file(_INSTALLED, exact_mode=0o500, limit=64 * 1024)
    if Path(sys.argv[0]) != _INSTALLED:
        raise CleanupStop("helper_runtime_untrusted")
    binding = _binding()
    if hashlib.sha256(installed).hexdigest() != binding.installed_sha256:
        raise CleanupStop("helper_source_mismatch")
    if os.uname().nodename.split(".")[0] != binding.host_short:
        raise CleanupStop("host_or_authority_mismatch")
    before = _socket(binding)
    original_acl = _acl(binding.socket_path)
    op = plan_cleanup(binding=binding, host=binding.host_short,
                      caller_euid=os.geteuid(), socket=before,
                      acl_text=original_acl)
    if op == Operation.REVOKE:
        # Volledige ACL-wisactie pas na exact toegelaten extra regels;
        # ook het eventueel achtergebleven masker moet verdwijnen.
        if _socket(binding) != before or _acl(binding.socket_path) != original_acl:
            raise CleanupStop("acl_changed_during_admission")
        result = _run(["/usr/bin/setfacl", "-b", "--", str(binding.socket_path)])
        if result.returncode != 0:
            raise CleanupStop("revoke_failed")
    _verify(binding, before)
    return op


def main() -> int:
    try:
        status = cleanup_once()
    except CleanupStop as exc:
        print(f"INCUS_ACL_REVOKE=STOP:{exc.code}")
        return 2
    except Exception:  # noqa: BLE001 - root-fouten mogen geen details lekken
        print("INCUS_ACL_REVOKE=STOP:unexpected")
        return 2
    print(f"INCUS_ACL_REVOKE=PASS:{status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
