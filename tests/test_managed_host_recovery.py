"""Offline synthetic acceptance for owner-local intact-stage recovery (#723)."""
from __future__ import annotations

import base64
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
_spec = importlib.util.spec_from_file_location(
    "managed_host_recovery_test_module", scripts / "managed_host_recovery.py",
)
assert _spec is not None and _spec.loader is not None
recovery = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = recovery
_spec.loader.exec_module(recovery)
bootstrap = recovery.bootstrap


def _git(source: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(source), *args],
        capture_output=True, text=True, check=True,
    )
    return p.stdout.strip()


def _row(path: str, raw: bytes) -> list[str]:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode()
    return [path, "sha256=" + encoded, str(len(raw))]


@pytest.fixture
def stage_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    if os.geteuid() == 0:
        pytest.skip("root operator is denied in production")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(recovery.Path, "home", lambda: home)
    monkeypatch.setattr(bootstrap, "host_identity_digest", lambda: "a" * 64)
    source = tmp_path / "trusted"
    source.mkdir()
    _git(source, "init", "-q")
    (source / ".gitignore").write_text(
        "build/\n*.egg-info/\n*.generated\n", encoding="utf-8"
    )
    (source / "install.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    (source / "pyproject.toml").write_text(
        '[project]\nname="aifordable-runner-mcp"\nversion="0.1.30"\n'
    )
    pkg_source = source / "src/runner_mcp"
    pkg_source.mkdir(parents=True)
    (pkg_source / "__init__.py").write_text('__version__ = "0.1.30"\n')
    (pkg_source / "cli.py").write_text("def main():\n    return 0\n")
    _git(source, "add", ".")
    _git(
        source, "-c", "user.email=maintainer@example.invalid",
        "-c", "user.name=Test", "commit", "-qm", "immutable fixture",
    )
    _git(source, "remote", "add", "origin", "https://github.com/Blacksp1d3r/runner-mcp.git")
    sha = _git(source, "rev-parse", "HEAD")
    installer_sha = hashlib.sha256((source / "install.sh").read_bytes()).hexdigest()
    manifest = home / "private-manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": "runner-mcp/local-host-bootstrap/v1",
        "asset_id": "AF-HOST-0000",
        "runner_subject": "runner:example-host",
        "machine_id_sha256": "a" * 64,
        "source_commit": sha,
        "installer_sha256": installer_sha,
    }))
    manifest.chmod(0o600)
    (source / "build").mkdir()
    egg = source / "src/aifordable_runner_mcp.egg-info"
    egg.mkdir()
    (egg / "PKG-INFO").write_text("generated")
    root = home / ".local/share/runner-mcp-bootstrap" / sha
    root.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    venv = root / "runtime/venv"
    bindir = venv / "bin"
    bindir.mkdir(parents=True)
    cli = bindir / "runner-mcp"
    cli.write_text("#!/usr/bin/env python3\nprint('demo')\n")
    cli.chmod(0o700)
    site = venv / "lib/python3.12/site-packages"
    installed = site / "runner_mcp"
    installed.mkdir(parents=True)
    for filename in ("__init__.py", "cli.py"):
        installed.joinpath(filename).write_bytes(pkg_source.joinpath(filename).read_bytes())
    dist = site / "aifordable_runner_mcp-0.1.30.dist-info"
    dist.mkdir()
    metadata = dist / "METADATA"
    metadata.write_text("Name: aifordable-runner-mcp\nVersion: 0.1.30\n")
    (root / "bin").mkdir()
    (root / "bin/runner-mcp").symlink_to(cli)
    record = dist / "RECORD"
    with record.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(_row("runner_mcp/__init__.py", (installed / "__init__.py").read_bytes()))
        writer.writerow(_row("runner_mcp/cli.py", (installed / "cli.py").read_bytes()))
        writer.writerow(_row("aifordable_runner_mcp-0.1.30.dist-info/METADATA", metadata.read_bytes()))
        writer.writerow(_row("../../../bin/runner-mcp", cli.read_bytes()))
        writer.writerow(["aifordable_runner_mcp-0.1.30.dist-info/RECORD", "", ""])
    # Tests mock only non-serving pip / help smokes; real CLI results remain
    # required by the actual recovery operator.
    monkeypatch.setattr(recovery, "_runtime_smoke", lambda _root: None)
    return source, root, manifest, record


