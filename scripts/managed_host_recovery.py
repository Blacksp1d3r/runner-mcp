"""Attest and explicitly finalize one intact non-serving first-host stage.

For a formerly BLOCKED/source_dirty stage only. This never runs install.sh,
git clean, network enrollment, service activation or a second stage.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.util
import io
import json
import marshal
import os
import re
import stat
import subprocess
import sys
import tarfile
import tomllib
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path, PurePosixPath

import managed_host_bootstrap as bootstrap

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_B64 = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_CANDIDATE = "runner-mcp/recovery-attestation/v1"
_EVIDENCE = "runner-mcp/recovered-local-stage/v1"
_EXPECTED_IGNORED = frozenset({
    "!! build/", "!! src/aifordable_runner_mcp.egg-info/",
})
_MAX_ARCHIVE = 48 * 1024 * 1024
_MAX_RECORD = 1024 * 1024


@dataclass(frozen=True, slots=True)
class RecoveryEvidence:
    manifest: bootstrap.HostManifest
    stage: Path
    digest: str
    package_version: str
    source_sha256: str
    record_sha256: str
    file_count: int

    def public(self) -> dict[str, object]:
        return {
            "schema_version": _CANDIDATE,
            "state": "READY_FOR_EXPLICIT_LOCAL_CONFIRMATION",
            "source_commit": self.manifest.source_commit,
            "asset_id": self.manifest.asset_id,
            "runner_subject": self.manifest.runner_subject,
            "package_version": self.package_version,
            "verified_python_files": self.file_count,
            "recovery_sha256": self.digest,
            "stage_complete": False,
            "service_activation": False,
            "relay_enrollment": False,
            "original_client_ack": False,
        }


def _regular(path: Path, *, max_bytes: int | None = None) -> bytes:
    bootstrap._reject_symlink_ancestors(path)
    try:
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o022 or info.st_nlink != 1):
            raise bootstrap.LocalBootstrapError("recovery_file_custody_invalid")
        if max_bytes is not None and info.st_size > max_bytes:
            raise bootstrap.LocalBootstrapError("recovery_file_oversized")
        return path.read_bytes()
    except OSError as exc:
        raise bootstrap.LocalBootstrapError("recovery_file_unavailable") from exc


def _private_directory(path: Path, *, root: bool = False) -> None:
    bootstrap._reject_symlink_ancestors(path)
    try:
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            raise bootstrap.LocalBootstrapError("recovery_directory_custody_invalid")
        if info.st_mode & (0o077 if root else 0o022):
            raise bootstrap.LocalBootstrapError("recovery_directory_custody_invalid")
    except OSError as exc:
        raise bootstrap.LocalBootstrapError("recovery_directory_missing") from exc


def _verify_generated_artifacts(source: Path) -> None:
    """Only the exact known build byproducts from the original failed stage."""
    reported = bootstrap._git(
        source, "status", "--porcelain", "--untracked-files=all",
        "--ignored=matching",
    )
    if frozenset(reported.splitlines()) != _EXPECTED_IGNORED:
        raise bootstrap.LocalBootstrapError("recovery_source_changes_unexpected")
    if bootstrap._git(source, "status", "--porcelain", "--untracked-files=all"):
        raise bootstrap.LocalBootstrapError("recovery_tracked_source_changed")
    count = 0
    for relative in ("build", "src/aifordable_runner_mcp.egg-info"):
        base = source / relative
        _private_directory(base)
        for current, dirs, files in os.walk(base, followlinks=False):
            _private_directory(Path(current))
            for name in dirs + files:
                count += 1
                if count > 20000:
                    raise bootstrap.LocalBootstrapError("recovery_generated_tree_oversized")
                part = Path(current) / name
                bootstrap._reject_symlink_ancestors(part)
                info = part.lstat()
                if (info.st_uid != os.geteuid() or info.st_mode & 0o022
                        or not (stat.S_ISREG(info.st_mode)
                                or stat.S_ISDIR(info.st_mode))):
                    raise bootstrap.LocalBootstrapError("recovery_generated_tree_unsafe")


def _verify_source(source: Path, manifest: bootstrap.HostManifest) -> str:
    """Original source integrity checks, except the TWO observed ignored paths."""
    try:
        bootstrap._verify_source(source, manifest)
    except bootstrap.LocalBootstrapError as exc:
        if str(exc) != "source_dirty":
            raise
        _verify_generated_artifacts(source)
    else:
        # The actual affected stage necessarily left known ignored directories.
        raise bootstrap.LocalBootstrapError("recovery_failure_signature_unmatched")
    project = tomllib.loads(
        _regular(source / "pyproject.toml", max_bytes=128 * 1024).decode("utf-8")
    )
    version = project["project"]["version"]
    if (project["project"]["name"] != "aifordable-runner-mcp"
            or not isinstance(version, str)
            or not re.fullmatch(r"\d+\.\d+\.\d+", version)):
        raise bootstrap.LocalBootstrapError("recovery_source_metadata_invalid")
    return version


def _git_python_archive(source: Path, commit: str) -> tuple[dict[str, bytes], str]:
    """Read pinned Git blob content, never installed/build output."""
    env = {
        "PATH": "/usr/bin:/bin", "HOME": "/", "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
    }
    try:
        proc = subprocess.run(
            ["/usr/bin/git", "-C", str(source), "archive", "--format=tar",
             commit, "src/runner_mcp"],
            env=env, cwd="/", stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=35, check=False,
        )
        if proc.returncode or not 0 < len(proc.stdout) <= _MAX_ARCHIVE:
            raise bootstrap.LocalBootstrapError("recovery_source_archive_invalid")
        tracked: dict[str, bytes] = {}
        with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as archive:
            for member in archive:
                if member.isdir():
                    continue
                name = member.name
                parts = PurePosixPath(name).parts
                if (not member.isfile() or len(parts) < 3
                        or parts[:2] != ("src", "runner_mcp")
                        or not name.endswith(".py")
                        or any(x in ("", ".", "..") for x in parts)):
                    raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
                if member.size < 0 or member.size > 8 * 1024 * 1024:
                    raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
                entry = archive.extractfile(member)
                if entry is None:
                    raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
                with entry:
                    raw = entry.read(member.size + 1)
                if len(raw) != member.size:
                    raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
                relative = "/".join(parts[2:])
                if relative in tracked or len(tracked) >= 2000:
                    raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
                tracked[relative] = raw
        if not tracked or "__init__.py" not in tracked:
            raise bootstrap.LocalBootstrapError("recovery_source_archive_unsafe")
        return tracked, hashlib.sha256(proc.stdout).hexdigest()
    except bootstrap.LocalBootstrapError:
        raise
    except (OSError, subprocess.SubprocessError, tarfile.TarError, ValueError) as exc:
        raise bootstrap.LocalBootstrapError("recovery_source_archive_invalid") from exc



def _verify_pip_compiled_bytecode(path: Path, raw: bytes, pkg: Path,
                                installed: dict[str, Path]) -> None:
    """Accept only actual pip-created unhashed pyc equal to verified source.

    Pip legitimately appends blank-hash RECORD rows for generated pycache.
    Never accept arbitrary unhashed files or executable bytecode.
    """
    if (path.suffix != ".pyc" or path.parent.name != "__pycache__"
            or not path.is_relative_to(pkg)):
        raise bootstrap.LocalBootstrapError("recovery_record_unhashed")
    stem, dot, tag = path.name.partition(".cpython-")
    if not dot or tag != f"{sys.version_info.major}{sys.version_info.minor}.pyc":
        raise bootstrap.LocalBootstrapError("recovery_record_unhashed")
    source = path.parent.parent / f"{stem}.py"
    if source not in installed.values():
        raise bootstrap.LocalBootstrapError("recovery_record_unhashed")
    if (len(raw) < 16 or raw[:4] != importlib.util.MAGIC_NUMBER
            or int.from_bytes(raw[4:8], "little") not in (0, 1, 3)):
        raise bootstrap.LocalBootstrapError("recovery_bytecode_invalid")
    source_bytes = _regular(source, max_bytes=8 * 1024 * 1024)
    if (int.from_bytes(raw[4:8], "little") == 0
            and int.from_bytes(raw[12:16], "little") != len(source_bytes)):
        raise bootstrap.LocalBootstrapError("recovery_bytecode_invalid")
    expected = marshal.dumps(compile(source_bytes, str(source), "exec", dont_inherit=True))
    if raw[16:] != expected:
        raise bootstrap.LocalBootstrapError("recovery_bytecode_content_mismatch")


def _verify_installed_package(
    stage: Path, source: Path, manifest: bootstrap.HostManifest, version: str,
) -> tuple[str, str, int]:
    venv = stage / "runtime/venv"
    site = venv / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    pkg = site / "runner_mcp"
    dist = site / f"aifordable_runner_mcp-{version}.dist-info"
    for directory in (stage / "runtime", venv, site, pkg, dist, stage / "bin"):
        _private_directory(directory)
    if stage.joinpath("stage-result.json").exists() or (
        stage / "stage-result.json"
    ).is_symlink():
        raise bootstrap.LocalBootstrapError("recovery_marker_already_present")
    if (stage / "recovery-evidence.json").exists() or (
        stage / "recovery-evidence.json"
    ).is_symlink():
        raise bootstrap.LocalBootstrapError("recovery_previously_attempted")
    python = venv / "bin/python"
    bootstrap._reject_symlink_ancestors(python.parent)
    try:
        if (not python.is_symlink() or
                python.resolve(strict=True) != Path("/usr/bin/python3").resolve(strict=True)):
            raise bootstrap.LocalBootstrapError("recovery_python_interpreter_untrusted")
    except OSError as exc:
        raise bootstrap.LocalBootstrapError("recovery_python_interpreter_unavailable") from exc
    cli = venv / "bin/runner-mcp"
    _regular(cli, max_bytes=1024 * 1024)
    if not os.access(cli, os.X_OK):
        raise bootstrap.LocalBootstrapError("recovery_cli_not_executable")
    launcher = stage / "bin/runner-mcp"
    bootstrap._reject_symlink_ancestors(launcher.parent)
    if not launcher.is_symlink() or launcher.resolve(strict=True) != cli:
        raise bootstrap.LocalBootstrapError("recovery_launcher_mismatch")
    dist_list = tuple(site.glob("aifordable_runner_mcp-*.dist-info"))
    if len(dist_list) != 1 or dist_list[0] != dist:
        raise bootstrap.LocalBootstrapError("recovery_distribution_ambiguous")
    metadata = Parser().parsestr(
        _regular(dist / "METADATA", max_bytes=1024 * 1024).decode("utf-8")
    )
    if metadata.get("Name", "").lower() != "aifordable-runner-mcp" or (
        metadata.get("Version") != version
    ):
        raise bootstrap.LocalBootstrapError("recovery_distribution_mismatch")
    tracked, source_digest = _git_python_archive(source, manifest.source_commit)
    installed = {}
    for path in pkg.rglob("*.py"):
        _regular(path, max_bytes=8 * 1024 * 1024)
        relative = path.relative_to(pkg).as_posix()
        if relative in installed:
            raise bootstrap.LocalBootstrapError("recovery_package_duplicate")
        installed[relative] = path
    if frozenset(installed) != frozenset(tracked):
        raise bootstrap.LocalBootstrapError("recovery_package_file_set_mismatch")
    for relative, expected in tracked.items():
        if _regular(installed[relative], max_bytes=8 * 1024 * 1024) != expected:
            raise bootstrap.LocalBootstrapError("recovery_installed_source_mismatch")

    record = _regular(dist / "RECORD", max_bytes=_MAX_RECORD)
    try:
        rows = list(csv.reader(io.StringIO(record.decode("utf-8"))))
    except (UnicodeError, csv.Error) as exc:
        raise bootstrap.LocalBootstrapError("recovery_record_invalid") from exc
    seen = set()
    attested_paths: set[Path] = set()
    unhashed = 0
    for row in rows:
        if len(row) != 3 or not row[0] or row[0] in seen:
            raise bootstrap.LocalBootstrapError("recovery_record_invalid")
        seen.add(row[0])
        # pip RECORD entries may refer to venv/bin via ../ paths.
        declared = site / row[0]
        bootstrap._reject_symlink_ancestors(declared)
        target = declared.resolve(strict=True)
        if not target.is_relative_to(venv):
            raise bootstrap.LocalBootstrapError("recovery_record_escapes_venv")
        raw = _regular(target, max_bytes=32 * 1024 * 1024)
        attested_paths.add(target)
        if row[1] == "":
            if row[2]:
                raise bootstrap.LocalBootstrapError("recovery_record_unhashed")
            if target == dist / "RECORD":
                unhashed += 1
            else:
                _verify_pip_compiled_bytecode(target, raw, pkg, installed)
            continue
        scheme, sep, encoded = row[1].partition("=")
        if scheme != "sha256" or not sep or not _B64.fullmatch(encoded):
            raise bootstrap.LocalBootstrapError("recovery_record_hash_invalid")
        expected_digest = base64.urlsafe_b64decode(encoded + "=")
        if hashlib.sha256(raw).digest() != expected_digest or (
            row[2] != str(len(raw))
        ):
            raise bootstrap.LocalBootstrapError("recovery_record_content_mismatch")
    if (unhashed != 1 or len(rows) < len(tracked) + 2
            or not set(installed.values()).issubset(attested_paths)
            or cli not in attested_paths or
            any(p not in attested_paths for p in pkg.rglob("*.pyc"))):
        raise bootstrap.LocalBootstrapError("recovery_record_incomplete")
    return source_digest, hashlib.sha256(record).hexdigest(), len(tracked)


def _runtime_smoke(stage: Path) -> None:
    venv = stage / "runtime/venv"
    env = {
        "PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
        "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INPUT": "1",
        "PIP_NO_CACHE_DIR": "1",
    }
    for args in (
        [str(venv / "bin/python"), "-B", "-m", "pip", "check"],
        [str(venv / "bin/runner-mcp"), "--help"],
    ):
        try:
            result = subprocess.run(
                args, cwd="/", env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=40, check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise bootstrap.LocalBootstrapError("recovery_runtime_unavailable") from exc
        if result.returncode:
            raise bootstrap.LocalBootstrapError("recovery_runtime_smoke_failed")



def _original_plan_sha256(manifest: bootstrap.HostManifest) -> str:
    canonical = {
        "schema_version": bootstrap._SCHEMA,
        "asset_id": manifest.asset_id,
        "runner_subject": manifest.runner_subject,
        "machine_id_sha256": manifest.machine_id_sha256,
        "source_commit": manifest.source_commit,
        "installer_sha256": manifest.installer_sha256,
        "stage_only": True,
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inspect_recovery(
    manifest_path: Path, source: Path, *, original_plan: str,
) -> RecoveryEvidence:
    if os.geteuid() == 0 or sys.platform != "linux" or sys.version_info < (3, 12):
        raise bootstrap.LocalBootstrapError("recovery_operator_unsupported")
    manifest = bootstrap.HostManifest.load(manifest_path)
    if type(original_plan) is not str or _SHA.fullmatch(original_plan) is None:
        raise bootstrap.LocalBootstrapError("recovery_original_plan_required")
    if _original_plan_sha256(manifest) != original_plan:
        raise bootstrap.LocalBootstrapError("recovery_original_plan_mismatch")
    if bootstrap.host_identity_digest() != manifest.machine_id_sha256:
        raise bootstrap.LocalBootstrapError("wrong_physical_host")
    version = _verify_source(source, manifest)
    stage = Path.home() / ".local/share/runner-mcp-bootstrap" / manifest.source_commit
    _private_directory(stage, root=True)
    source_digest, record_digest, file_count = _verify_installed_package(
        stage, source, manifest, version,
    )
    _runtime_smoke(stage)
    # All caller/environment/installed payload predicates are checked again
    # after any non-serving package code was executed.
    if bootstrap.host_identity_digest() != manifest.machine_id_sha256:
        raise bootstrap.LocalBootstrapError("host_identity_changed")
    if bootstrap.HostManifest.load(manifest_path) != manifest:
        raise bootstrap.LocalBootstrapError("manifest_changed_during_recovery")
    if _verify_source(source, manifest) != version:
        raise bootstrap.LocalBootstrapError("recovery_source_changed")
    renewed = _verify_installed_package(stage, source, manifest, version)
    if renewed != (source_digest, record_digest, file_count):
        raise bootstrap.LocalBootstrapError("recovery_installed_payload_changed")
    canonical = {
        "schema_version": _CANDIDATE,
        "source_commit": manifest.source_commit,
        "machine_id_sha256": manifest.machine_id_sha256,
        "asset_id": manifest.asset_id,
        "runner_subject": manifest.runner_subject,
        "installer_sha256": manifest.installer_sha256,
        "package_version": version,
        "source_archive_sha256": source_digest,
        "record_sha256": record_digest,
        "verified_python_files": file_count,
        "stage_dev": stage.lstat().st_dev,
        "stage_inode": stage.lstat().st_ino,
        "stage_only": True,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return RecoveryEvidence(
        manifest, stage, digest, version, source_digest, record_digest, file_count,
    )


def finalize_recovery(
    manifest_path: Path, source: Path, *, original_plan: str, accept_digest: str,
) -> dict[str, object]:
    if type(accept_digest) is not str or _SHA.fullmatch(accept_digest) is None:
        raise bootstrap.LocalBootstrapError("recovery_explicit_confirmation_required")
    first = inspect_recovery(manifest_path, source, original_plan=original_plan)
    if first.digest != accept_digest:
        raise bootstrap.LocalBootstrapError("recovery_confirmation_mismatch")
    # Revalidate the entire trust chain immediately before opening receipts.
    latest = inspect_recovery(manifest_path, source, original_plan=original_plan)
    if latest.digest != first.digest:
        raise bootstrap.LocalBootstrapError("recovery_attestation_changed")
    receipt = {
        "schema_version": _EVIDENCE,
        "source_commit": latest.manifest.source_commit,
        "asset_id": latest.manifest.asset_id,
        "runner_subject": latest.manifest.runner_subject,
        "package_version": latest.package_version,
        "recovery_sha256": latest.digest,
        "verified_python_files": latest.file_count,
        "source_archive_sha256": latest.source_sha256,
        "record_sha256": latest.record_sha256,
        "service_activation": False,
        "relay_enrollment": False,
        "original_client_ack": False,
    }
    state = {
        "schema_version": "runner-mcp/local-host-stage-result/v1",
        "plan_sha256": original_plan,
        "source_commit": latest.manifest.source_commit,
        "asset_id": latest.manifest.asset_id,
        "runner_subject": latest.manifest.runner_subject,
        "stage_complete": True,
        "service_activation": False,
        "relay_enrollment": False,
        "original_client_ack": False,
    }
    for name, payload in (
        ("recovery-evidence.json", receipt), ("stage-result.json", state),
    ):
        dest = latest.stage / name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(dest, flags, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(json.dumps(payload, sort_keys=True).encode() + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            # Retain any partial receipt for forensic, never fake completion.
            raise bootstrap.LocalBootstrapError("recovery_receipt_write_failed") from exc
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    for action in ("inspect", "finalize"):
        command = subs.add_parser(action)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--original-plan", required=True)
        if action == "finalize":
            command.add_argument("--accept-recovery", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "inspect":
            result = inspect_recovery(
                args.manifest, args.source, original_plan=args.original_plan,
            ).public()
        else:
            result = finalize_recovery(
                args.manifest, args.source, original_plan=args.original_plan,
                accept_digest=args.accept_recovery,
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    except bootstrap.LocalBootstrapError as exc:
        print(json.dumps({"state": "BLOCKED", "reason_code": str(exc)}), file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RuntimeError):
        print(json.dumps({"state": "BLOCKED", "reason_code": "recovery_inspection_unavailable"}),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
