"""Q7 lab-only temporary credential cache: no permanent token persistence."""
from __future__ import annotations

import os
import time

import pytest

from runner_mcp import fabric_q7_lab_session_auth as auth


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    root = tmp_path / "private-user-runtime"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    monkeypatch.setattr(auth, "_root", lambda: root)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(root))
    return root


def test_explicit_login_reuse_and_logout(runtime):
    assert auth.read_lab_login() is None
    auth.save_lab_login("fixed-SYNTHETIC-token-1")
    stored = runtime / "runner-mcp-q7-lab-login" / "contents-read-token"
    assert (stored.stat().st_mode & 0o777) == 0o600
    assert (stored.parent.stat().st_mode & 0o777) == 0o700
    assert auth.read_lab_login() == "fixed-SYNTHETIC-token-1"
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.save_lab_login("different-SYNTHETIC-token")
    assert auth.read_lab_login() == "fixed-SYNTHETIC-token-1"
    auth.clear_lab_login()
    assert auth.read_lab_login() is None
    auth.clear_lab_login()


def test_expired_token_not_reused_or_removed_on_read(runtime):
    auth.save_lab_login("fixed-SYNTHETIC-token-2")
    token = runtime / "runner-mcp-q7-lab-login" / "contents-read-token"
    at = time.time() - 3700
    os.utime(token, (at, at))
    assert auth.read_lab_login() is None
    assert token.is_file()
    auth.clear_lab_login()
    assert not token.exists()


def test_wrong_owner_root_mode_refuses_creation(runtime):
    runtime.chmod(0o755)
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.save_lab_login("fixed-SYNTHETIC-token-3")
    assert not (runtime / "runner-mcp-q7-lab-login").exists()


def test_different_runtime_env_refuses_creation(runtime, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime) + "else")
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.save_lab_login("fixed-SYNTHETIC-token-4")
    assert not (runtime / "runner-mcp-q7-lab-login").exists()


def test_symlinked_leaf_refused_no_follow(runtime, tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    (runtime / "runner-mcp-q7-lab-login").symlink_to(target, target_is_directory=True)
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.save_lab_login("fixed-SYNTHETIC-token-5")
    assert list(target.iterdir()) == []


def test_private_file_rejects_symlink_and_broad_mode(runtime):
    auth.save_lab_login("fixed-SYNTHETIC-token-6")
    p = runtime / "runner-mcp-q7-lab-login" / "contents-read-token"
    p.chmod(0o644)
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.read_lab_login()
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.clear_lab_login()
    p.chmod(0o600)
    auth.clear_lab_login()
    p.symlink_to(runtime / "unsafe")
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.read_lab_login()
    assert not (runtime / "unsafe").exists()


@pytest.mark.parametrize("token", ["short", "a" * 513, "a\n" * 10, "á" * 10])
def test_refuses_unqualified_token_without_creating_cache(runtime, token):
    with pytest.raises(auth.Q7LabLoginDenied):
        auth.save_lab_login(token)
    assert not (runtime / "runner-mcp-q7-lab-login").exists()


def test_future_mtime_refused(runtime):
    auth.save_lab_login("fixed-SYNTHETIC-token-7")
    token = runtime / "runner-mcp-q7-lab-login" / "contents-read-token"
    at = time.time() + 180
    os.utime(token, (at, at))
    assert auth.read_lab_login() is None
    auth.clear_lab_login()
