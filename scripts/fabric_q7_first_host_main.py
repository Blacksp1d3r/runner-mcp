"""Private one-shot Q7 source-zipapp entrypoint, never an installer.

This is bundled as __main__.py with only the audited Runner-MCP source modules.
Uses the host's existing qualified Python 3.12 environment and cryptography;
does NOT import a newer globally installed Runner-MCP, run pip or start agents.
"""
from __future__ import annotations

import getpass
import hashlib
import os
import socket
import stat
import sys
from pathlib import Path

from runner_mcp.fabric_q7_fixed_root_prepare import prepare_black_q7_private_root
from runner_mcp.fabric_release_private_custody import _fixed_root, _private_root_fd
from runner_mcp.fabric_release_signed_import import (
    _signed_pins,
    import_signed_pinned_q7_once,
    probe_q7_disposable_lab_metadata,
    import_q7_disposable_lab_once,
    probe_signed_pinned_q7_metadata,
)

_ROOT = Path.home() / ".config/runner-mcp"
_ROSTER = "q7-publisher-signed-roster.json"
_SIGNATURE = "q7-publisher-signature.ed25519"
_KEY = "q7-publisher-key.ed25519"
_TRUST = "q7-independent-key-sha256"
_MAX = {_ROSTER: 32768, _SIGNATURE: 64, _KEY: 32, _TRUST: 65}


class FirstHostDenied(ValueError):
    """No private contents, paths, keys or host metadata in a failure."""


def _deny() -> None:
    raise FirstHostDenied("first_host_q7_preflight_unqualified")


def _owner_private_file(parent_fd: int, name: str, limit: int) -> bytes:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600
                or not 0 < info.st_size <= limit
            ):
                _deny()
            raw = bytearray()
            while len(raw) <= limit:
                part = os.read(fd, min(65536, limit + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
            if len(raw) != info.st_size:
                _deny()
            return bytes(raw)
        finally:
            os.close(fd)
    except OSError:
        _deny()


def _private_inputs() -> tuple[bytes, bytes, bytes, str]:
    """Never create/repair missing private source material or trust key."""
    if socket.gethostname().split(".")[0] != "black" or os.geteuid() == 0:
        _deny()
    config_fd = _private_root_fd(_ROOT)
    try:
        values = {
            name: _owner_private_file(config_fd, name, limit)
            for name, limit in _MAX.items()
        }
    finally:
        os.close(config_fd)
    trust = values[_TRUST]
    if len(trust) == 65 and trust.endswith(b"\n"):
        trust = trust[:-1]
    try:
        fingerprint = trust.decode("ascii")
    except UnicodeDecodeError:
        _deny()
    if len(fingerprint) != 64:
        _deny()
    public_key = values[_KEY]
    if hashlib.sha256(public_key).hexdigest() != fingerprint:
        _deny()
    _signed_pins(values[_ROSTER], values[_SIGNATURE], public_key, fingerprint)
    root_fd = _private_root_fd(_fixed_root())
    os.close(root_fd)
    return values[_ROSTER], values[_SIGNATURE], public_key, fingerprint


def _lab_owner_private_root() -> None:
    """A one-host, no-key test. Refuse root/wrong host/unsafe storage."""
    if socket.gethostname().split(".")[0] != "black" or os.geteuid() == 0:
        _deny()
    fd = _private_root_fd(_fixed_root())
    os.close(fd)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--help"]:
        print("Usage: fabric-q7-first-host.pyz prepare-root | preflight | probe-release | import | lab-preflight | lab-probe-release | lab-import")
        print("Fixed Black host, exact signed Q7 release, no install or service activation.")
        return 0
    if args not in (["prepare-root"], ["preflight"], ["probe-release"], ["import"], ["lab-preflight"], ["lab-probe-release"], ["lab-import"]):
        print("WAIT_UNSUPPORTED_ACTION")
        return 2
    if sys.version_info[:2] != (3, 12):
        print("WAIT_PYTHON")
        return 1
    os.umask(0o077)
    if args == ["prepare-root"]:
        try:
            state = prepare_black_q7_private_root()
            if state.get("state") not in ("fixed_root_prepared", "already_private"):
                _deny()
        except (ValueError, TypeError, OSError):
            print("Q7_FIXED_PRIVATE_ROOT=WAIT")
            return 1
        print("Q7_FIXED_PRIVATE_ROOT=PASS")
        print("NO_SIGNER_AUTHORITY_NO_DOWNLOAD_NO_INSTALL")
        return 0
    lab = args in (["lab-preflight"], ["lab-probe-release"], ["lab-import"])
    try:
        if lab:
            _lab_owner_private_root()
        else:
            roster, signature, public_key, fingerprint = _private_inputs()
    except (ValueError, TypeError, OSError):
        print("WAIT_PRIVATE_LAB_ROOT_OR_SIGNED_ROSTER")
        return 1
    if args == ["lab-preflight"]:
        print("Q7_KEYLESS_DISPOSABLE_LAB=PASS")
        print("UNSIGNED_SOURCE_NO_INSTALL_NO_WORKER")
        return 0
    if args == ["preflight"]:
        print("PINNED_Q7_OFFLINE_INPUTS=PASS")
        print("OPERATOR_SIGNER_AUTHORITY=NOT_ATTESTED")
        print("NO_DOWNLOAD_NO_INSTALL_NO_WORKER")
        return 0
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        print("WAIT_INTERACTIVE_TERMINAL")
        return 1
    try:
        token = getpass.getpass("One-time scoped GitHub Contents:read token (hidden): ")
        try:
            if args == ["lab-probe-release"]:
                result = probe_q7_disposable_lab_metadata(token=token)
                if result.get("state") != "q7_lab_metadata_only_untrusted_publisher":
                    _deny()
                print("Q7_LAB_METADATA=PASS_UNSIGNED")
                print("NO_ASSETS_NO_INSTALL_NO_ACK")
                return 0
            if args == ["lab-import"]:
                result = import_q7_disposable_lab_once(token=token)
                if result.get("state") != "q7_lab_bytes_custodied_only":
                    _deny()
                print("Q7_LAB_PRIVATE_CUSTODY=PASS_UNSIGNED_SOURCE_BYTES_ONLY")
                print("NO_INSTALL_NO_WORKER_NO_ACK")
                return 0
            if args == ["probe-release"]:
                result = probe_signed_pinned_q7_metadata(
                    token=token, signed_roster=roster, signature=signature,
                    public_key=public_key,
                    independently_trusted_key_sha256=fingerprint,
                )
                if result.get("state") != "q7_release_metadata_exact_under_supplied_key":
                    _deny()
                print("Q7_RELEASE_METADATA=PASS")
                print("NO_ASSETS_NO_INSTALL_NO_ACK")
                return 0
            result = import_signed_pinned_q7_once(
                token=token, signed_roster=roster, signature=signature,
                public_key=public_key,
                independently_trusted_key_sha256=fingerprint,
            )
        finally:
            del token
        if result.get("state") != "q7_signed_bytes_custodied_only":
            _deny()
        print("Q7_PRIVATE_CUSTODY=PASS_SOURCE_BYTES_ONLY")
        print("OPERATOR_SIGNER_AUTHORITY=NOT_ATTESTED")
        print("NO_INSTALL_NO_WORKER_NO_ACK")
        return 0
    except (ValueError, TypeError, OSError, EOFError, KeyboardInterrupt):
        print("Q7_PRIVATE_CUSTODY=WAIT")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
