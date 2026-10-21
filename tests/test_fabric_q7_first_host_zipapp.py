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
    assert "Usage: fabric-q7-first-host.pyz prepare-root | preflight | probe-release | import" in result.stdout
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
