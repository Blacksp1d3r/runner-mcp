from __future__ import annotations

from pathlib import Path

from .base import (
    AdapterPresetError,
    MigrationPresetRecipe,
    ProjectAdapter,
    TestPresetRecipe,
)
from .generic import GenericAdapter
from .python import PythonAdapter


class AdapterError(RuntimeError):
    pass


_ADAPTERS: dict[str, ProjectAdapter] = {
    "generic": GenericAdapter(),
    "python": PythonAdapter(),
}


def adapter_ids() -> tuple[str, ...]:
    return tuple(sorted(_ADAPTERS))


def get_adapter(adapter_id: str) -> ProjectAdapter:
    adapter = _ADAPTERS.get(adapter_id)
    if adapter is None:
        raise AdapterError("Unknown or disabled project adapter")
    return adapter


def list_adapters() -> list[dict[str, object]]:
    return [
        _ADAPTERS[adapter_id].info.public_dict()
        for adapter_id in sorted(_ADAPTERS)
    ]


def inspect_project(adapter_id: str, root: Path) -> dict[str, object]:
    return get_adapter(adapter_id).inspect(root)


def _preset_owner(preset: str, *, kind: str) -> ProjectAdapter:
    if preset == "custom":
        raise AdapterError("Custom presets are configured explicitly")
    matches = []
    for adapter in _ADAPTERS.values():
        presets = (
            adapter.info.test_presets
            if kind == "test"
            else adapter.info.migration_presets
        )
        if preset in presets:
            matches.append(adapter)
    if not matches:
        raise AdapterError(f"Unknown {kind} preset")
    if len(matches) != 1:
        raise AdapterError(f"Ambiguous {kind} preset")
    return matches[0]


def materialize_test_preset(
    root: Path,
    preset: str,
    arguments: tuple[str, ...] = (),
) -> TestPresetRecipe:
    adapter = _preset_owner(preset, kind="test")
    try:
        return adapter.materialize_test_preset(root, preset, arguments)
    except AdapterPresetError as exc:
        raise AdapterError(str(exc)) from exc


def materialize_migration_preset(
    root: Path,
    preset: str,
) -> MigrationPresetRecipe:
    adapter = _preset_owner(preset, kind="migration")
    try:
        return adapter.materialize_migration_preset(root, preset)
    except AdapterPresetError as exc:
        raise AdapterError(str(exc)) from exc
