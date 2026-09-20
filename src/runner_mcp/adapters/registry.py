from __future__ import annotations

from pathlib import Path

from .base import ProjectAdapter
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
