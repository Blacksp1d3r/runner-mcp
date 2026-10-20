from __future__ import annotations

from types import ModuleType

import pytest

from runner_mcp.serving_process_readonly import observe_current_process_modules


def _roster(imported_version: object = "0.1.55") -> dict[str, object]:
    package = ModuleType("runner_mcp")
    package.__version__ = imported_version
    return {
        "runner_mcp": package,
        "runner_mcp.server": ModuleType("runner_mcp.server"),
        "runner_mcp.build_identity": ModuleType("runner_mcp.build_identity"),
    }


def _check(
    *, loaded: object = "0.1.55", installed: object = "0.1.55",
    modules: object = None,
) -> dict[str, object]:
    return observe_current_process_modules(
        imported_version=loaded,
        installed_distribution_version=installed,
        modules=_roster(loaded) if modules is None else modules,
    )


def _never_live_authority(result: dict[str, object]) -> None:
    assert result["scope"] == "this_connected_process_only"
    assert result["activeBuildProvenanceVerified"] is False
    assert result["sourceRevision"] is None
    assert result["artifactDigest"] is None
    assert result["selfUpdateReady"] is False
    assert result["updateAuthorized"] is False
    assert result["dispatchAuthorized"] is False
    assert "host" not in result
    assert "path" not in result
    assert "pid" not in result


def test_same_process_roster_is_not_an_attestation() -> None:
    result = _check()
    assert result["state"] == "observed_local_only"
    assert result["reasonCode"] == "current_module_roster_observed_only"
    assert result["moduleRosterCount"] == 3
    assert result["moduleRosterComplete"] is True
    assert result["loadedVersionMatchesPackage"] is True
    assert result["loadedVersionMatchesInstalled"] is True
    _never_live_authority(result)


@pytest.mark.parametrize("missing", (
    "runner_mcp", "runner_mcp.server", "runner_mcp.build_identity"
))
def test_missing_imported_module_is_not_fleet_proof(missing: str) -> None:
    modules = _roster()
    modules.pop(missing)
    result = _check(modules=modules)
    assert result["state"] == "wait"
    assert result["reasonCode"] == "incomplete_local_module_roster"
    assert result["moduleRosterCount"] == 2
    _never_live_authority(result)


def test_wrong_module_object_cannot_fake_roster() -> None:
    modules = _roster()
    modules["runner_mcp.server"] = {"__name__": "runner_mcp.server"}
    result = _check(modules=modules)
    assert result["state"] == "wait"
    _never_live_authority(result)


def test_imported_old_code_after_new_dist_info_is_explicit_mismatch() -> None:
    result = _check(loaded="0.1.38", installed="0.1.55")
    assert result["state"] == "wait"
    assert result["reasonCode"] == "loaded_vs_installed_version_mismatch"
    assert result["moduleRosterComplete"] is True
    assert result["loadedVersionMatchesInstalled"] is False
    _never_live_authority(result)


def test_mutated_package_version_is_not_accepted() -> None:
    modules = _roster()
    modules["runner_mcp"].__version__ = "0.1.30"
    result = _check(modules=modules)
    assert result["reasonCode"] == "imported_package_version_mismatch"
    assert result["state"] == "wait"
    _never_live_authority(result)


@pytest.mark.parametrize("bad", (None, "", "private\\nvalue", "x" * 65, 0, True))
def test_untrusted_version_field_stays_wait_without_leak(bad: object) -> None:
    result = _check(installed=bad)
    assert result["state"] == "wait"
    assert result["reasonCode"] == "invalid_version_input"
    _never_live_authority(result)


def test_missing_or_malformed_roster_does_not_forge_processes() -> None:
    result = _check(modules={})
    assert result["moduleRosterCount"] == 0
    assert result["state"] == "wait"
    _never_live_authority(result)


def test_no_module_source_paths_or_private_values_returned() -> None:
    mods = _roster()
    mods["runner_mcp.server"].__file__ = "/private/SECRETVALUE/server.py"
    result = _check(modules=mods)
    assert "SECRETVALUE" not in str(result)
    _never_live_authority(result)
