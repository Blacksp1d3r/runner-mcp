from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class AdapterInfo:
    adapter_id: str
    display_name: str
    test_presets: tuple[str, ...]
    migration_presets: tuple[str, ...]
    supports_services: bool = True
    supports_deployment: bool = True

    def public_dict(self) -> dict[str, object]:
        return {
            "id": self.adapter_id,
            "name": self.display_name,
            "test_presets": list(self.test_presets),
            "migration_presets": list(self.migration_presets),
            "supports_services": self.supports_services,
            "supports_deployment": self.supports_deployment,
        }


class ProjectAdapter(Protocol):
    info: AdapterInfo

    def inspect(self, root: Path) -> dict[str, object]: ...

    def default_test_preset(self, root: Path) -> str | None: ...

    def default_migration_preset(self, root: Path) -> str | None: ...
