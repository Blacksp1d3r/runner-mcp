import os
import stat
from pathlib import Path

import pytest

from runner_mcp.fabric_a6_binding_repair import (
    FabricA6BindingRepairError,
    classify_a6_bindings_for_doctor,
    inspect_a6_binding_state,
    repair_a6_qualification_binding,
    _prepare_fixed_a6_private_roots_under,
    prepare_black_a6_private_roots,
)
from runner_mcp.onboarding import load_env_file


def _private_runtime(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env_path = config / "runner-mcp.env"
    env_path.write_text("UNRELATED_VALUE=keep\n", encoding="utf-8")
    env_path.chmod(0o600)

    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    for name in ("a6-update-journal", "a6-evidence"):
        target = state / name
        target.mkdir(mode=0o700)
        target.chmod(0o700)

    environment = {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}
    return config, state, environment


@pytest.mark.parametrize("operation", ["inspect", "repair"])
def test_private_a6_env_hardlink_alias_refused_without_mutation(
    tmp_path: Path, operation: str,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    env_path = config / "runner-mcp.env"
    original = env_path.read_text(encoding="utf-8")
    alias = tmp_path / "alias-to-private-env"
    alias.hardlink_to(env_path)
    assert env_path.stat().st_nlink == 2

    if operation == "inspect":
        with pytest.raises(
            FabricA6BindingRepairError, match="fabric_a6_runtime_config_unavailable"
        ):
            inspect_a6_binding_state(config_dir=config, state_root=state)
    else:
        with pytest.raises(
            FabricA6BindingRepairError, match="fabric_a6_runtime_config_unavailable"
        ):
            repair_a6_qualification_binding(
                environment=environment,
                config_dir=config,
                state_root=state,
                fabric_revision="f" * 40,
            )

    assert env_path.read_text(encoding="utf-8") == original
    assert alias.read_text(encoding="utf-8") == original
    assert environment == {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}


def test_repair_restores_exact_fixed_a6_binding_and_preserves_other_values(
    tmp_path: Path,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    revision = "f" * 40

    repair_a6_qualification_binding(
        environment=environment,
        config_dir=config,
        state_root=state,
        fabric_revision=revision,
    )

    values = load_env_file(config / "runner-mcp.env")
    expected = {
        "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT",
        "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN",
        "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN",
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT",
        "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN",
        "RUNNER_FABRIC_SYNTHETIC_PROBE_ID",
        "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT",
        "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION",
        "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS",
        "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT",
        "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION",
    }
    assert expected <= values.keys()
    assert values["UNRELATED_VALUE"] == "keep"
    assert values["RUNNER_FABRIC_RUNNER_MCP_ENDPOINT"] == (
        "http://127.0.0.1:8000/mcp"
    )
    assert values["RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN"] == "r" * 48
    assert values["RUNNER_FABRIC_SYNTHETIC_PROBE_ID"] == "fleet-a6"
    assert values["RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT"] == (
        "runner:aifordable-lab"
    )
    assert values["RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION"] == revision
    assert values["RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION"] == revision
    assert values["RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS"] == "60"
    assert environment["RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN"] == (
        "control:evidence"
    )
    assert environment["RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN"] == (
        "target:runner-mcp"
    )


def test_repair_is_noop_without_durable_a6_state_roots(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env_path = config / "runner-mcp.env"
    env_path.write_text("UNRELATED_VALUE=keep\n", encoding="utf-8")
    env_path.chmod(0o600)
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    environment = {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}

    repair_a6_qualification_binding(
        environment=environment,
        config_dir=config,
        state_root=state,
        fabric_revision="f" * 40,
    )

    assert load_env_file(env_path) == {"UNRELATED_VALUE": "keep"}


def test_repair_fails_closed_on_partial_or_unsafe_a6_state(tmp_path: Path) -> None:
    config, state, environment = _private_runtime(tmp_path)
    (state / "a6-evidence").rmdir()

    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_incomplete"):
        repair_a6_qualification_binding(
            environment=environment,
            config_dir=config,
            state_root=state,
            fabric_revision="f" * 40,
        )

    evidence = state / "a6-evidence"
    evidence.mkdir(mode=0o700)
    evidence.chmod(0o755)

    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        repair_a6_qualification_binding(
            environment=environment,
            config_dir=config,
            state_root=state,
            fabric_revision="f" * 40,
        )

def test_inspection_reports_sanitized_binding_and_state_root_counts(
    tmp_path: Path,
) -> None:
    config, state, environment = _private_runtime(tmp_path)

    before = inspect_a6_binding_state(
        config_dir=config,
        state_root=state,
    )
    assert before == {
        "state_roots": "ready",
        "binding_count": 0,
        "binding_total": 11,
        "binding_complete": False,
    }

    repair_a6_qualification_binding(
        environment=environment,
        config_dir=config,
        state_root=state,
        fabric_revision="f" * 40,
    )
    after = inspect_a6_binding_state(
        config_dir=config,
        state_root=state,
    )
    assert after == {
        "state_roots": "ready",
        "binding_count": 11,
        "binding_total": 11,
        "binding_complete": True,
    }


def test_inspection_distinguishes_absent_roots_from_shared_bindings(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env_path = config / "runner-mcp.env"
    env_path.write_text(
        "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT=http://127.0.0.1:8000/mcp\n"
        + "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN="
        + ("r" * 48)
        + "\n",
        encoding="utf-8",
    )
    env_path.chmod(0o600)
    state = tmp_path / "state"
    state.mkdir(mode=0o700)

    observed = inspect_a6_binding_state(
        config_dir=config,
        state_root=state,
    )

    assert observed == {
        "state_roots": "absent",
        "binding_count": 2,
        "binding_total": 11,
        "binding_complete": False,
    }


@pytest.mark.parametrize("root_name", ["a6-update-journal", "a6-evidence"])
def test_repair_rejects_dangling_a6_root_symlink_before_noop(
    tmp_path: Path, root_name: str,
) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env_path = config / "runner-mcp.env"
    env_path.write_text("UNRELATED_VALUE=keep\n", encoding="utf-8")
    env_path.chmod(0o600)
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    (state / root_name).symlink_to(state / "nonexistent-target", target_is_directory=True)
    environment = {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}

    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        repair_a6_qualification_binding(
            environment=environment,
            config_dir=config,
            state_root=state,
            fabric_revision="f" * 40,
        )
    assert load_env_file(env_path) == {"UNRELATED_VALUE": "keep"}
    assert "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT" not in environment


def test_symlinked_a6_parent_root_blocks_repair_and_diagnostic(
    tmp_path: Path,
) -> None:
    config, real_state, environment = _private_runtime(tmp_path)
    linked_root = tmp_path / "linked-state"
    linked_root.symlink_to(real_state, target_is_directory=True)
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        repair_a6_qualification_binding(
            environment=environment,
            config_dir=config,
            state_root=linked_root,
            fabric_revision="f" * 40,
        )
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        inspect_a6_binding_state(config_dir=config, state_root=linked_root)
    assert load_env_file(config / "runner-mcp.env") == {
        "UNRELATED_VALUE": "keep",
    }
    assert "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT" not in environment

def test_a6_symlink_cycle_in_parent_is_sanitized_before_mutation(
    tmp_path: Path,
) -> None:
    config, _state, environment = _private_runtime(tmp_path)
    loop = tmp_path / "loop"
    loop.symlink_to(loop, target_is_directory=True)
    state_root = loop / "a6-state"
    from runner_mcp.fabric_a6_binding_repair import a6_state_requested

    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        a6_state_requested(state_root)
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        inspect_a6_binding_state(config_dir=config, state_root=state_root)
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        repair_a6_qualification_binding(
            environment=environment,
            config_dir=config,
            state_root=state_root,
            fabric_revision="f" * 40,
        )
    assert load_env_file(config / "runner-mcp.env") == {
        "UNRELATED_VALUE": "keep",
    }
    assert "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT" not in environment


@pytest.mark.parametrize(
    ("inspection", "expected"),
    [
        (
            {"state_roots": "absent", "binding_count": 0, "binding_total": 11,
             "binding_complete": False},
            ("warn", "not_configured_0_of_11"),
        ),
        (
            {"state_roots": "ready", "binding_count": 11, "binding_total": 11,
             "binding_complete": True},
            ("pass", "ready_11_of_11"),
        ),
        (
            {"state_roots": "ready", "binding_count": 0, "binding_total": 11,
             "binding_complete": False},
            ("warn", "ready_0_of_11"),
        ),
        (
            {"state_roots": "absent", "binding_count": 2, "binding_total": 11,
             "binding_complete": False},
            ("warn", "absent_2_of_11"),
        ),
        (
            {"state_roots": "unsafe", "binding_count": 11, "binding_total": 11,
             "binding_complete": True},
            ("warn", "unsafe_11_of_11"),
        ),
        (
            {"state_roots": "incomplete", "binding_count": 3, "binding_total": 11,
             "binding_complete": False},
            ("warn", "incomplete_3_of_11"),
        ),
    ],
)
def test_doctor_a6_private_config_classification_is_not_update_admission(
    inspection: dict[str, object], expected: tuple[str, str],
) -> None:
    assert classify_a6_bindings_for_doctor(inspection) == expected


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"state_roots": "ready", "binding_count": True, "binding_total": 11,
         "binding_complete": False},
        {"state_roots": "ready", "binding_count": 11, "binding_total": 11,
         "binding_complete": False},
        {"state_roots": "absent", "binding_count": 0, "binding_total": 11,
         "binding_complete": True},
        {"state_roots": "ready", "binding_count": 11, "binding_total": 12,
         "binding_complete": True},
        {"state_roots": "private-secret", "binding_count": 11, "binding_total": 11,
         "binding_complete": True},
        {"state_roots": "ready", "binding_count": -1, "binding_total": 11,
         "binding_complete": False},
    ],
)
def test_doctor_a6_unknown_or_malformed_inspection_never_admits(
    bad: object,
) -> None:
    assert classify_a6_bindings_for_doctor(bad) == ("warn", "unavailable")


def test_doctor_reports_safe_absent_a6_but_no_false_green(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    env = config / "runner-mcp.env"
    env.write_text("UNRELATED_VALUE=keep\n", encoding="utf-8")
    env.chmod(0o600)
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    inspected = inspect_a6_binding_state(config_dir=config, state_root=state)
    assert classify_a6_bindings_for_doctor(inspected) == (
        "warn", "not_configured_0_of_11",
    )
    assert load_env_file(env) == {"UNRELATED_VALUE": "keep"}

@pytest.mark.parametrize("operation", ["requested", "inspect", "repair"])
def test_a6_state_parent_symlink_redirect_fails_without_private_writes(
    tmp_path: Path, operation: str,
) -> None:
    # The *leaf* is not a link: an earlier leaf-only test missed the redirect.
    from runner_mcp.fabric_a6_binding_repair import a6_state_requested

    config, genuine_state, environment = _private_runtime(tmp_path)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(tmp_path, target_is_directory=True)
    redirected = linked_parent / genuine_state.name
    assert redirected.is_dir() and not redirected.is_symlink()
    if operation == "requested":
        with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
            a6_state_requested(redirected)
    elif operation == "inspect":
        with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
            inspect_a6_binding_state(config_dir=config, state_root=redirected)
    else:
        with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
            repair_a6_qualification_binding(
                environment=environment,
                config_dir=config,
                state_root=redirected,
                fabric_revision="f" * 40,
            )
    assert load_env_file(config / "runner-mcp.env") == {"UNRELATED_VALUE": "keep"}
    assert environment == {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}


@pytest.mark.parametrize("operation", ["inspect", "repair"])
def test_a6_config_parent_symlink_redirect_fails_without_private_writes(
    tmp_path: Path, operation: str,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    linked_parent = tmp_path / "linked-config-parent"
    linked_parent.symlink_to(tmp_path, target_is_directory=True)
    redirected = linked_parent / config.name
    assert redirected.is_dir() and not redirected.is_symlink()
    if operation == "inspect":
        with pytest.raises(
            FabricA6BindingRepairError, match="fabric_a6_runtime_config_unavailable"
        ):
            inspect_a6_binding_state(config_dir=redirected, state_root=state)
    else:
        with pytest.raises(
            FabricA6BindingRepairError, match="fabric_a6_runtime_config_unavailable"
        ):
            repair_a6_qualification_binding(
                environment=environment,
                config_dir=redirected,
                state_root=state,
                fabric_revision="f" * 40,
            )
    assert load_env_file(config / "runner-mcp.env") == {"UNRELATED_VALUE": "keep"}
    assert environment == {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}


def test_a6_lexical_parent_traversal_is_not_canonical_private_root(
    tmp_path: Path,
) -> None:
    from runner_mcp.fabric_a6_binding_repair import a6_state_requested

    config, state, environment = _private_runtime(tmp_path)
    noncanonical = state / ".." / state.name
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        a6_state_requested(noncanonical)
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_state_unsafe"):
        repair_a6_qualification_binding(
            environment=environment, config_dir=config, state_root=noncanonical,
            fabric_revision="f" * 40,
        )
    assert load_env_file(config / "runner-mcp.env") == {"UNRELATED_VALUE": "keep"}
    assert environment == {"RUNNER_MCP_BEARER_TOKEN": "r" * 48}

@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("RUNNER_FABRIC_UPDATE_JOURNAL_ROOT", "/untrusted/a6"),
        ("RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN", "target:runner-mcp"),
        ("RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN", "control:evidence"),
        ("RUNNER_FABRIC_RUNNER_MCP_ENDPOINT", "http://127.0.0.1:8020/mcp"),
        ("RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN", "short"),
        ("RUNNER_FABRIC_SYNTHETIC_PROBE_ID", "other-probe"),
        ("RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT", "runner:primary"),
        ("RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION", "f" * 40),
        ("RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS", "0"),
        ("RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT", "/untrusted/evidence"),
        ("RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION", "f" * 40),
    ],
)
def test_doctor_a6_refuses_full_count_with_mismatched_private_fixed_value(
    tmp_path: Path, key: str, replacement: str,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    repair_a6_qualification_binding(
        environment=environment,
        config_dir=config,
        state_root=state,
        fabric_revision="a" * 40,
    )
    env_path = config / "runner-mcp.env"
    values = load_env_file(env_path)
    assert len([name for name in values if name.startswith("RUNNER_FABRIC_")]) == 11
    before = inspect_a6_binding_state(config_dir=config, state_root=state)
    assert before["binding_complete"] is True
    values[key] = replacement
    env_path.write_text(
        "".join(f"{name}={value}\n" for name, value in values.items()),
        encoding="utf-8",
    )
    env_path.chmod(0o600)
    inspected = inspect_a6_binding_state(config_dir=config, state_root=state)
    assert inspected["state_roots"] == "ready"
    assert inspected["binding_count"] == 11
    assert inspected["binding_complete"] is False
    assert classify_a6_bindings_for_doctor(inspected) == ("warn", "unavailable")


def test_doctor_a6_full_count_without_owner_private_roots_is_not_ready(
    tmp_path: Path,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    repair_a6_qualification_binding(
        environment=environment, config_dir=config, state_root=state,
        fabric_revision="a" * 40,
    )
    (state / "a6-evidence").rmdir()
    observed = inspect_a6_binding_state(config_dir=config, state_root=state)
    assert observed["state_roots"] == "incomplete"
    assert observed["binding_count"] == 11
    assert observed["binding_complete"] is False
    assert classify_a6_bindings_for_doctor(observed) == ("warn", "unavailable")


def test_doctor_a6_complete_fixed_values_still_not_physical_recovery_proof(
    tmp_path: Path,
) -> None:
    config, state, environment = _private_runtime(tmp_path)
    repair_a6_qualification_binding(
        environment=environment, config_dir=config, state_root=state,
        fabric_revision="a" * 40,
    )
    observed = inspect_a6_binding_state(config_dir=config, state_root=state)
    assert observed["binding_complete"] is True
    assert classify_a6_bindings_for_doctor(observed) == ("pass", "ready_11_of_11")
    # PASS here is confined to structural PRIVATE CONFIG ONLY; no assertion
    # about independent storage, A6 journal append, A7 or client ACK.


def _a6_fixed_parent_fixture(tmp_path: Path) -> Path:
    """Maak alleen een tijdelijke private eigenaar-root voor offline tests."""
    if os.name != "posix" or not hasattr(os, "geteuid"):
        pytest.skip("deze owner-private functie vereist Linux")
    if os.geteuid() == 0:
        pytest.skip("positieve private-owner-tests mogen niet als root draaien")
    root = tmp_path / "runner-fabric"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return root


def test_a6_fixed_pair_prepares_only_two_private_leaves(tmp_path: Path) -> None:
    root = _a6_fixed_parent_fixture(tmp_path)
    result = _prepare_fixed_a6_private_roots_under(root)
    assert result == {
        "state": "fixed_roots_prepared",
        "roots_private": True,
        "physical_independence_verified": False,
        "off_target_readback_verified": False,
        "journal_integrity_verified": False,
        "a6_ready": False,
        "mutation_authorized": False,
        "service_restarted": False,
    }
    assert {p.name for p in root.iterdir()} == {
        "a6-update-journal", "a6-evidence",
    }
    for name in ("a6-update-journal", "a6-evidence"):
        info = (root / name).lstat()
        assert stat.S_ISDIR(info.st_mode)
        assert info.st_uid == os.geteuid()
        assert stat.S_IMODE(info.st_mode) == 0o700
        assert list((root / name).iterdir()) == []


def test_a6_fixed_pair_adopts_existing_pair_without_writing(
    tmp_path: Path,
) -> None:
    root = _a6_fixed_parent_fixture(tmp_path)
    first = _prepare_fixed_a6_private_roots_under(root)
    before = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in root.iterdir()}
    second = _prepare_fixed_a6_private_roots_under(root)
    after = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in root.iterdir()}
    assert first["state"] == "fixed_roots_prepared"
    assert second["state"] == "already_private"
    assert before == after


def test_a6_fixed_pair_refuses_partial_without_repair(
    tmp_path: Path,
) -> None:
    root = _a6_fixed_parent_fixture(tmp_path)
    existing = root / "a6-update-journal"
    existing.mkdir(mode=0o700)
    before = existing.stat().st_ino
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_incomplete"):
        _prepare_fixed_a6_private_roots_under(root)
    assert existing.stat().st_ino == before
    assert not (root / "a6-evidence").exists()


@pytest.mark.parametrize("kind", ["symlink", "broad_mode", "regular_file"])
def test_a6_fixed_pair_refuses_unsafe_leaf_without_changes(
    tmp_path: Path, kind: str,
) -> None:
    root = _a6_fixed_parent_fixture(tmp_path)
    leaf = root / "a6-update-journal"
    if kind == "symlink":
        leaf.symlink_to(tmp_path, target_is_directory=True)
    elif kind == "broad_mode":
        leaf.mkdir(mode=0o700)
        leaf.chmod(0o755)
    else:
        leaf.write_text("do not replace", encoding="utf-8")
    before = tuple((p.name, p.lstat().st_ino) for p in root.iterdir())
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_denied"):
        _prepare_fixed_a6_private_roots_under(root)
    assert tuple((p.name, p.lstat().st_ino) for p in root.iterdir()) == before
    assert not (root / "a6-evidence").exists()


def test_a6_fixed_pair_refuses_redirected_or_missing_parent(
    tmp_path: Path,
) -> None:
    real = _a6_fixed_parent_fixture(tmp_path)
    alias = tmp_path / "root-alias"
    alias.symlink_to(real, target_is_directory=True)
    for root in (alias, tmp_path / "not-created"):
        with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_denied"):
            _prepare_fixed_a6_private_roots_under(root)
    assert list(real.iterdir()) == []


def test_a6_fixed_pair_interrupted_second_mkdir_remains_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _a6_fixed_parent_fixture(tmp_path)
    original_mkdir = os.mkdir

    def fail_second(name: object, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
        if name == "a6-evidence":
            raise OSError("synthetic second mkdir failure")
        original_mkdir(name, mode, dir_fd=dir_fd)

    with monkeypatch.context() as edits:
        edits.setattr(os, "mkdir", fail_second)
        with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_denied"):
            _prepare_fixed_a6_private_roots_under(root)
    assert {p.name for p in root.iterdir()} == {"a6-update-journal"}
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_incomplete"):
        _prepare_fixed_a6_private_roots_under(root)
    assert {p.name for p in root.iterdir()} == {"a6-update-journal"}


def test_a6_fixed_pair_operator_entrypoint_refuses_untrusted_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp import fabric_a6_binding_repair as repair

    monkeypatch.setattr(repair.socket, "gethostname", lambda: "not-original-black")
    with pytest.raises(FabricA6BindingRepairError, match="fabric_a6_root_prepare_denied"):
        prepare_black_a6_private_roots()
