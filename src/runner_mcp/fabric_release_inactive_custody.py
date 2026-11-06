"""Inactieve owner-private opslag voor een VOLLEDIG gecontroleerde Fabric Release.

Dit is uitsluitend een niet-geëxporteerde bronbouwsteen voor #937. De eigenaar
moet de echte signer-key, commit, release-ID, doelhost en opslagroot onafhankelijk
autoriseren; door de aanroeper opgegeven testpins zijn GEEN productiebevoegdheid.
Gebruik het bestaande Q7-no-replace en de bestaande lokale Fabric-update-root.
Geen netwerk, tokens, install, launcher, service, rollback of worker-mutatie.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import stat
from pathlib import Path
from uuid import uuid4

from .fabric_release_assets import ReleaseAdmission
from .fabric_release_private_custody import _private_root_fd
from .fabric_release_signed_roster import (
    compare_signed_fabric_roster,
    verify_signed_fabric_roster,
)
from .fabric_release_wheelhouse import verify_signed_fabric_wheelhouse
from .fabric_update import FabricUpdateError, _promote_inactive_bundle_noreplace

_MAX_BYTES = 256 * 1024 * 1024
_MAX_FILE = 64 * 1024 * 1024
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,150}\Z")


class InactiveSignedCustodyUnqualified(ValueError):
    """Veilige vaste foutcode zonder hostpaden, secrets of bytes."""


def _deny() -> None:
    raise InactiveSignedCustodyUnqualified("fabric_signed_inactive_custody_unqualified")


def _absent(root_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    return False


def _write_and_check(stage_fd: int, name: str, raw: bytes) -> None:
    """Maak precies één bestand aan, fsync en verifieer de teruggelezen bytes."""
    fd = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600, dir_fd=stage_fd,
    )
    try:
        os.fchmod(fd, 0o600)
        data = memoryview(raw)
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:offset + 65536])
            if written <= 0:
                _deny()
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)

    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=stage_fd)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_size != len(raw)
        ):
            _deny()
        digest = hashlib.sha256()
        total = 0
        while total < len(raw):
            block = os.read(fd, min(65536, len(raw) - total))
            if not block:
                _deny()
            total += len(block)
            digest.update(block)
        if not hmac.compare_digest(digest.digest(), hashlib.sha256(raw).digest()):
            _deny()
    finally:
        os.close(fd)


def _stage_signed_release_inactive_once(
    *,
    local_bundles_root: Path,
    signed_document: bytes,
    signature: bytes,
    public_key: bytes,
    independently_trusted_key_sha256: str,
    expected_commit: str,
    expected_release_id: int,
    observed_metadata: ReleaseAdmission,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Bewaar een volledig opnieuw geverifieerde offline bundel zonder activatie.

    Alleen de al geconfigureerde FabricUpdateManager.local_bundles_root mag de
    root leveren. Deze private functie is niet aan een MCP-tool of de runtime
    gekoppeld. Echte operator-/publisherbevoegdheid wordt hier NIET verstrekt.
    """
    try:
        pins = verify_signed_fabric_roster(
            signed_document=signed_document,
            signature=signature,
            public_key=public_key,
            independently_trusted_key_sha256=independently_trusted_key_sha256,
            expected_commit=expected_commit,
            expected_release_id=expected_release_id,
        )
        compare_signed_fabric_roster(pins, observed_metadata)
        if (
            type(asset_bodies) is not dict
            or set(asset_bodies) != {item.name for item in pins.files}
            or not 5 <= len(asset_bodies) <= 160
        ):
            _deny()
        total = 0
        for item in pins.files:
            raw = asset_bodies[item.name]
            if (
                _SAFE_NAME.fullmatch(item.name) is None
                or type(raw) is not bytes
                or not 0 < len(raw) <= _MAX_FILE
                or len(raw) != item.bytes
                or not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), item.sha256)
            ):
                _deny()
            total += len(raw)
            if total > _MAX_BYTES:
                _deny()
        verify_signed_fabric_wheelhouse(pins, observed_metadata, asset_bodies)
    except (ValueError, TypeError):
        _deny()

    if not isinstance(local_bundles_root, Path):
        _deny()
    root_fd = -1
    work_fd = -1
    source_fd = -1
    bundle_fd = -1
    incoming = ".incoming-" + uuid4().hex
    try:
        # Er wordt NOOIT een willekeurige root aangemaakt. Root 0700 moet
        # vooraf bestaan; _private_root_fd weigert symlinks en vreemde owner.
        root_fd = _private_root_fd(local_bundles_root)
        if not _absent(root_fd, expected_commit):
            _deny()
        os.mkdir(incoming, 0o700, dir_fd=root_fd)
        os.fsync(root_fd)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        work_fd = os.open(incoming, flags, dir_fd=root_fd)
        os.fchmod(work_fd, 0o700)
        os.mkdir("source", 0o700, dir_fd=work_fd)
        source_fd = os.open("source", flags, dir_fd=work_fd)
        os.fchmod(source_fd, 0o700)
        os.mkdir("bundle", 0o700, dir_fd=source_fd)
        bundle_fd = os.open("bundle", flags, dir_fd=source_fd)
        os.fchmod(bundle_fd, 0o700)
        for name in sorted(asset_bodies):
            _write_and_check(bundle_fd, name, asset_bodies[name])
        os.fsync(bundle_fd)
        os.fsync(source_fd)
        os.fsync(work_fd)
        # De atomische promotie hergebruikt de al bestaande, geteste
        # renameat2(RENAME_NOREPLACE); nooit een andere versie overschrijven.
        _promote_inactive_bundle_noreplace(
            local_bundles_root, incoming, expected_commit
        )
        os.fsync(root_fd)
    except (OSError, ValueError, FabricUpdateError):
        # Onvolledige .incoming blijft bewust staan voor forensisch onderzoek;
        # geen automatische delete/retry en geen gedeeltelijk 'ready'-bewijs.
        _deny()
    finally:
        for fd in (bundle_fd, source_fd, work_fd, root_fd):
            if fd >= 0:
                os.close(fd)

    return {
        "commit": expected_commit,
        "source": "signed-release-offline-test",
        "inactive_custody": True,
        "asset_count": len(asset_bodies),
        "install_authorized": False,
        "owner_authority_proven": False,
        "rollback_verified": False,
        "original_client_ack": False,
    }
