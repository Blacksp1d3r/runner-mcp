"""Provision fixed private authority for one Bewind OCR qualification run."""

from __future__ import annotations

import json
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from .fabric_worker_qualification_provisioning import (
    FabricWorkerQualificationProvisioningError,
    _merge_private_env,
)
from .operational_safety import ActionClass, OperatorSafetyGuard

_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_GENERATION = 1
_FABRIC_REVISION = "be71bd95c60ad858ab1878fe1c8e662a0b6ffddc"
_BEWIND_REVISION = "cf16b9e7481bdb56b8c308ff29c6f305cd1a0a48"
_EXECUTION_ENV = "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON"
_SCHEMA = "runner-mcp/bewind-ocr-qualification-execution/v1"
_RESULT_SCHEMA = "runner-mcp/bewind-ocr-qualification-execution-authority/v1"


class BewindOcrQualificationExecutionAuthorityError(RuntimeError):
    """Sanitized fixed execution-authority provisioning failure."""


class BewindOcrQualificationExecutionAuthorityConfigurator:
    """Persist and activate exactly one fixed OCR qualification authority."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: MutableMapping[str, str],
        config_dir: Path,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()

    def configure(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)

        payload = {
            "schemaVersion": _SCHEMA,
            "worker_id": _WORKER_ID,
            "capability_profile": _CAPABILITY,
            "generation": _GENERATION,
            "fabric_revision": _FABRIC_REVISION,
            "bewind_revision": _BEWIND_REVISION,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        env_path = self.config_dir / "runner-mcp.env"
        try:
            _merge_private_env(env_path, {_EXECUTION_ENV: encoded})
        except FabricWorkerQualificationProvisioningError as exc:
            raise BewindOcrQualificationExecutionAuthorityError(
                "bewind OCR qualification execution authority could not be persisted"
            ) from exc

        self.environment[_EXECUTION_ENV] = encoded
        return {
            "schemaVersion": _RESULT_SCHEMA,
            "state": "configured",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "generation": _GENERATION,
            "fabricRevision": _FABRIC_REVISION,
            "bewindRevision": _BEWIND_REVISION,
            "normalActivationEnabled": False,
        }