def test_recovery_inspects_without_forging_stage_marker(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    result = recovery.inspect_recovery(manifest, source)
    assert result.package_version == "0.1.30"
    assert result.file_count == 2
    assert result.public()["stage_complete"] is False
    assert len(result.digest) == 64
    assert not (root / "stage-result.json").exists()
    assert not (root / "recovery-evidence.json").exists()


def test_explicit_recovery_persists_canonical_marker_but_never_activates(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    digest = recovery.inspect_recovery(manifest, source).digest
    state = recovery.finalize_recovery(manifest, source, accept_digest=digest)
    assert state["stage_complete"] is True
    assert state["service_activation"] is False
    assert state["relay_enrollment"] is False
    assert state["original_client_ack"] is False
    assert (root / "stage-result.json").stat().st_mode & 0o777 == 0o600
    evidence = json.loads((root / "recovery-evidence.json").read_text())
    assert evidence["recovery_sha256"] == digest
    assert evidence["service_activation"] is False
    with pytest.raises(bootstrap.LocalBootstrapError, match="marker_already_present"):
        recovery.finalize_recovery(manifest, source, accept_digest=digest)


def test_wrong_host_cannot_attest_or_write(stage_fixture, monkeypatch) -> None:
    source, root, manifest, _record = stage_fixture
    monkeypatch.setattr(bootstrap, "host_identity_digest", lambda: "b" * 64)
    with pytest.raises(bootstrap.LocalBootstrapError, match="wrong_physical_host"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_record_hash_mismatch_fails_closed(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    cli = root / "runtime/venv/bin/runner-mcp"
    cli.write_text("tampered executable")
    with pytest.raises(bootstrap.LocalBootstrapError, match="recovery_record_content_mismatch"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_package_source_mismatch_even_with_valid_new_record(stage_fixture) -> None:
    source, root, manifest, record = stage_fixture
    py = root / "runtime/venv/lib/python3.12/site-packages/runner_mcp/cli.py"
    py.write_text("malicious edit\n")
    rows = list(csv.reader(io.StringIO(record.read_text())))
    for row in rows:
        if row[0] == "runner_mcp/cli.py":
            row[:] = _row("runner_mcp/cli.py", py.read_bytes())
    with record.open("w", newline="") as out:
        csv.writer(out).writerows(rows)
    with pytest.raises(bootstrap.LocalBootstrapError, match="recovery_installed_source_mismatch"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_unexpected_ignored_source_content_denied(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    (source / "unknown.generated").write_text("unexpected ignored content")
    with pytest.raises(bootstrap.LocalBootstrapError, match="recovery_source_changes_unexpected"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_tracked_installer_tamper_denied(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    (source / "install.sh").write_text("changed\n")
    with pytest.raises(bootstrap.LocalBootstrapError, match="installer_digest_mismatch"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_recovery_rejects_symlinked_installed_package(stage_fixture, tmp_path) -> None:
    source, root, manifest, _record = stage_fixture
    pkg = root / "runtime/venv/lib/python3.12/site-packages/runner_mcp"
    # The test fixture's real directory remains intact under a renamed path,
    # but a symlink in its former location must never be accepted.
    target = tmp_path / "elsewhere"
    pkg.rename(target)
    pkg.symlink_to(target, target_is_directory=True)
    with pytest.raises(bootstrap.LocalBootstrapError, match="symlink_path_denied"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()


def test_invalid_approval_never_creates_receipts(stage_fixture) -> None:
    source, root, manifest, _record = stage_fixture
    with pytest.raises(bootstrap.LocalBootstrapError, match="confirmation_mismatch"):
        recovery.finalize_recovery(manifest, source, accept_digest="f" * 64)
    assert not (root / "recovery-evidence.json").exists()
    assert not (root / "stage-result.json").exists()


def test_recovery_smoke_failure_keeps_stage_blocked(stage_fixture, monkeypatch) -> None:
    source, root, manifest, _record = stage_fixture

    def fail_smoke(_root):
        raise bootstrap.LocalBootstrapError("recovery_runtime_smoke_failed")

    monkeypatch.setattr(recovery, "_runtime_smoke", fail_smoke)
    with pytest.raises(bootstrap.LocalBootstrapError, match="recovery_runtime_smoke_failed"):
        recovery.inspect_recovery(manifest, source)
    assert not (root / "stage-result.json").exists()
