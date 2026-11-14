"""#669: fresh pip, immutable wheel custody and source/owner replay regressions.

All subprocesses are created in disposable local virtual environments. A
synthetic owner callback is never evidence from physical github-runner.
No network access, external runner, original-service fault injection or CI.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from runner_mcp.active_build_provenance import _validated_self_update_lineage
from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight
from runner_mcp.offline_installed_record_preflight import offline_installed_record_preflight
from runner_mcp.self_update_install import PackageInstallError, SelfUpdatePackageInstaller

SOURCE_DIR = Path(__file__).resolve().parents[1] / "src" / "runner_mcp"
REV = "f" * 40
BEFORE = "e" * 40
JOB = "d" * 32


def _wheel(root: Path, version: str, *, bad_record: bool = False) -> Path:
    """Build a synthetic wheel via RECORD; never call it an official release."""
    members: dict[str, bytes] = {
        "runner_mcp/__init__.py": f'__version__ = "{version}"\n'.encode(),
        "runner_mcp/server.py": b'def generation():\n    return "' + version.encode() + b'"\n',
        "runner_mcp/self_update.py": b'def import_test():\n    return True\n',
    }
    # Only the future synthetic 0.1.175 runtime carries the actual new source.
    if version == "0.1.175":
        for name in (
            "active_build_provenance.py", "build_identity.py",
            "artifact_receipt_preflight.py", "offline_installed_record_preflight.py",
            "serving_process_readonly.py",
        ):
            members["runner_mcp/" + name] = (SOURCE_DIR / name).read_bytes()
    else:
        members["runner_mcp/build_identity.py"] = b'def identity():\n    return "old"\n'
    dist = f"aifordable_runner_mcp-{version}.dist-info/"
    members[dist + "METADATA"] = (
        f"Metadata-Version: 2.1\nName: aifordable-runner-mcp\nVersion: {version}\n"
    ).encode()
    members[dist + "WHEEL"] = b"Wheel-Version: 1.0\nGenerator: isolated-669-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    record = dist + "RECORD"
    rows: list[tuple[str, str, str]] = []
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        if bad_record and name == "runner_mcp/server.py":
            digest = "X" * 43
        rows.append((name, "sha256=" + digest, str(len(content))))
    rows.append((record, "", ""))
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    members[record] = buf.getvalue().encode()
    wheel = root / f"aifordable_runner_mcp-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)
    wheel.chmod(0o600)
    return wheel


def _call(python: Path, *args: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.update({"PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    return subprocess.run(
        [str(python), *args], input=input, capture_output=True, text=True,
        check=False, timeout=80, env=environment,
    )


@pytest.fixture
def installation(tmp_path: Path):
    venv = tmp_path / "venv"
    built = _call(Path(sys.executable), "-m", "venv", "--system-site-packages", str(venv))
    assert built.returncode == 0, built.stderr[-450:]
    python = venv / "bin/python"
    config = tmp_path / "settings"
    config.mkdir(mode=0o700)
    installed = next(venv.glob("lib/python*/site-packages")) / "runner_mcp"
    installer = SelfUpdatePackageInstaller(config_dir=config, python_executable=python)
    return tmp_path, installer, python, installed


def _install(installer: SelfUpdatePackageInstaller, wheel: Path, *, job: str) -> Path:
    target = installer.artifacts_root / job / "target"
    target.mkdir(mode=0o700, parents=True)
    target.chmod(0o700)
    installed = target / wheel.name
    installed.write_bytes(wheel.read_bytes())
    installed.chmod(0o600)
    # Exercise the actual offline pip install command, not a fake runner.
    installer.install_wheel(installed)
    installer.verify_runtime()
    return installed


def test_actual_pip_install_new_process_provenance_and_rollback(installation):
    root, installer, python, package = installation
    old = _wheel(root, "0.1.174")
    new = _wheel(root, "0.1.175")
    _install(installer, old, job="a" * 32)
    probe = _call(python, "-c", "import runner_mcp; print(runner_mcp.__version__)")
    assert probe.returncode == 0 and probe.stdout.strip() == "0.1.174"

    _install(installer, new, job=JOB)
    probe = _call(python, "-c", "import runner_mcp; print(runner_mcp.__version__)")
    assert probe.returncode == 0 and probe.stdout.strip() == "0.1.175"
    receipt = installer.retain_installed_wheel_provenance(
        job_id=JOB, target_commit=REV, baseline_commit=BEFORE,
        baseline_wheel_sha256="b" * 64, installed_package=package,
    )
    assert receipt["state"] == "retained_installer_bytes_only"
    assert receipt["source_revision"] == REV
    assert receipt["owner_verified"] is False
    assert receipt["loaded_process_verified"] is False
    sha = receipt["artifact_digest"]
    custody = installer.artifacts_root.parent / "artifact-custody" / "sha256" / sha[:2]
    retained = custody / sha
    retained_receipt = custody / (sha + ".receipt.json")
    lineage = custody / (sha + "." + JOB + ".lineage.json")
    assert offline_installed_record_preflight(retained, package, sha)["state"] == "offline_installed_record_match"
    assert _validated_self_update_lineage(lineage, retained, retained_receipt, REV, sha) == (JOB, BEFORE, "b" * 64)
    installer.cleanup_job(JOB)
    assert not (installer.artifacts_root / JOB).exists()
    assert retained.exists() and retained_receipt.exists() and lineage.exists()

    # A fresh Python process after installation is allowed to inspect source
    # and synthetic owner challenge only; no physical owner is present here.
    script = """import json, os, sys
