from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import ProjectRegistry
from .source_control import clean_head


def migration_plan_material(
    registry: ProjectRegistry,
    project: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the canonical migration approval/revalidation material."""
    config = registry.projects.get(project)
    if config is None:
        raise ValueError("Unknown or disabled project")
    if config.environment != "staging":
        raise ValueError("Mutating project actions are enabled only for staging environments")
    if config.database is None or config.database.migrations is None:
        raise ValueError("Migration profile is not configured")

    source = clean_head(config.root)
    binding = {
        "environment": config.environment,
        "repository": config.repository,
        "database": config.database.model_dump(mode="json"),
        "source": source,
    }
    summary = {
        "action": "migration",
        "environment": config.environment,
        "commit": source["commit"],
        "pre_migration_backup_required": True,
        "automatic_database_restore": False,
    }
    return binding, summary


def migration_binding_fingerprint(binding: dict[str, Any]) -> str:
    encoded = json.dumps(
        binding,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
