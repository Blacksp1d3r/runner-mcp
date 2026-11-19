"""#520 — Synthetische regressies voor de vaste root-only ACL-intrekking.

Er wordt nooit echt een Incus-socket of ACL gewijzigd. Test alleen de
beslissingsgrens en het fail-closed verloop van het zelfstandige programma.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "incus_acl_cleanup_once.py"
SPEC = importlib.util.spec_from_file_location("root_incus_acl_cleanup_test", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

BASE = "user::rw-\ngroup::rw-\nother::---\n"
MASK = "user::rw-\ngroup::rw-\nmask::rw-\nother::---\n"
GRANT = "user::rw-\nuser:1234:rw-\ngroup::rw-\nmask::rw-\nother::---\n"
BINDING = mod.Binding(
    host_short="lab-example", owner_name="worker-example", owner_uid=1234,
    owner_gid=1234, socket_path=Path("/example/incus.socket"), socket_gid=789,
    installed_sha256=hashlib.sha256(b"sealed-actor").hexdigest(),
)
SOCKET = mod.SocketEvidence(13, 28, 0, 789, 0o660, True, 1)


@pytest.mark.parametrize(
    ("acl", "action"),
    [(BASE, mod.Operation.NOOP), (MASK, mod.Operation.REVOKE),
     (GRANT, mod.Operation.REVOKE)],
)
def test_known_exact_acl_patterns(acl, action):
    assert mod.plan_cleanup(binding=BINDING, host="lab-example", caller_euid=0,
                            socket=SOCKET, acl_text=acl) == action


@pytest.mark.parametrize("bad", [
    "user::rw-\nuser:9999:rw-\ngroup::rw-\nmask::rw-\nother::---\n",
    "user::rw-\nuser:1234:r--\ngroup::rw-\nmask::rw-\nother::---\n",
    "user::rw-\nuser:1234:rw-\ngroup::rw-\nother::---\n",
    "user::rw-\ngroup::rw-\nmask::r--\nother::---\n",
    "user::rw-\ngroup::rw-\ngroup:9999:rw-\nmask::rw-\nother::---\n",
    "user::rw-\ngroup::rw-\nother::---\ndefault:user::rwx\n",
    "user::rw-\ngroup::rw-\nother::---\nother::---\n",
    "user::rw-\ngroup::rw-\nother::---\n# unexpected comment\n",
    "user::rw-\ngroup::r--\nother::---\n",
    "user::rw-\ngroup::rw-\nother::---\nmask::rw-\nuser:1234:rw-\nuser:9999:rw-\n",
    "user::rw-\ngroup::rw-\nother::---\n" + "Z" * 4097,
    "",
])
def test_unknown_acl_never_admits_revoke(bad):
    with pytest.raises(mod.CleanupStop, match="acl_unexpected"):
        mod._acl_action(bad, 1234)


@pytest.mark.parametrize("overrides", [
    {"host": "different-lab"}, {"caller_euid": 1234},
    {"socket": mod.SocketEvidence(13, 28, 1234, 789, 0o660, True, 1)},
    {"socket": mod.SocketEvidence(13, 28, 0, 10, 0o660, True, 1)},
    {"socket": mod.SocketEvidence(13, 28, 0, 789, 0o666, True, 1)},
    {"socket": mod.SocketEvidence(13, 28, 0, 789, 0o660, False, 1)},
    {"socket": mod.SocketEvidence(13, 28, 0, 789, 0o660, True, 2)},
    {"socket": mod.SocketEvidence(13, 0, 0, 789, 0o660, True, 1)},
])
def test_host_root_and_socket_generation_are_required(overrides):
    args = dict(binding=BINDING, host="lab-example", caller_euid=0,
                socket=SOCKET, acl_text=GRANT)
    args.update(overrides)
    with pytest.raises(mod.CleanupStop):
        mod.plan_cleanup(**args)


def test_private_config_rejects_smuggled_fields(monkeypatch):
    base = dict(schema=mod._SCHEMA, host_short="lab-example",
                owner_name="worker-example", owner_uid=1234, owner_gid=1234,
                socket_path="/example/incus.socket", socket_gid=789,
                installed_sha256=BINDING.installed_sha256)
    monkeypatch.setattr(mod.pwd, "getpwnam", lambda name: SimpleNamespace(
        pw_uid=1234, pw_gid=1234))
    for payload in [
        {**base, "extra": "arbitrary"},
        {**base, "socket_path": "relative"},
        {**base, "socket_path": "/example/../other"},
        {**base, "owner_uid": True},
        {**base, "host_short": "bad host"},
        {**base, "owner_name": "../name"},
        {**base, "installed_sha256": "a" * 40},
    ]:
        monkeypatch.setattr(mod, "_read_root_file",
                            lambda *a, d=payload, **k: json.dumps(d).encode())
        with pytest.raises(mod.CleanupStop, match="private_policy_invalid"):
            mod._binding()


def _fake_runtime(monkeypatch, *, initial=GRANT, digest_ok=True,
                  host="lab-example", final_access_denied=True,
                  setfacl_rc=0):
    state = {"acl": initial, "writes": [], "verified": 0}
    binding = BINDING if digest_ok else mod.Binding(
        BINDING.host_short, BINDING.owner_name, BINDING.owner_uid,
        BINDING.owner_gid, BINDING.socket_path, BINDING.socket_gid,
        hashlib.sha256(b"different-file").hexdigest())
    monkeypatch.setattr(mod, "_read_root_file", lambda *a, **k: b"sealed-actor")
    monkeypatch.setattr(mod, "_binding", lambda: binding)
    monkeypatch.setattr(mod, "_socket", lambda *a: SOCKET)
    monkeypatch.setattr(mod, "_acl", lambda *a: state["acl"])
    monkeypatch.setattr(mod, "_owner_denied", lambda *a: final_access_denied)
    monkeypatch.setattr(mod.sys, "argv", [str(mod._INSTALLED)])
    monkeypatch.setattr(mod.sys, "flags", SimpleNamespace(isolated=1, no_site=1))
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setattr(mod.os, "uname", lambda: SimpleNamespace(nodename=host))

    def run(args, **kwargs):
        state["writes"].append(args)
        if setfacl_rc == 0:
            state["acl"] = BASE
        return subprocess.CompletedProcess(args, setfacl_rc, "", "")
    monkeypatch.setattr(mod, "_run", run)
    return state


@pytest.mark.parametrize("original", [BASE, GRANT, MASK])
def test_idempotent_revoke_and_stale_mask_restoration(monkeypatch, original):
    state = _fake_runtime(monkeypatch, initial=original)
    expected = mod.Operation.NOOP if original == BASE else mod.Operation.REVOKE
    assert mod.cleanup_once() == expected
    assert state["acl"] == BASE
    assert len(state["writes"]) == (0 if original == BASE else 1)
    if state["writes"]:
        assert state["writes"][0] == [
            "/usr/bin/setfacl", "-b", "--", "/example/incus.socket"
        ]


def test_source_digest_mismatch_refuses_before_mutation(monkeypatch):
    state = _fake_runtime(monkeypatch, digest_ok=False)
    with pytest.raises(mod.CleanupStop, match="helper_source_mismatch"):
        mod.cleanup_once()
    assert state["writes"] == []


def test_wrong_original_host_refuses_before_mutation(monkeypatch):
    state = _fake_runtime(monkeypatch, host="wrong")
    with pytest.raises(mod.CleanupStop, match="host_or_authority_mismatch"):
        mod.cleanup_once()
    assert state["writes"] == []


def test_invalid_acl_never_invokes_setfacl(monkeypatch):
    state = _fake_runtime(monkeypatch, initial=GRANT+"user:9999:rw-\n")
    with pytest.raises(mod.CleanupStop, match="acl_unexpected"):
        mod.cleanup_once()
    assert state["writes"] == []


def test_failed_setfacl_is_not_success(monkeypatch):
    state = _fake_runtime(monkeypatch, setfacl_rc=1)
    with pytest.raises(mod.CleanupStop, match="revoke_failed"):
        mod.cleanup_once()
    assert len(state["writes"]) == 1


def test_negative_access_is_required_even_with_clean_acl(monkeypatch):
    _fake_runtime(monkeypatch, final_access_denied=False)
    with pytest.raises(mod.CleanupStop, match="owner_access_unverified"):
        mod.cleanup_once()


def test_verify_denies_changed_socket_inode(monkeypatch):
    _fake_runtime(monkeypatch)
    monkeypatch.setattr(mod, "_socket", lambda *a: mod.SocketEvidence(
        13, 29, 0, 789, 0o660, True, 1))
    with pytest.raises(mod.CleanupStop, match="socket_generation_changed"):
        mod._verify(BINDING, SOCKET)


def test_runtime_requires_no_caller_args_and_isolation(monkeypatch):
    state = _fake_runtime(monkeypatch)
    monkeypatch.setattr(mod.sys, "argv", [str(mod._INSTALLED), "some-path"])
    with pytest.raises(mod.CleanupStop, match="helper_runtime_untrusted"):
        mod.cleanup_once()
    assert state["writes"] == []
    monkeypatch.setattr(mod.sys, "argv", [str(mod._INSTALLED)])
    monkeypatch.setattr(mod.sys, "flags", SimpleNamespace(isolated=0, no_site=0))
    with pytest.raises(mod.CleanupStop, match="helper_runtime_untrusted"):
        mod.cleanup_once()
    assert state["writes"] == []


def test_main_only_returns_bounded_status(monkeypatch, capsys):
    monkeypatch.setattr(mod, "cleanup_once", lambda: (_ for _ in ()).throw(
        mod.CleanupStop("acl_unexpected")))
    assert mod.main() == 2
    assert capsys.readouterr().out == "INCUS_ACL_REVOKE=STOP:acl_unexpected\n"
