"""Build exactly one source-only Q7 first-host Python zipapp (no host actions).

Only auditable pinned package modules are included. Build step never downloads,
adds GitHub credentials, installs Python packages, changes services or signs a
publisher key. The resulting zipapp requires independently verified custody
and public-key authorization before owner-local use on the Black machine.
"""
from __future__ import annotations

import hashlib
import os
import sys
import zipfile
from pathlib import Path

_FILES = (
    "runner_mcp/__init__.py",
    "runner_mcp/fabric_release_asset_bytes.py",
    "runner_mcp/fabric_release_assets.py",
    "runner_mcp/fabric_release_independent_roster.py",
    "runner_mcp/fabric_release_full_bundle.py",
    "runner_mcp/fabric_release_wheelhouse.py",
    "runner_mcp/fabric_release_private_custody.py",
    "runner_mcp/fabric_release_signed_import.py",
    "runner_mcp/fabric_q7_fixed_root_prepare.py",
    "runner_mcp/fabric_q7_lab_session_auth.py",
)
_FIXED_TIME = (2020, 1, 1, 0, 0, 0)


class ZipappBuildRefused(ValueError):
    """Fail closed; a build artifact is not an admitted release."""


def build_q7_first_host_zipapp(*, source_root: Path, destination: Path) -> str:
    """Tests may supply isolated inputs; production CLI uses fixed repo layout."""
    if (
        not isinstance(source_root, Path)
        or not isinstance(destination, Path)
        or not source_root.is_absolute()
        or not destination.is_absolute()
    ):
        raise ZipappBuildRefused("zipapp_build_unqualified")
    files = [(source_root / "scripts/fabric_q7_first_host_main.py", "__main__.py")]
    files += [(source_root / "src" / name, name) for name in _FILES]
    for file, name in files:
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(source_root):
            raise ZipappBuildRefused("zipapp_source_unqualified")
        if len(file.read_bytes()) > 128 * 1024:
            raise ZipappBuildRefused("zipapp_source_oversized")
    if destination.exists() or destination.is_symlink():
        raise ZipappBuildRefused("zipapp_destination_exists")
    if not destination.parent.is_dir():
        raise ZipappBuildRefused("zipapp_parent_missing")

    # Exclusive creation, deterministic ZIP bytes, no mutable source or extra
    # dependency: cryptography is an independently qualified host dependency.
    try:
        handle = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(handle, "wb") as target:
                with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as package:
                    for file, name in files:
                        record = zipfile.ZipInfo(name, _FIXED_TIME)
                        record.compress_type = zipfile.ZIP_STORED
                        record.create_system = 3
                        record.external_attr = 0o600 << 16
                        package.writestr(record, file.read_bytes())
                target.flush()
                os.fsync(target.fileno())
        except Exception as exc:
            # Preserve any partial output as a fail-closed forensic receipt.
            raise ZipappBuildRefused("zipapp_build_unqualified") from exc
    except OSError as exc:
        raise ZipappBuildRefused("zipapp_build_unqualified") from exc
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def main() -> int:
    if sys.argv[1:] not in ([], ["build"]):
        print("WAIT_ARGUMENTS_UNSUPPORTED")
        return 1
    root = Path(__file__).resolve().parent.parent
    output = root / "dist/fabric-q7-first-host-import.pyz"
    try:
        digest = build_q7_first_host_zipapp(source_root=root, destination=output)
    except (OSError, ValueError):
        print("Q7_FIRST_HOST_ZIPAPP=WAIT")
        return 1
    print("Q7_FIRST_HOST_ZIPAPP=BUILT_SOURCE_ONLY")
    print("ZIPAPP_SHA256=" + digest)
    print("NO_SIGNER_AUTHORIZATION_NO_INSTALL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
