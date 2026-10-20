from pathlib import Path

import pytest

from runner_mcp.fabric_a6_binding_repair import (
    FabricA6BindingRepairError,
    classify_a6_bindings_for_doctor,
    inspect_a6_binding_state,
    repair_a6_qualification_binding,
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


