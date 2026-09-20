from pathlib import Path

from .base import AdapterInfo


class GenericAdapter:
    info = AdapterInfo(
        adapter_id="generic",
        display_name="Generic project",
        test_presets=("custom",),
        migration_presets=("custom",),
    )

    def inspect(self, root: Path) -> dict[str, object]:
        return {
            "adapter": self.info.adapter_id,
            "project_root_available": root.exists() and root.is_dir() and not root.is_symlink(),
            "automatic_test_preset": None,
            "automatic_migration_preset": None,
        }

    def default_test_preset(self, root: Path) -> str | None:
        return None

    def default_migration_preset(self, root: Path) -> str | None:
        return None