from pathlib import Path
import runner_mcp, runner_mcp.server, runner_mcp.build_identity
from importlib.metadata import version
from runner_mcp.active_build_provenance import qualify_serving_build
sha, job, rev, base = sys.argv[1:5]
package = Path(runner_mcp.__file__).parent
wheel = Path(sys.argv[5]); receipt = Path(sys.argv[6]); lineage = Path(sys.argv[7])
seen = []
def synthetically_approved(challenge):
    seen.append([challenge.self_update_job_id, challenge.rollback_baseline_revision,
                 challenge.pid == os.getpid(), challenge.source_revision, challenge.artifact_digest,
                 challenge.rollback_baseline_wheel_sha256])
    return (challenge.self_update_job_id == job and
            challenge.rollback_baseline_revision == base and
            challenge.rollback_baseline_wheel_sha256 == 'b'*64 and
            challenge.pid == os.getpid() and challenge.artifact_digest == sha and
            challenge.source_revision == rev)
result = qualify_serving_build(
 receipt=receipt,wheel=wheel,installed_package=package,
 loaded_version=runner_mcp.__version__, installed_version=version('aifordable-runner-mcp'),
 serving_epoch='a'*32, independent_owner_verifier=synthetically_approved,
 lineage=lineage, installed_record_required=True)
print(json.dumps({'version':runner_mcp.__version__, 'result':bool(result),
                  'owner_challenge':seen, 'real_owner_authenticated':False}))
