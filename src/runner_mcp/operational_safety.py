from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SafetyConfigurationError(RuntimeError):
    pass


class OperatorStopActive(RuntimeError):
    pass


class ActionClass(StrEnum):
    READ_ONLY = "read_only"
    CANCEL = "cancel"
    TEST = "test"
    SERVICE = "service"
    BACKUP = "backup"
    MIGRATION = "migration"
    DEPLOY = "deploy"
    CODE_ROLLBACK = "code_rollback"
    DATABASE_RESTORE = "database_restore"


class RetentionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    min_releases_to_keep: int = Field(default=20, ge=2, le=1000)
    min_release_age_days: int = Field(default=90, ge=1, le=3650)
    pitr_retention_days: int = Field(default=30, ge=1, le=3650)
    pre_migration_backup_days: int = Field(default=180, ge=1, le=3650)
    max_automatic_code_rollback_steps: int = Field(default=1, ge=1, le=1)
    database_restore_requires_explicit_approval: bool = True
    automatic_production_database_restore: bool = False

    @field_validator("database_restore_requires_explicit_approval")
    @classmethod
    def require_database_restore_approval(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Database restore must require explicit approval")
        return value

    @field_validator("automatic_production_database_restore")
    @classmethod
    def prohibit_automatic_production_restore(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("Automatic production database restore is prohibited")
        return value

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> RetentionPolicy:
        def integer(name: str, default: int) -> int:
            raw = values.get(name, str(default))
            try:
                return int(raw)
            except ValueError as exc:
                raise SafetyConfigurationError(f"{name} must be an integer") from exc

        return cls(
            min_releases_to_keep=integer("RUNNER_MCP_MIN_RELEASES_TO_KEEP", 20),
            min_release_age_days=integer("RUNNER_MCP_MIN_RELEASE_DAYS", 90),
            pitr_retention_days=integer("RUNNER_MCP_PITR_RETENTION_DAYS", 30),
            pre_migration_backup_days=integer(
                "RUNNER_MCP_PRE_MIGRATION_BACKUP_DAYS",
                180,
            ),
        )

    @classmethod
    def from_env(cls) -> RetentionPolicy:
        return cls.from_mapping(os.environ)

    def release_is_deletable(
        self,
        *,
        release_rank_from_newest: int,
        deployed_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        if release_rank_from_newest < self.min_releases_to_keep:
            return False

        current = now or datetime.now(UTC)
        deployed = deployed_at if deployed_at.tzinfo else deployed_at.replace(tzinfo=UTC)
        age_days = (current - deployed.astimezone(UTC)).days
        return age_days >= self.min_release_age_days

    def pre_migration_backup_is_deletable(
        self,
        *,
        created_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(UTC)
        created = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
        age_days = (current - created.astimezone(UTC)).days
        return age_days >= self.pre_migration_backup_days


@dataclass(frozen=True)
class OperatorSafetyStatus:
    configured: bool
    stop_active: bool
    mode: str


class OperatorSafetyGuard:
    def __init__(
        self,
        stop_file: Path | None,
        retention: RetentionPolicy,
        *,
        retention_confirmed: bool = True,
    ) -> None:
        self.stop_file = stop_file
        self.retention = retention
        self.retention_confirmed = retention_confirmed

    @classmethod
    def from_env(cls, retention: RetentionPolicy) -> OperatorSafetyGuard:
        raw = os.getenv("RUNNER_MCP_OPERATOR_STOP_FILE", "").strip()
        stop_file = Path(raw) if raw else None
        confirmed = os.getenv("RUNNER_MCP_RETENTION_CONFIRMED", "").strip().lower()
        if confirmed not in {"", "true", "false"}:
            raise SafetyConfigurationError(
                "RUNNER_MCP_RETENTION_CONFIRMED must be true or false"
            )
        return cls(
            stop_file=stop_file,
            retention=retention,
            retention_confirmed=confirmed == "true",
        )

    def status(self) -> OperatorSafetyStatus:
        if not self.retention_confirmed:
            return OperatorSafetyStatus(
                configured=self.stop_file is not None,
                stop_active=self.stop_file.exists() if self.stop_file else False,
                mode="read_only_until_retention_is_confirmed",
            )

        if self.stop_file is None:
            return OperatorSafetyStatus(
                configured=False,
                stop_active=False,
                mode="read_only_until_operator_stop_is_configured",
            )

        active = self.stop_file.exists()
        return OperatorSafetyStatus(
            configured=True,
            stop_active=active,
            mode="read_only_emergency_stop" if active else "operational",
        )

    def assert_action_allowed(self, action: ActionClass) -> None:
        if action in {ActionClass.READ_ONLY, ActionClass.CANCEL}:
            return

        status = self.status()
        if not self.retention_confirmed:
            raise SafetyConfigurationError(
                "Retention policy must be explicitly confirmed before operator actions are enabled"
            )
        if not status.configured:
            raise SafetyConfigurationError(
                "Operator stop mechanism must be configured before operator actions are enabled"
            )
        if status.stop_active:
            raise OperatorStopActive("Operator emergency stop is active")

    def assert_code_rollback_steps(self, steps: int) -> None:
        if steps != 1:
            raise SafetyConfigurationError(
                "A code rollback may move only one release per approved action"
            )

    @staticmethod
    def assert_database_restore_approved(*, explicit_approval: bool) -> None:
        if not explicit_approval:
            raise SafetyConfigurationError(
                "Database restore requires explicit human approval"
            )
