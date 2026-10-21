"""Standalone first-host zipapp synthetic build and CLI denial tests."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from runpy import run_path

import pytest

_SOURCE = Path(__file__).resolve().parents[1]
_BUILDER = run_path(str(_SOURCE / "scripts/build_fabric_q7_first_host_zipapp.py"))
ZipappBuildRefused = _BUILDER["ZipappBuildRefused"]
build_q7_first_host_zipapp = _BUILDER["build_q7_first_host_zipapp"]


def test_bounded_zipapp_build_is_deterministic_and_disconnected(tmp_path):
    outputs = [tmp_path / "one.pyz", tmp_path / "two.pyz"]
    digests = [
        build_q7_first_host_zipapp(source_root=_SOURCE, destination=path)
        for path in outputs
    ]
    assert digests[0] == digests[1]
    assert outputs[0].stat().st_mode & 0o777 == 0o600
    assert digests[0] == hashlib.sha256(outputs[0].read_bytes()).hexdigest()

    result = subprocess.run(
        [sys.executable, str(outputs[0]), "--help"],
        check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0
    assert "Usage: fabric-q7-first-host.pyz prepare-root | preflight | probe-release | import | lab-preflight | lab-probe-release | lab-import | lab-readback | lab-login | lab-logout" in result.stdout
    assert "NO_INSTALL" not in result.stdout


def test_duplicate_build_never_overwrites_original(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    original = target.read_bytes()
    with pytest.raises(ZipappBuildRefused):
        build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    assert target.read_bytes() == original


def test_missing_source_refuses_without_creating_artifact(tmp_path):
    target = tmp_path / "importer.pyz"
    with pytest.raises(ZipappBuildRefused):
        build_q7_first_host_zipapp(source_root=tmp_path, destination=target)
    assert not target.exists()


def test_unrecognized_invocation_denied_without_fetch_or_write(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    for command in [["evil"], ["--source", "/tmp/evil"], ["--token", "SECRET"]]:
        result = subprocess.run(
            [sys.executable, str(target), *command],
            check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 2
        assert result.stdout.strip() == "WAIT_UNSUPPORTED_ACTION"
    assert list(tmp_path.iterdir()) == [target]


def test_preflight_refuses_unconfigured_source_without_mutation(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    sandbox_home = tmp_path / "empty-home"
    sandbox_home.mkdir()
    result = subprocess.run(
        [sys.executable, str(target), "preflight"],
        check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        env={**os.environ, "HOME": str(sandbox_home)},
    )
    assert result.returncode != 0
    assert result.stdout.strip().startswith("WAIT_")
    assert list(sandbox_home.iterdir()) == []


def test_prepare_root_requires_real_fixed_host_no_mutation_in_ci(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        [sys.executable, str(target), "prepare-root"],
        check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        env={**os.environ, "HOME": str(home)},
    )
    assert result.returncode != 0
    assert result.stdout.strip().startswith("Q7_FIXED_PRIVATE_ROOT=WAIT")
    assert list(home.iterdir()) == []



def test_signed_metadata_probe_cli_only_checks_metadata(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    entry = source["main"]
    objects = entry.__globals__
    roster = b"synthetic-roster"
    objects["_private_inputs"] = lambda: (roster, b"x" * 64, b"k" * 32, "a" * 64)
    received = []
    def safe_probe(**kwargs):
        received.append(kwargs)
        return {"state": "q7_release_metadata_exact_under_supplied_key"}
    objects["probe_signed_pinned_q7_metadata"] = safe_probe
    objects["import_signed_pinned_q7_once"] = lambda **kwargs: pytest.fail(
        "metadata preflight must not download any assets"
    )
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda message: "synthetic-token")
    assert entry(["probe-release"]) == 0
    captured = capsys.readouterr().out
    assert "Q7_RELEASE_METADATA=PASS" in captured
    assert "NO_ASSETS_NO_INSTALL_NO_ACK" in captured
    assert len(received) == 1
    assert received[0]["signed_roster"] == roster
    assert "synthetic-token" not in captured


def test_lab_private_root_denies_wrong_host_without_token_or_effect(tmp_path):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    entry = source["main"]
    lab = entry.__globals__
    lab["prepare_black_q7_private_root"] = lambda: pytest.fail(
        "lab-preflight may not create anything"
    )
    lab["_lab_owner_private_root"] = lambda: (_ for _ in ()).throw(
        ValueError("denied")
    )
    assert entry(["lab-preflight"]) == 1


def test_lab_probe_cli_never_requires_publisher_or_asset_fetch(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    entry = source["main"]
    funcs = entry.__globals__
    funcs["_lab_owner_private_root"] = lambda: None
    funcs["_private_inputs"] = lambda: pytest.fail("publisher keys not required")
    funcs["probe_q7_disposable_lab_metadata"] = lambda **kw: {
        "state": "q7_lab_metadata_only_untrusted_publisher"
    }
    funcs["import_q7_disposable_lab_once"] = lambda **kw: pytest.fail(
        "lab probe is read-only"
    )
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "synthetic-secret")
    assert entry(["lab-probe-release"]) == 0
    output = capsys.readouterr().out
    assert "Q7_LAB_METADATA=PASS_UNSIGNED" in output
    assert "NO_ASSETS_NO_INSTALL_NO_ACK" in output
    assert "synthetic-secret" not in output


def test_lab_import_cli_is_explicit_and_never_installs(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    entry = source["main"]
    funcs = entry.__globals__
    funcs["_lab_owner_private_root"] = lambda: None
    funcs["_private_inputs"] = lambda: pytest.fail("publisher keys not required")
    funcs["import_signed_pinned_q7_once"] = lambda **kw: pytest.fail(
        "signed path not implicitly used"
    )
    funcs["import_q7_disposable_lab_once"] = lambda **kw: {
        "state": "q7_lab_bytes_custodied_only"
    }
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "synthetic-secret")
    assert entry(["lab-import"]) == 0
    output = capsys.readouterr().out
    assert "Q7_LAB_PRIVATE_CUSTODY=PASS_UNSIGNED_SOURCE_BYTES_ONLY" in output
    assert "NO_INSTALL_NO_WORKER_NO_ACK" in output
    assert "synthetic-secret" not in output


def test_lab_readback_cli_is_offline_and_never_asks_for_token(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    area = main.__globals__
    area["_lab_owner_private_root"] = lambda: None
    area["_private_inputs"] = lambda: pytest.fail("no publisher signer for lab readback")
    area["read_q7_lab_custody_offline"] = lambda: {
        "state": "q7_lab_local_readback_verified_only", "asset_count": 33,
    }
    area["probe_q7_disposable_lab_metadata"] = lambda **kw: pytest.fail("no network")
    area["import_q7_disposable_lab_once"] = lambda **kw: pytest.fail("no writes")
    monkeypatch.setattr("getpass.getpass", lambda prompt: pytest.fail("no token"))
    assert main(["lab-readback"]) == 0
    output = capsys.readouterr().out
    assert "Q7_LAB_OFFLINE_READBACK=PASS_UNSIGNED_LOCAL_ONLY" in output
    assert "NO_NETWORK_NO_INSTALL_NO_ACK" in output


def test_lab_readback_cli_refuses_invalid_local_custody(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    area = main.__globals__
    area["_lab_owner_private_root"] = lambda: None
    area["read_q7_lab_custody_offline"] = lambda: (_ for _ in ()).throw(
        ValueError("synthetic corruption")
    )
    monkeypatch.setattr("getpass.getpass", lambda prompt: pytest.fail("no token"))
    assert main(["lab-readback"]) == 1
    assert "Q7_LAB_OFFLINE_READBACK=WAIT" in capsys.readouterr().out


def test_lab_login_validates_exact_metadata_then_caches_once(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    scope = main.__globals__
    scope["_lab_owner_private_root"] = lambda: None
    observed = []
    scope["probe_q7_disposable_lab_metadata"] = lambda **kw: (
        observed.append(kw["token"]) or
        {"state": "q7_lab_metadata_only_untrusted_publisher"}
    )
    scope["clear_lab_login"] = lambda: observed.append("clear")
    scope["save_lab_login"] = lambda token: observed.append("save")
    scope["import_q7_disposable_lab_once"] = lambda **kw: pytest.fail(
        "login must not import"
    )
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "SYNTHETIC-PRIVATE-TOKEN")
    assert main(["lab-login"]) == 0
    assert observed == ["SYNTHETIC-PRIVATE-TOKEN", "clear", "save"]
    output = capsys.readouterr().out
    assert "Q7_LAB_LOGIN=PASS_ONE_HOUR_USER_RUNTIME_ONLY" in output
    assert "SYNTHETIC-PRIVATE-TOKEN" not in output


def test_lab_import_reuses_cached_credential_without_terminal_then_forgets(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    scope = main.__globals__
    scope["_lab_owner_private_root"] = lambda: None
    scope["read_lab_login"] = lambda: "SYNTHETIC-CACHED-TOKEN"
    scope["clear_lab_login"] = lambda: events.append("logout")
    events = []
    scope["import_q7_disposable_lab_once"] = lambda **kw: (
        events.append(kw["token"]) or {"state": "q7_lab_bytes_custodied_only"}
    )
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("sys.stderr.isatty", lambda: False)
    monkeypatch.setattr("getpass.getpass", lambda prompt: pytest.fail("token reentry"))
    assert main(["lab-import"]) == 0
    assert events == ["SYNTHETIC-CACHED-TOKEN", "logout"]
    assert "SYNTHETIC-CACHED-TOKEN" not in capsys.readouterr().out


def test_lab_logout_does_not_read_token_or_call_network(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    scope = main.__globals__
    scope["_lab_owner_private_root"] = lambda: None
    scope["clear_lab_login"] = lambda: None
    scope["read_lab_login"] = lambda: pytest.fail("logout never reads token")
    scope["probe_q7_disposable_lab_metadata"] = lambda **kw: pytest.fail(
        "logout never contacts GitHub"
    )
    monkeypatch.setattr("getpass.getpass", lambda prompt: pytest.fail("token"))
    assert main(["lab-logout"]) == 0
    assert "Q7_LAB_LOGOUT=PASS_NO_TOKEN_PERSISTED" in capsys.readouterr().out


def test_lab_login_denies_when_release_auth_unavailable_without_caching(monkeypatch, capsys):
    source = run_path(str(_SOURCE / "scripts/fabric_q7_first_host_main.py"))
    main = source["main"]
    scope = main.__globals__
    scope["_lab_owner_private_root"] = lambda: None
    scope["probe_q7_disposable_lab_metadata"] = lambda **kw: (
        (_ for _ in ()).throw(ValueError("synthetic denied"))
    )
    scope["save_lab_login"] = lambda token: pytest.fail("invalid token must not persist")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "SYNTHETIC-FAILED-TOKEN")
    assert main(["lab-login"]) == 1
    assert "Q7_PRIVATE_CUSTODY=WAIT" in capsys.readouterr().out
