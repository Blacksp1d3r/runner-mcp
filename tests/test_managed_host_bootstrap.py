from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# scripts/ is not an installed Python package in wheel-based CI.
_spec = importlib.util.spec_from_file_location(
    "managed_host_bootstrap_test_module",
    Path(__file__).resolve().parents[1] / "scripts" / "managed_host_bootstrap.py",
)
assert _spec is not None and _spec.loader is not None
bootstrap = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bootstrap
_spec.loader.exec_module(bootstrap)


def _git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args], check=True,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def source(tmp_path: Path) -> tuple[Path, str, str]:
    root = tmp_path / "trusted-source"
    root.mkdir()
    _git(root, "init", "-q")
    installer = root / "install.sh"
    installer.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname='aifordable-runner-mcp'\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "-c", "user.email=test@example.invalid", "-c", "user.name=Test", "commit", "-qm", "snapshot")
    _git(root, "remote", "add", "origin", "https://github.com/Blacksp1d3r/runner-mcp.git")
    return (
        root, _git(root, "rev-parse", "HEAD"),
        hashlib.sha256(installer.read_bytes()).hexdigest(),
    )


@pytest.fixture
def manifest(tmp_path: Path, source: tuple[Path, str, str]) -> Path:
    _, commit, installer_digest = source
    target = tmp_path / "private-manifest.json"
    target.write_text(
        json.dumps({
            "schema_version": "runner-mcp/local-host-bootstrap/v1",
            "asset_id": "AF-HOST-0000",
            "runner_subject": "runner:example-host",
            "machine_id_sha256": "a" * 64,
            "source_commit": commit,
            "installer_sha256": installer_digest,
        }),
        encoding="utf-8",
    )
    target.chmod(0o600)
    return target


def _plan(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
    *,
    digest: str = "a" * 64,
) -> bootstrap.LocalStagePlan:
    return bootstrap.plan_local_stage(
        manifest, source[0], home=tmp_path / "home", machine_digest=digest,
    )


def test_local_plan_does_not_create_any_file(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    result = _plan(manifest, source, tmp_path)
    assert len(result.digest) == 64
    assert result.source_commit == source[1]
    assert result.asset_id == "AF-HOST-0000"
    assert not home.exists()
    assert result.public_dict()["service_activation"] is False
    assert result.public_dict()["original_client_ack"] is False


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("asset_id", "AF-HOST-xyz", "manifest_field_invalid"),
    ("runner_subject", "runner:../../wrong", "manifest_field_invalid"),
    ("source_commit", "A" * 40, "manifest_field_invalid"),
    ("installer_sha256", "a" * 63, "manifest_field_invalid"),
    ("machine_id_sha256", "A" * 64, "manifest_field_invalid"),
])
def test_rejects_malformed_private_authority_manifest(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
    field: str, value: str, reason: str,
) -> None:
    raw = json.loads(manifest.read_text())
    raw[field] = value
    manifest.write_text(json.dumps(raw))
    with pytest.raises(bootstrap.LocalBootstrapError, match=reason):
        _plan(manifest, source, tmp_path)


