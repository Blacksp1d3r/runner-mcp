"""Operator-attended, non-serving Runner-MCP first-host stage.

This local-only script is NOT an MCP tool, a host enrollment credential or
remote execution authority. It deliberately cannot activate a service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

_SCHEMA = "runner-mcp/local-host-bootstrap/v1"
_MANIFEST_FIELDS = frozenset({
    "schema_version", "asset_id", "runner_subject", "machine_id_sha256",
    "source_commit", "installer_sha256",
})
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_ASSET = re.compile(r"AF-HOST-[0-9]{4}\Z")
_SUBJECT = re.compile(r"runner:[a-z0-9][a-z0-9._:-]{0,119}\Z")
_ORIGINS = frozenset({
    "https://github.com/Blacksp1d3r/runner-mcp.git",
    "git@github.com:Blacksp1d3r/runner-mcp.git",
})
_STAGE_SCHEMA = "runner-mcp/local-host-stage-result/v1"


class LocalBootstrapError(RuntimeError):
    """A categorical local-only preflight or stage refusal."""


@dataclass(frozen=True, slots=True)
class HostManifest:
    asset_id: str
    runner_subject: str
    machine_id_sha256: str
    source_commit: str
    installer_sha256: str

    @classmethod
    def load(cls, path: Path) -> HostManifest:
        if not isinstance(path, Path) or not path.is_absolute():
            raise LocalBootstrapError("manifest_path_invalid")
        _reject_symlink_ancestors(path)
        try:
            metadata = path.lstat()
            if (not stat.S_ISREG(metadata.st_mode) or
                    metadata.st_uid != os.geteuid() or
                    metadata.st_mode & 0o077 or
                    not 0 < metadata.st_size <= 4096):
                raise LocalBootstrapError("manifest_custody_invalid")
            raw = path.read_bytes()
            if len(raw) > 4096:
                raise LocalBootstrapError("manifest_custody_invalid")
            value = json.loads(raw)
        except (OSError, ValueError, UnicodeError) as exc:
            raise LocalBootstrapError("manifest_unavailable_or_invalid") from exc
        if not isinstance(value, dict) or frozenset(value) != _MANIFEST_FIELDS:
            raise LocalBootstrapError("manifest_shape_invalid")
        if value["schema_version"] != _SCHEMA:
            raise LocalBootstrapError("manifest_schema_invalid")
        for key, expression in (
            ("asset_id", _ASSET), ("runner_subject", _SUBJECT),
            ("machine_id_sha256", _HEX64), ("source_commit", _HEX40),
            ("installer_sha256", _HEX64),
        ):
            if type(value[key]) is not str or expression.fullmatch(value[key]) is None:
                raise LocalBootstrapError("manifest_field_invalid")
        return cls(**{key: value[key] for key in _MANIFEST_FIELDS if key != "schema_version"})


@dataclass(frozen=True, slots=True)
class LocalStagePlan:
    digest: str
    source_commit: str
    runner_subject: str
    asset_id: str
    stage_root: Path

    def public_dict(self) -> dict[str, str | bool]:
        return {
            "schema_version": "runner-mcp/local-host-stage-plan/v1",
            "asset_id": self.asset_id,
            "runner_subject": self.runner_subject,
            "source_commit": self.source_commit,
            "plan_sha256": self.digest,
            "stage_only": True,
            "service_activation": False,
            "relay_enrollment": False,
            "original_client_ack": False,
        }


def _reject_symlink_ancestors(path: Path) -> None:
    if not path.is_absolute():
        raise LocalBootstrapError("path_not_absolute")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise LocalBootstrapError("symlink_path_denied")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def host_identity_digest(*, machine_id_file: Path = Path("/etc/machine-id")) -> str:
    """A LOCAL fingerprint, never upload or treat as independent attestation."""
    try:
        raw = machine_id_file.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise LocalBootstrapError("machine_identity_unavailable") from exc
    if re.fullmatch(r"[0-9a-f]{32}", raw) is None or raw == "0" * 32:
        raise LocalBootstrapError("machine_identity_invalid")
    return _sha256(raw.encode("ascii"))


def _git(source: Path, *args: str) -> str:
    env = {
        "PATH": "/usr/bin:/bin", "HOME": "/",
        "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    try:
        proc = subprocess.run(
            ["/usr/bin/git", "-C", str(source), *args],
            env=env, cwd="/", stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalBootstrapError("source_git_unavailable") from exc
    if proc.returncode != 0 or len(proc.stdout) > 8192:
        raise LocalBootstrapError("source_git_invalid")
    return proc.stdout.strip()


def _verify_source(source_root: Path, manifest: HostManifest) -> None:
    if not source_root.is_absolute():
        raise LocalBootstrapError("source_path_invalid")
    _reject_symlink_ancestors(source_root)
    try:
        source = source_root.resolve(strict=True)
        if not source.is_dir():
            raise LocalBootstrapError("source_path_invalid")
        installer = source / "install.sh"
        _reject_symlink_ancestors(installer)
        raw = installer.read_bytes()
    except OSError as exc:
        raise LocalBootstrapError("installer_unavailable") from exc
    if not 0 < len(raw) <= 64 * 1024 or _sha256(raw) != manifest.installer_sha256:
        raise LocalBootstrapError("installer_digest_mismatch")
    if _git(source, "rev-parse", "--show-toplevel") != str(source):
        raise LocalBootstrapError("source_checkout_mismatch")
    if _git(source, "rev-parse", "--verify", "HEAD") != manifest.source_commit:
        raise LocalBootstrapError("source_revision_mismatch")
    if _git(source, "remote", "get-url", "origin") not in _ORIGINS:
        raise LocalBootstrapError("source_origin_unapproved")
    if _git(source, "status", "--porcelain", "--untracked-files=all", "--ignored=matching"):
        raise LocalBootstrapError("source_dirty")


def plan_local_stage(
    manifest_path: Path, source_root: Path, *,
    home: Path | None = None, machine_digest: str | None = None,
) -> LocalStagePlan:
    if sys.version_info < (3, 12) or sys.platform != "linux":
        raise LocalBootstrapError("runtime_unsupported")
    if os.geteuid() == 0:
        raise LocalBootstrapError("root_operator_denied")
    manifest = HostManifest.load(manifest_path)
    observed = machine_digest if machine_digest is not None else host_identity_digest()
    if observed != manifest.machine_id_sha256:
        raise LocalBootstrapError("wrong_physical_host")
    _verify_source(source_root, manifest)
    local_home = Path.home() if home is None else home
    if not local_home.is_absolute():
        raise LocalBootstrapError("home_invalid")
    stage_root = (
        local_home / ".local" / "share" / "runner-mcp-bootstrap" /
        manifest.source_commit
    )
    _reject_symlink_ancestors(stage_root)
    if stage_root.exists() or stage_root.is_symlink():
        raise LocalBootstrapError("stage_already_present")
    canonical = {
        "schema_version": _SCHEMA, "asset_id": manifest.asset_id,
        "runner_subject": manifest.runner_subject,
        "machine_id_sha256": manifest.machine_id_sha256,
        "source_commit": manifest.source_commit,
        "installer_sha256": manifest.installer_sha256,
        "stage_only": True,
    }
    digest = _sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode())
    return LocalStagePlan(
        digest=digest, source_commit=manifest.source_commit,
        runner_subject=manifest.runner_subject, asset_id=manifest.asset_id,
        stage_root=stage_root,
    )


def stage_local_runner_mcp(
    manifest_path: Path, source_root: Path, *, accept_digest: str,
    home: Path | None = None, machine_digest: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> dict[str, object]:
    """Stage via the EXISTING installer; no service or control-plane activation."""
    if type(accept_digest) is not str or _HEX64.fullmatch(accept_digest) is None:
        raise LocalBootstrapError("explicit_plan_confirmation_required")
    plan = plan_local_stage(
        manifest_path, source_root, home=home, machine_digest=machine_digest,
    )
    initial_manifest = HostManifest.load(manifest_path)
    if plan.digest != accept_digest:
        raise LocalBootstrapError("plan_confirmation_mismatch")

    stage_root = plan.stage_root
    parent = stage_root.parent
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _reject_symlink_ancestors(parent)
    if parent.stat().st_uid != os.geteuid() or parent.stat().st_mode & 0o077:
        raise LocalBootstrapError("stage_parent_custody_invalid")
    try:
        stage_root.mkdir(mode=0o700)
        (stage_root / "bin").mkdir(mode=0o700)
    except FileExistsError as exc:
        raise LocalBootstrapError("stage_already_present") from exc
    except OSError as exc:
        raise LocalBootstrapError("stage_creation_failed") from exc

    # Nothing from the caller's environment can redirect installer/runtime
    # paths, Python imports, Git credential helpers, or shell startup.
    environment = {
        "PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
        "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
        "RUNNER_MCP_INSTALL_ROOT": str(stage_root / "runtime"),
        "RUNNER_MCP_BIN_DIR": str(stage_root / "bin"),
        "RUNNER_MCP_PYTHON": "/usr/bin/python3",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "PIP_NO_CACHE_DIR": "1",
    }
    try:
        result = runner(
            ["/usr/bin/bash", str(source_root / "install.sh")],
            cwd=str(source_root), env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=1300, check=False,
        )
        if result.returncode != 0:
            raise LocalBootstrapError("existing_installer_failed")
        executable = stage_root / "runtime" / "venv" / "bin" / "runner-mcp"
        launcher = stage_root / "bin" / "runner-mcp"
        python = stage_root / "runtime" / "venv" / "bin" / "python"
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise LocalBootstrapError("stage_executable_missing")
        if not launcher.is_symlink() or launcher.resolve(strict=True) != executable:
            raise LocalBootstrapError("stage_launcher_mismatch")
        for args in ([str(python), "-m", "pip", "check"], [str(executable), "--help"]):
            checked = runner(
                args, cwd="/", env=environment, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=40, check=False,
            )
            if checked.returncode != 0:
                raise LocalBootstrapError("stage_runtime_check_failed")
        # This is a second TOCTOU fence. The source can never be promoted
        # after any observed checkout mutation during staging.
        current_manifest = HostManifest.load(manifest_path)
        if current_manifest != initial_manifest:
            raise LocalBootstrapError("manifest_changed_during_stage")
        _verify_source(source_root, current_manifest)
        if (machine_digest if machine_digest is not None else host_identity_digest()) != (
            current_manifest.machine_id_sha256
        ):
            raise LocalBootstrapError("host_identity_changed")
        state = {
            "schema_version": _STAGE_SCHEMA, "plan_sha256": plan.digest,
            "source_commit": plan.source_commit,
            "asset_id": plan.asset_id, "runner_subject": plan.runner_subject,
            "stage_complete": True, "service_activation": False,
            "relay_enrollment": False, "original_client_ack": False,
        }
        marker = stage_root / "stage-result.json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(marker, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(json.dumps(state, sort_keys=True).encode() + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            marker.unlink(missing_ok=True)
            raise
        return state
    except LocalBootstrapError:
        # Do not remove or retry an incomplete stage; retain it for diagnosis.
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalBootstrapError("stage_execution_unavailable") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operator-local, non-serving Runner-MCP stage")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("identity", help="Display LOCAL machine identity SHA-256 only")
    for name in ("plan", "stage"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--source", type=Path, required=True)
        if name == "stage":
            command.add_argument("--accept-plan", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "identity":
            print(json.dumps({"machine_id_sha256": host_identity_digest()}))
        elif args.action == "plan":
            plan = plan_local_stage(args.manifest, args.source)
            print(json.dumps(plan.public_dict(), sort_keys=True))
        else:
            state = stage_local_runner_mcp(
                args.manifest, args.source, accept_digest=args.accept_plan
            )
            print(json.dumps(state, sort_keys=True))
        return 0
    except LocalBootstrapError as exc:
        print(json.dumps({"state": "BLOCKED", "reason_code": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
