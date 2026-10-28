from __future__ import annotations

from pathlib import Path
from types import CodeType, FunctionType, ModuleType

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


@pytest.mark.parametrize("bad", (None, "", "private\nvalue", "x" * 65, 0, True))
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


def _loaded_modules(
    code: str = "def active():\n    return 42\n",
    *,
    filename: str = "/private/host/secret-original.py",
) -> dict[str, object]:
    """Minimal real in-memory code objects, with no wheel-file reading."""
    modules = _roster()
    for name in ("runner_mcp.server", "runner_mcp.build_identity"):
        module = modules[name]
        assert isinstance(module, ModuleType)
        module.__dict__["__name__"] = name
        function_code = next(
            constant for constant in compile(code, filename, "exec").co_consts
            if type(constant) is CodeType and constant.co_name == "active"
        )
        module.__dict__["active"] = FunctionType(function_code, module.__dict__)
    return modules


def test_actual_imported_code_fingerprint_is_bounded_and_not_build_provenance() -> None:
    result = _check(modules=_loaded_modules())
    assert result["loadedCodeObservationSchema"] == "runner-mcp/selected-loaded-code-objects/v1"
    assert result["loadedCodeObservationComplete"] is True
    assert result["loadedCodeModuleCount"] == 2
    assert result["loadedCodeObjectCount"] == 2
    assert len(result["loadedCodeObjectDigest"]) == 64
    assert result["state"] == "observed_local_only"
    _never_live_authority(result)


def test_replacing_on_disk_source_does_not_change_already_loaded_code(
    tmp_path: Path,
) -> None:
    original = tmp_path / "live.py"
    original.write_text("def active():\n    return 42\n", encoding="utf-8")
    modules = _loaded_modules(original.read_text(encoding="utf-8"), filename=str(original))
    before = _check(modules=modules)
    original.write_text("def active():\n    return 9001\n", encoding="utf-8")
    after = _check(modules=modules)
    assert before["loadedCodeObjectDigest"] == after["loadedCodeObjectDigest"]
    assert after["loadedCodeObservationComplete"] is True
    assert after["activeBuildProvenanceVerified"] is False


def test_in_memory_code_changes_even_when_package_versions_do_not() -> None:
    modules = _loaded_modules()
    before = _check(modules=modules)
    changed = _loaded_modules("def active():\n    return 9001\n")
    after = _check(modules=changed)
    assert before["loadedCodeObjectDigest"] != after["loadedCodeObjectDigest"]
    assert before["loadedVersionMatchesInstalled"] is True
    assert after["loadedVersionMatchesInstalled"] is True
    _never_live_authority(after)


def test_filename_redaction_is_recursive_and_does_not_leak_paths() -> None:
    body = "def active():\n    def child():\n        return 42\n    return child()\n"
    one = _check(modules=_loaded_modules(body, filename="/secret/one.py"))
    two = _check(modules=_loaded_modules(body, filename="/secret/two.py"))
    assert one["loadedCodeObjectDigest"] == two["loadedCodeObjectDigest"]
    assert "secret" not in str(one)
    _never_live_authority(two)


def test_missing_code_objects_cannot_be_misreported_as_measured() -> None:
    result = _check()
    assert result["loadedCodeObjectDigest"] is None
    assert result["loadedCodeObservationComplete"] is False
    assert result["loadedCodeModuleCount"] == 0
    _never_live_authority(result)


def test_code_version_mismatch_does_not_yield_fingerprint() -> None:
    mismatch = _check(loaded="0.1.38", installed="0.1.55", modules=_loaded_modules())
    assert mismatch["loadedCodeObjectDigest"] is None
    assert mismatch["loadedCodeObservationComplete"] is False
    _never_live_authority(mismatch)


def test_no_module_source_paths_or_private_values_returned() -> None:
    mods = _roster()
    mods["runner_mcp.server"].__file__ = "/private/SECRETVALUE/server.py"
    result = _check(modules=mods)
    assert "SECRETVALUE" not in str(result)
    _never_live_authority(result)
