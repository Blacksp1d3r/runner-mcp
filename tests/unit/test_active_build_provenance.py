"""#669 isolated wheel/loaded-generation/owner cross-check regressions.

Synthetic owner callbacks have NO production authority and are only for tests.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import importlib.machinery
import io
import json
import shutil
import types
import zipfile
from pathlib import Path

import pytest

from runner_mcp.active_build_provenance import (
    _wheel_record_matches,
    qualify_serving_build,
)

REV = "a" * 40
OLD = "b" * 40
EPOCH = "c" * 32
VERSION = "0.1.175"
SOURCE = {
    "runner_mcp/__init__.py": b'__version__ = "0.1.175"\n',
    "runner_mcp/server.py": b'def active_response():\n    return "new"\n',
    "runner_mcp/build_identity.py": b'def runtime_identity():\n    return 123\n',
}


def make_wheel(root: Path, package_source: dict[str, bytes], *, tamper_record=False):
    wheel = root / "runner-mcp-test.whl"
    members = dict(package_source)
    members["aifordable_runner_mcp-0.1.175.dist-info/METADATA"] = b"Metadata-Version: 2.4\nName: aifordable-runner-mcp\nVersion: 0.1.175\n"
    entries = []
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        if tamper_record and name == "runner_mcp/server.py":
            digest = "0" * len(digest)
        entries.append((name, "sha256=" + digest, str(len(content))))
    record = "aifordable_runner_mcp-0.1.175.dist-info/RECORD"
    entries.append((record, "", ""))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(entries)
    members[record] = buffer.getvalue().encode()
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    wheel.chmod(0o600)
    return wheel, hashlib.sha256(wheel.read_bytes()).hexdigest()


def fake_module(name: str, source_path: Path, content: bytes):
    obj = types.ModuleType(name)
    obj.__file__ = str(source_path)
    obj.__spec__ = importlib.machinery.ModuleSpec(name, loader=None, origin=str(source_path))
    # Trusted fixed-source synthetic module execution tests in-memory tampering.
    exec(compile(content, str(source_path), "exec"), obj.__dict__)  # noqa: S102
    return obj


@pytest.fixture
def prepared(tmp_path: Path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    root.chmod(0o700)
    package = root / "runner_mcp"
    package.mkdir()
    for name, data in SOURCE.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    wheel, wheel_sha = make_wheel(root, SOURCE)
    receipt = root / "receipt.json"
    receipt.write_text(json.dumps({
        "schema_version": "runner-mcp/offline-artifact-receipt/v1",
        "source_revision": REV,
        "wheel_sha256": wheel_sha,
        "modules": {x.removeprefix("runner_mcp/"): hashlib.sha256(data).hexdigest() for x, data in SOURCE.items()},
    }))
    receipt.chmod(0o600)
    modules = {
        "runner_mcp": fake_module("runner_mcp", root / "runner_mcp/__init__.py", SOURCE["runner_mcp/__init__.py"]),
        "runner_mcp.server": fake_module("runner_mcp.server", root / "runner_mcp/server.py", SOURCE["runner_mcp/server.py"]),
        "runner_mcp.build_identity": fake_module("runner_mcp.build_identity", root / "runner_mcp/build_identity.py", SOURCE["runner_mcp/build_identity.py"]),
    }
    # Synthetic launch occurs AFTER fixture installation; never physical PID spoof.
    import runner_mcp.active_build_provenance as p
    monkeypatch.setattr(p, "_process_generation", lambda: (123, 10**30))
    kwargs = {"receipt": receipt, "wheel": wheel, "installed_package": package,
                  "loaded_version": VERSION, "installed_version": VERSION,
                  "serving_epoch": EPOCH, "modules": modules,
                  "independent_owner_verifier": lambda c: (
                      c.source_revision == REV and c.artifact_digest == wheel_sha
                      and c.serving_epoch == EPOCH and c.start_ticks == 123
                      and c.selected_loaded_code_sha256 is not None
                  )}
    return kwargs


def test_new_process_same_release_and_existing_owner_qualifies(prepared):
    result = qualify_serving_build(**prepared)
    assert result is not None
    assert result.source_revision == REV
    assert result.artifact_digest == hashlib.sha256(prepared["wheel"].read_bytes()).hexdigest()
    assert result.build_version == VERSION
    assert result.serving_epoch == EPOCH


def test_manual_upgrade_and_self_update_use_same_receipt_protocol(prepared):
    assert qualify_serving_build(**prepared) is not None
    # The receipt is independent of the old self-update-state.json marker.
    (prepared["receipt"].parent / "self-update-state.json").write_text('{"commit":"' + OLD + '"}')
    assert qualify_serving_build(**prepared).source_revision == REV


def test_missing_independent_owner_fails(prepared):
    prepared["independent_owner_verifier"] = None
    assert qualify_serving_build(**prepared) is None


def test_external_owner_rejection_fails(prepared):
    prepared["independent_owner_verifier"] = lambda _c: False
    assert qualify_serving_build(**prepared) is None


def test_owner_wrong_revision_fails(prepared):
    prepared["independent_owner_verifier"] = lambda c: c.source_revision == OLD
    assert qualify_serving_build(**prepared) is None


def test_old_process_after_pip_overwrite_fails(prepared, monkeypatch):
    import runner_mcp.active_build_provenance as p
    # Source was installed AFTER already-running process boot.
    monkeypatch.setattr(p, "_process_generation", lambda: (123, 1))
    assert qualify_serving_build(**prepared) is None


def test_same_version_changed_wheel_module_fails(prepared):
    (prepared["installed_package"] / "server.py").write_text('def active_response():\n    return "tampered"\n')
    assert qualify_serving_build(**prepared) is None


def test_same_version_old_in_memory_modules_after_disk_update_fails(prepared):
    # Package metadata and loaded version remain the same; file content changes.
    (prepared["installed_package"] / "build_identity.py").write_bytes(
        b'def runtime_identity():\n    return 456\n'
    )
    assert qualify_serving_build(**prepared) is None


def test_missing_receipt_fails(prepared):
    prepared["receipt"].unlink()
    assert qualify_serving_build(**prepared) is None


def test_tampered_receipt_fails(prepared):
    prepared["receipt"].write_text('not json')
    assert qualify_serving_build(**prepared) is None


def test_wrong_receipt_revision_fails(prepared):
    data = json.loads(prepared["receipt"].read_text())
    data["source_revision"] = OLD
    prepared["receipt"].write_text(json.dumps(data))
    assert qualify_serving_build(**prepared) is None


def test_wrong_wheel_hash_receipt_fails(prepared):
    data = json.loads(prepared["receipt"].read_text())
    data["wheel_sha256"] = "f" * 64
    prepared["receipt"].write_text(json.dumps(data))
    assert qualify_serving_build(**prepared) is None


def test_wrong_record_fails(prepared):
    tampered_wheel, _ = make_wheel(prepared["wheel"].parent, SOURCE, tamper_record=True)
    assert not _wheel_record_matches(tampered_wheel, hashlib.sha256(tampered_wheel.read_bytes()).hexdigest())
    assert qualify_serving_build(**prepared) is None


def test_wrong_loaded_version_fails(prepared):
    prepared["loaded_version"] = "0.1.174"
    assert qualify_serving_build(**prepared) is None


def test_foreign_process_epoch_rejected(prepared):
    prepared["serving_epoch"] = "d" * 32
    assert qualify_serving_build(**prepared) is None


def test_wrong_process_start_tick_rejected(prepared):
    prepared["independent_owner_verifier"] = lambda c: c.start_ticks == 456
    assert qualify_serving_build(**prepared) is None


def test_foreign_import_file_rejected(prepared, tmp_path):
    prepared["modules"]["runner_mcp.server"].__file__ = str(tmp_path / "foreign.py")
    assert qualify_serving_build(**prepared) is None


def test_foreign_import_origin_rejected(prepared):
    prepared["modules"]["runner_mcp.server"].__spec__.origin = "/foreign/server.py"
    assert qualify_serving_build(**prepared) is None


def test_missing_live_function_code_denied(prepared):
    del prepared["modules"]["runner_mcp.server"].active_response
    assert qualify_serving_build(**prepared) is None


def test_changed_live_function_code_owner_denied(prepared):
    from runner_mcp.serving_process_readonly import observe_current_process_modules
    before = observe_current_process_modules(imported_version=VERSION, installed_distribution_version=VERSION, modules=prepared["modules"])
    exec('def active_response():\n    return "injected"\n', prepared["modules"]["runner_mcp.server"].__dict__)  # noqa: S102
    original = prepared["independent_owner_verifier"]
    prepared["independent_owner_verifier"] = lambda c: (
        original(c) and c.selected_loaded_code_sha256 == before["loadedCodeObjectDigest"]
    )
    assert qualify_serving_build(**prepared) is None


def test_disk_symlink_rejected(prepared, tmp_path):
    p = prepared["installed_package"] / "build_identity.py"
    backup = tmp_path / "save.py"
    shutil.copy2(p, backup)
    p.unlink()
    p.symlink_to(backup)
    assert qualify_serving_build(**prepared) is None


def test_wheel_symlink_rejected(prepared, tmp_path):
    p = prepared["wheel"]
    other = tmp_path / "somewheel.whl"
    shutil.copy2(p, other)
    p.unlink()
    p.symlink_to(other)
    assert qualify_serving_build(**prepared) is None


def test_post_owner_wheel_mutation_fails_closed(prepared):
    def mutate(_challenge):
        with prepared["wheel"].open("ab") as handle:
            handle.write(b"tampered")
        return True
    prepared["independent_owner_verifier"] = mutate
    assert qualify_serving_build(**prepared) is None


def test_post_owner_installed_package_mutation_fails_closed(prepared):
    def mutate(_challenge):
        (prepared["installed_package"] / "server.py").write_bytes(b"modified")
        return True
    prepared["independent_owner_verifier"] = mutate
    assert qualify_serving_build(**prepared) is None


def test_modified_inmemory_function_without_file_change_is_rejected(prepared):
    # Even a lying owner cannot turn different live bytes into wheel bytes.
    exec('def active_response():\n    return "old-memory"\n',  # noqa: S102
         prepared["modules"]["runner_mcp.server"].__dict__)
    prepared["independent_owner_verifier"] = lambda _c: True
    assert qualify_serving_build(**prepared) is None


def test_rollback_with_new_authenticated_process_generation(prepared):
    # The same existing receipt protocol also works for an old rollback slot;
    # there is no substitution from self-update-state.json history.
    record = json.loads(prepared["receipt"].read_text())
    record["source_revision"] = OLD
    prepared["receipt"].write_text(json.dumps(record))
    prepared["serving_epoch"] = "e" * 32
    prepared["independent_owner_verifier"] = lambda c: (
        c.source_revision == OLD and c.serving_epoch == "e" * 32
    )
    rollback = qualify_serving_build(**prepared)
    assert rollback is not None and rollback.source_revision == OLD


def test_old_owner_epoch_cannot_authorize_new_process(prepared):
    prepared["independent_owner_verifier"] = lambda c: c.serving_epoch == "f" * 32
    assert qualify_serving_build(**prepared) is None


def test_exception_from_owner_never_yields_verified_identity(prepared):
    def broken(_challenge):
        raise ValueError("private token=must-not-leak")
    prepared["independent_owner_verifier"] = broken
    assert qualify_serving_build(**prepared) is None


def test_owner_mutates_inmemory_code_after_first_observation(prepared):
    def mutate(_challenge):
        exec('def runtime_identity():\n    return "injected"\n',  # noqa: S102
             prepared["modules"]["runner_mcp.build_identity"].__dict__)
        return True
    prepared["independent_owner_verifier"] = mutate
    assert qualify_serving_build(**prepared) is None


def test_owner_inputs_default_none_never_qualifies(prepared):
    from runner_mcp.active_build_provenance import observe_owner_qualified_serving_build
    assert observe_owner_qualified_serving_build(
        None, loaded_version=VERSION, installed_version=VERSION, serving_epoch=EPOCH
    ) is None


def test_injected_existing_owner_inputs_return_current_loaded_wheel(prepared, monkeypatch):
    # Wrapper normally observes real sys.modules; synthetically bind only
    # our isolated process fixture to avoid touching a physical server.
    import runner_mcp.active_build_provenance as p
    from runner_mcp.active_build_provenance import (
        ActiveBuildOwnerInputs,
        observe_owner_qualified_serving_build,
    )
    monkeypatch.setattr(p, "sys", types.SimpleNamespace(modules=prepared["modules"]))
    owner = ActiveBuildOwnerInputs(
        receipt=prepared["receipt"], wheel=prepared["wheel"],
        installed_package=prepared["installed_package"],
        independent_owner_verifier=prepared["independent_owner_verifier"],
    )
    result = observe_owner_qualified_serving_build(
        owner, loaded_version=VERSION, installed_version=VERSION,
        serving_epoch=EPOCH,
    )
    assert result is not None and result.source_revision == REV
    from runner_mcp.build_identity import BuildIdentity
    identity = BuildIdentity(
        component_id="runner-mcp", build_version=result.build_version,
        source_revision=result.source_revision, artifact_digest=result.artifact_digest,
    )
    assert identity.to_payload()["artifact_digest"] == result.artifact_digest
    assert identity.to_payload()["source_revision"] == REV


def test_existing_epoch_rejects_parent_to_child_fork_identity():
    from runner_mcp.serving_instance_epoch import ServingInstanceEpoch
    epoch = ServingInstanceEpoch()
    first = epoch.value()
    assert len(first) == 32 and epoch.value() == first


def test_malformed_owner_receipt_cannot_qualify_after_rollback(prepared):
    prepared["receipt"].write_text('{"commit":"' + OLD + '"}')
    assert qualify_serving_build(**prepared) is None