"""
    result = _call(python, "-c", script, sha, JOB, REV, BEFORE,
                   str(retained), str(retained_receipt), str(lineage))
    assert result.returncode == 0, result.stderr[-700:]
    parsed = json.loads(result.stdout.strip())
    assert parsed["version"] == "0.1.175"
    assert parsed["real_owner_authenticated"] is False
    assert parsed["result"] is True
    assert parsed["owner_challenge"][0][0:2] == [JOB, BEFORE]

    # Real offline pip rollback after the synthetic upgrade, not a mock.
    _install(installer, old, job="c" * 32)
    downgraded = _call(python, "-c", "import runner_mcp; print(runner_mcp.__version__)")
    assert downgraded.returncode == 0 and downgraded.stdout.strip() == "0.1.174"
    assert offline_artifact_receipt_preflight(retained_receipt, retained, package)["state"] == "unverified"
    assert offline_installed_record_preflight(retained, package, sha)["state"] == "unverified"


def test_invalid_record_never_retained(installation):
    root, installer, _python, package = installation
    good = _wheel(root, "0.1.175")
    _install(installer, good, job=JOB)
    # Replace only the staged ZIP with one whose RECORD is fraudulent.
    damaged = _wheel(root, "0.1.175", bad_record=True)
    stage = installer.artifacts_root / JOB / "target" / damaged.name
    stage.write_bytes(damaged.read_bytes())
    stage.chmod(0o600)
    with pytest.raises(PackageInstallError, match="RECORD mismatch"):
        installer.retain_installed_wheel_provenance(
            job_id=JOB, target_commit=REV, baseline_commit=None,
            baseline_wheel_sha256=None, installed_package=package,
        )


def test_mismatched_rollback_relation_denies_lineage(installation):
    root, installer, _python, package = installation
    new = _wheel(root, "0.1.175")
    _install(installer, new, job=JOB)
    record = installer.retain_installed_wheel_provenance(
        job_id=JOB,target_commit=REV, baseline_commit=None,
        baseline_wheel_sha256=None,installed_package=package,
    )
    sha = record["artifact_digest"]
    directory = installer.artifacts_root.parent / "artifact-custody" / "sha256" / sha[:2]
    wheel = directory / sha
    receipt = directory / (sha + ".receipt.json")
    lineage = directory / (sha + "." + JOB + ".lineage.json")
    assert _validated_self_update_lineage(lineage, wheel, receipt, REV, sha) == (JOB, None, None)
    changed = json.loads(lineage.read_text())
    changed["baseline_revision"] = BEFORE  # No matching baseline wheel hash.
    lineage.write_text(json.dumps(changed) + "\n")
    assert _validated_self_update_lineage(lineage, wheel, receipt, REV, sha) is None


def test_unauthorized_source_revision_never_auto_verified(installation):
    root, installer, _python, package = installation
    new = _wheel(root, "0.1.175")
    _install(installer, new, job=JOB)
    record = installer.retain_installed_wheel_provenance(
        job_id=JOB, target_commit=REV, baseline_commit=None,
        baseline_wheel_sha256=None, installed_package=package,
    )
    assert record["owner_verified"] is False
    assert record["loaded_process_verified"] is False


def test_failed_actual_pip_install_keeps_previous_release_without_receipt(installation):
    root, installer, python, package = installation
    old = _wheel(root, "0.1.174")
    _install(installer, old, job="a" * 32)
    target = installer.artifacts_root / JOB / "target"
    target.mkdir(mode=0o700, parents=True)
    broken = target / "aifordable_runner_mcp-0.1.175-py3-none-any.whl"
    broken.write_bytes(b"malformed zip, no installed RECORD")
    broken.chmod(0o600)
    with pytest.raises(PackageInstallError, match="package installation failed"):
        installer.install_wheel(broken)
    running = _call(python, "-c", "import runner_mcp; print(runner_mcp.__version__)")
    assert running.returncode == 0 and running.stdout.strip() == "0.1.174"
    assert package.is_dir()
    assert not (installer.artifacts_root.parent / "artifact-custody").exists()
    assert not any(target.glob("*.receipt.json"))


def test_old_process_keeps_old_loaded_code_after_same_version_pip_replacement(installation):
    root, installer, python, package = installation
    old = _wheel(root, "0.1.175")
    _install(installer, old, job=JOB)
    captured = installer.retain_installed_wheel_provenance(
        job_id=JOB, target_commit=REV, baseline_commit=None,
        baseline_wheel_sha256=None, installed_package=package,
    )
    sha = captured["artifact_digest"]
    directory = installer.artifacts_root.parent / "artifact-custody" / "sha256" / sha[:2]
    wheel = directory / sha
    receipt = directory / (sha + ".receipt.json")
    lineage = directory / (sha + "." + JOB + ".lineage.json")
    program = """import os, sys