def test_wrong_host_rejected_before_any_stage(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    with pytest.raises(bootstrap.LocalBootstrapError, match="wrong_physical_host"):
        _plan(manifest, source, tmp_path, digest="b" * 64)
    assert not (tmp_path / "home").exists()


def test_source_tampering_and_dirty_checkout_fail_closed(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    source[0].joinpath("install.sh").write_text("#!/bin/sh\nexit 1\n")
    with pytest.raises(bootstrap.LocalBootstrapError, match="installer_digest_mismatch"):
        _plan(manifest, source, tmp_path)
    _git(source[0], "checkout", "--", "install.sh")
    source[0].joinpath("injected").write_text("untracked")
    with pytest.raises(bootstrap.LocalBootstrapError, match="source_dirty"):
        _plan(manifest, source, tmp_path)


def test_wrong_repository_and_revision_rejected(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    _git(source[0], "remote", "set-url", "origin", "https://example.invalid/evil.git")
    with pytest.raises(bootstrap.LocalBootstrapError, match="source_origin_unapproved"):
        _plan(manifest, source, tmp_path)
    _git(source[0], "remote", "set-url", "origin", "https://github.com/Blacksp1d3r/runner-mcp.git")
    payload = json.loads(manifest.read_text())
    payload["source_commit"] = "f" * 40
    manifest.write_text(json.dumps(payload))
    with pytest.raises(bootstrap.LocalBootstrapError, match="source_revision_mismatch"):
        _plan(manifest, source, tmp_path)


def test_manifest_permissions_and_symlink_refused(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    manifest.chmod(0o644)
    with pytest.raises(bootstrap.LocalBootstrapError, match="manifest_custody_invalid"):
        _plan(manifest, source, tmp_path)
    manifest.chmod(0o600)
    shortcut = tmp_path / "shortcut.json"
    shortcut.symlink_to(manifest)
    with pytest.raises(bootstrap.LocalBootstrapError, match="symlink_path_denied"):
        _plan(shortcut, source, tmp_path)


def test_stage_requires_exact_plan_confirmation_before_mutation(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    for value in ("", "f" * 64):
        with pytest.raises(bootstrap.LocalBootstrapError, match="confirmation"):
            bootstrap.stage_local_runner_mcp(
                manifest, source[0], accept_digest=value,
                home=home, machine_digest="a" * 64,
            )
    assert not home.exists()


def test_stage_reuses_existing_installer_and_remains_unactivated(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    expected = _plan(manifest, source, tmp_path)
    observed_commands: list[list[str]] = []

    def fake_runner(args, **kw):
        observed_commands.append(args)
        assert kw["check"] is False
        assert kw["stdin"] is subprocess.DEVNULL
        assert kw["stdout"] is subprocess.DEVNULL
        assert kw["stderr"] is subprocess.DEVNULL
        assert kw["env"]["PATH"] == "/usr/bin:/bin"
        assert "RUNNER_FABRIC_RELAY_CREDENTIAL" not in kw["env"]
        assert "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL" not in kw["env"]
        assert "GITHUB_TOKEN" not in kw["env"]
        if args[0] == "/usr/bin/bash":
            runtime = expected.stage_root / "runtime" / "venv" / "bin"
            runtime.mkdir(parents=True)
            (runtime / "runner-mcp").write_text("dummy")
            (runtime / "runner-mcp").chmod(0o700)
            (runtime / "python").write_text("dummy")
            (expected.stage_root / "bin" / "runner-mcp").symlink_to(
                runtime / "runner-mcp"
            )
        return subprocess.CompletedProcess(args, 0)

    result = bootstrap.stage_local_runner_mcp(
        manifest, source[0], accept_digest=expected.digest,
        home=home, machine_digest="a" * 64, runner=fake_runner,
    )

    assert len(observed_commands) == 3
    assert observed_commands[0] == ["/usr/bin/bash", str(source[0] / "install.sh")]
    assert result["stage_complete"] is True
    assert result["service_activation"] is False
    assert result["relay_enrollment"] is False
    assert result["original_client_ack"] is False
    marker = expected.stage_root / "stage-result.json"
    assert json.loads(marker.read_text()) == result
    assert marker.stat().st_mode & 0o777 == 0o600
    with pytest.raises(bootstrap.LocalBootstrapError, match="stage_already_present"):
        _plan(manifest, source, tmp_path)


def test_failed_installer_keeps_stage_without_faking_success(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    expected = _plan(manifest, source, tmp_path)

    def failed_runner(args, **kw):
        return subprocess.CompletedProcess(args, 1)

    with pytest.raises(bootstrap.LocalBootstrapError, match="existing_installer_failed"):
        bootstrap.stage_local_runner_mcp(
            manifest, source[0], accept_digest=expected.digest,
            home=tmp_path / "home", machine_digest="a" * 64,
            runner=failed_runner,
        )
    assert expected.stage_root.is_dir()
    assert not (expected.stage_root / "stage-result.json").exists()
    with pytest.raises(bootstrap.LocalBootstrapError, match="stage_already_present"):
        _plan(manifest, source, tmp_path)


def test_root_operator_is_denied_before_host_or_git(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(bootstrap.os, "geteuid", lambda: 0)
    with pytest.raises(bootstrap.LocalBootstrapError, match="root_operator_denied"):
        _plan(manifest, source, tmp_path)


def test_manifest_changed_during_install_never_marks_stage_ready(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    plan = _plan(manifest, source, tmp_path)

    def changing_runner(args, **kw):
        if args[0] == "/usr/bin/bash":
            root = plan.stage_root / "runtime" / "venv" / "bin"
            root.mkdir(parents=True)
            (root / "runner-mcp").write_text("dummy")
            (root / "runner-mcp").chmod(0o700)
            (root / "python").write_text("dummy")
            (plan.stage_root / "bin" / "runner-mcp").symlink_to(root / "runner-mcp")
            data = json.loads(manifest.read_text())
            data["runner_subject"] = "runner:unexpected"
            manifest.write_text(json.dumps(data))
        return subprocess.CompletedProcess(args, 0)

    with pytest.raises(bootstrap.LocalBootstrapError, match="manifest_changed_during_stage"):
        bootstrap.stage_local_runner_mcp(
            manifest, source[0], accept_digest=plan.digest,
            home=tmp_path / "home", machine_digest="a" * 64, runner=changing_runner,
        )
    assert not (plan.stage_root / "stage-result.json").exists()


def _failed_stage_root(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> Path:
    root = _plan(manifest, source, tmp_path).stage_root
    root.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    return root


def test_failed_stage_diagnosis_is_readonly_and_never_executes_venv(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
    monkeypatch,
) -> None:
    root = _failed_stage_root(manifest, source, tmp_path)
    bin_dir = root / "runtime" / "venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").symlink_to("/usr/bin/python3")
    before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))

    def deny_subprocess(*args, **kwargs):
        raise AssertionError("diagnosis must never run untrusted staged code")

    monkeypatch.setattr(bootstrap.subprocess, "run", deny_subprocess)
    result = bootstrap.diagnose_failed_stage(
        manifest, home=tmp_path / "home", machine_digest="a" * 64,
    )
    assert result == {
        "schema_version": "runner-mcp/local-stage-diagnosis/v1",
        "state": "failed_or_incomplete",
        "source_commit": source[1],
        "venv_python_kind": "symlink",
        "venv_pip_file_kind": "absent",
        "runner_cli_kind": "absent",
        "launcher_kind": "absent",
        "stage_marker_kind": "absent",
        "installer_error_cause": "undetermined",
        "diagnostic_method": "filesystem_metadata_only",
        "mutation_authorized": False,
        "service_activation_verified": False,
        "relay_enrollment_verified": False,
        "original_client_ack_verified": False,
    }
    assert sorted(str(path.relative_to(root)) for path in root.rglob("*")) == before
    assert "machine_id_sha256" not in result
    assert "installer_sha256" not in result
    assert "stage_root" not in result


def test_marker_or_pip_file_alone_does_not_authorize_stage(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    root = _failed_stage_root(manifest, source, tmp_path)
    pip_dir = (
        root / "runtime" / "venv" / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages" / "pip"
    )
    pip_dir.mkdir(parents=True)
    (pip_dir / "__init__.py").write_text("contents are not executed")
    (root / "stage-result.json").write_text('{"stage_complete":true}')
    actual = bootstrap.diagnose_failed_stage(
        manifest, home=tmp_path / "home", machine_digest="a" * 64,
    )
    assert actual["venv_pip_file_kind"] == "regular"
    assert actual["state"] == "marker_present_unverified"
    assert actual["service_activation_verified"] is False
    assert actual["original_client_ack_verified"] is False
    with pytest.raises(bootstrap.LocalBootstrapError, match="stage_already_present"):
        _plan(manifest, source, tmp_path)


def test_diagnosis_wrong_host_root_and_absent_stage_denied(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    with pytest.raises(bootstrap.LocalBootstrapError, match="wrong_physical_host"):
        bootstrap.diagnose_failed_stage(
            manifest, home=home, machine_digest="b" * 64,
        )
    with pytest.raises(bootstrap.LocalBootstrapError, match="failed_stage_not_found"):
        bootstrap.diagnose_failed_stage(
            manifest, home=home, machine_digest="a" * 64,
        )
    monkeypatch.setattr(bootstrap.os, "geteuid", lambda: 0)
    with pytest.raises(bootstrap.LocalBootstrapError, match="root_operator_denied"):
        bootstrap.diagnose_failed_stage(
            manifest, home=home, machine_digest="a" * 64,
        )


def test_diagnosis_refuses_symlinked_or_unsafe_partial_stage(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    root = _plan(manifest, source, tmp_path).stage_root
    victim = tmp_path / "victim"
    victim.mkdir()
    root.parent.mkdir(parents=True)
    root.symlink_to(victim, target_is_directory=True)
    with pytest.raises(bootstrap.LocalBootstrapError, match="symlink_path_denied"):
        bootstrap.diagnose_failed_stage(
            manifest, home=tmp_path / "home", machine_digest="a" * 64,
        )
    root.unlink()
    root.mkdir(mode=0o700)
    (root / "runtime").symlink_to(victim, target_is_directory=True)
    with pytest.raises(bootstrap.LocalBootstrapError, match="stage_layout_unsafe"):
        bootstrap.diagnose_failed_stage(
            manifest, home=tmp_path / "home", machine_digest="a" * 64,
        )
    assert not list(victim.iterdir())


def test_diagnosis_denies_insecure_stage_custody(
    manifest: Path, source: tuple[Path, str, str], tmp_path: Path,
) -> None:
    root = _failed_stage_root(manifest, source, tmp_path)
    root.chmod(0o755)
    with pytest.raises(bootstrap.LocalBootstrapError, match="stage_custody_invalid"):
        bootstrap.diagnose_failed_stage(
            manifest, home=tmp_path / "home", machine_digest="a" * 64,
        )