from pathlib import Path
from importlib.metadata import version
import runner_mcp, runner_mcp.server, runner_mcp.build_identity
from runner_mcp.active_build_provenance import qualify_serving_build
print('READY', flush=True)
sys.stdin.readline()
identity = qualify_serving_build(
    receipt=Path(sys.argv[1]), wheel=Path(sys.argv[2]),
    installed_package=Path(runner_mcp.__file__).parent,
    loaded_version=runner_mcp.__version__,
    installed_version=version('aifordable-runner-mcp'),
    serving_epoch='c'*32, independent_owner_verifier=lambda _: True,
    lineage=Path(sys.argv[3]), installed_record_required=True)
print('REJECTED' if identity is None else 'WRONG_APPROVAL', flush=True)
"""
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    worker = subprocess.Popen(
        [str(python), "-u", "-c", program, str(receipt), str(wheel), str(lineage)],
        text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=environment,
    )
    try:
        assert worker.stdout is not None
        assert worker.stdout.readline().strip() == "READY"
        # Same version and dist metadata, but a genuinely different installed
        # source image after process start. The old process remains stale.
        newer = root / "repacked"
        newer.mkdir()
        changed = _wheel(newer, "0.1.175")
        with zipfile.ZipFile(changed) as z:
            original = {name: z.read(name) for name in z.namelist() if not name.endswith("/RECORD")}
        original["runner_mcp/server.py"] = b'def generation():\n    return "different-same-version"\n'
        # Construct a new valid RECORD with the changed bytes.
        record_name = "aifordable_runner_mcp-0.1.175.dist-info/RECORD"
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        for name, content in original.items():
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
            writer.writerow((name, "sha256=" + digest, str(len(content))))
        writer.writerow((record_name, "", ""))
        with zipfile.ZipFile(changed, "w") as archive:
            for name, content in original.items():
                archive.writestr(name, content)
            archive.writestr(record_name, buf.getvalue().encode())
        changed.chmod(0o600)
        _install(installer, changed, job="b" * 32)
        assert worker.stdin is not None
        worker.stdin.write("CONTINUE\n")
        worker.stdin.flush()
        assert worker.stdout.readline().strip() == "REJECTED"
        assert worker.wait(timeout=15) == 0
        # A new process reads the replacement source; the old receipt now
        # points to another wheel generation and MUST not validate.
        assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=10)


def test_existing_manager_default_retention_off_and_explicit_owner_optin(tmp_path):
    """Existing no-owner callers cannot unexpectedly acquire custody writes."""
    from runner_mcp.self_update import SelfUpdateError, SelfUpdateManager

    kwargs = dict(
        config_dir=tmp_path / "default", registry=None, safety=None,
        tests=None, source=None, resource_url="http://127.0.0.1:8000/mcp",
    )
    manager = SelfUpdateManager(**kwargs)
    assert manager._retain_installed_provenance is False
    explicit = SelfUpdateManager(
        **{**kwargs, "config_dir": tmp_path / "owner"},
        retain_installed_provenance=True,
    )
    assert explicit._retain_installed_provenance is True
    with pytest.raises(SelfUpdateError, match="provenance retention flag"):
        SelfUpdateManager(
            **{**kwargs, "config_dir": tmp_path / "invalid"},
            retain_installed_provenance="enabled",
        )


def test_replayed_identical_custody_is_idempotent_but_foreign_commit_denied(installation):
    root, installer, _python, package = installation
    wheel = _wheel(root, "0.1.175")
    _install(installer, wheel, job=JOB)
    args = dict(job_id=JOB, target_commit=REV, baseline_commit=None,
                baseline_wheel_sha256=None, installed_package=package)
    one = installer.retain_installed_wheel_provenance(**args)
    two = installer.retain_installed_wheel_provenance(**args)
    assert one == two
    with pytest.raises(PackageInstallError, match="source claim conflict"):
        installer.retain_installed_wheel_provenance(
            **{**args, "target_commit": BEFORE},
        )
