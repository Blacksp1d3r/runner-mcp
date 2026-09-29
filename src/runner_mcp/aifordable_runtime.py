from __future__ import annotations

import os
import stat
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from .aifordable_results import (
    AIfordableDurableResult,
    AIfordableResultStore,
    AIfordableResultStoreError,
    AIfordableTerminalAction,
)
from .aifordable_transport import (
    AIFORDABLE_RELAY_ENV_KEYS,
    AIfordableClaim,
    AIfordableControlOperation,
    AIfordableRelayClient,
    AIfordableRelayConfig,
    AIfordableTransportError,
    reconnect_delay_seconds,
)
from .bridge_mcp_executor import LocalMCPBridgeExecutor, LocalMCPConfig
from .bridge_processor import BridgeExecutionAdapterError
from .onboarding import OnboardingError, load_env_file, read_private_runtime

DEFAULT_IDLE_SLEEP_SECONDS = 1.0
_MAX_IDLE_SLEEP_SECONDS = 60.0


class AIfordableWatcherRuntimeError(RuntimeError):
    """Safe primary-control runtime failure without private configuration detail."""


class AIfordableWatcherState(StrEnum):
    IDLE = "idle"
    COMPLETED = "completed"
    REPLAYED = "replayed"
    DEFERRED = "deferred"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True, slots=True)
class AIfordableWatcherOutcome:
    state: AIfordableWatcherState
    request_id: str | None = None
    operation: AIfordableControlOperation | None = None


class RuntimeExecutor(Protocol):
    def runtime_status(self) -> Any: ...

    def runtime_doctor(self) -> Any: ...


@dataclass(slots=True)
class AIfordableWatcherRuntime:
    relay: AIfordableRelayClient
    executor: RuntimeExecutor
    results: AIfordableResultStore
    subject: str

    @classmethod
    def from_private_config(
        cls,
        config_dir: Path,
    ) -> AIfordableWatcherRuntime:
        try:
            paths, settings, _registry = read_private_runtime(config_dir)
            values = load_env_file(paths.env_file)
        except (OnboardingError, RuntimeError, ValueError, OSError) as exc:
            raise AIfordableWatcherRuntimeError(
                "Runner MCP private runtime configuration is unavailable"
            ) from exc

        if any(not values.get(key, "").strip() for key in AIFORDABLE_RELAY_ENV_KEYS):
            raise AIfordableWatcherRuntimeError(
                "AIfordable relay private configuration is incomplete"
            )

        try:
            relay_config = AIfordableRelayConfig.from_mapping(values)
            local_config = LocalMCPConfig(
                endpoint=settings.resource_url,
                bearer_token=settings.bearer_token,
            )
        except ValueError as exc:
            raise AIfordableWatcherRuntimeError(
                "AIfordable relay private configuration is invalid"
            ) from exc

        result_root = paths.config_dir / "aifordable-results"
        _ensure_private_directory(result_root)

        return cls(
            relay=AIfordableRelayClient(relay_config),
            executor=LocalMCPBridgeExecutor(local_config),
            results=AIfordableResultStore(result_root),
            subject=relay_config.subject,
        )

    def run_once(self, *, now: int | None = None) -> AIfordableWatcherOutcome:
        epoch = int(time.time()) if now is None else now
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
            raise ValueError("now must be a non-negative integer")

        pending = self.results.pending()
        stale_pending: AIfordableDurableResult | None = None
        if pending:
            if len(pending) > 1:
                return AIfordableWatcherOutcome(
                    state=AIfordableWatcherState.RECOVERY_REQUIRED
                )
            stored = pending[0]
            try:
                self._send_stored(stored)
            except AIfordableTransportError as exc:
                if exc.status != 409:
                    return AIfordableWatcherOutcome(
                        state=AIfordableWatcherState.DEFERRED,
                        request_id=stored.request_id,
                    )
                stale_pending = stored
            else:
                self.results.acknowledge(
                    stored.request_id,
                    stored.fingerprint,
                )
                return AIfordableWatcherOutcome(
                    state=AIfordableWatcherState.REPLAYED,
                    request_id=stored.request_id,
                )

        claim = self.relay.claim_once(now=epoch)
        if claim is None:
            return AIfordableWatcherOutcome(
                state=(
                    AIfordableWatcherState.DEFERRED
                    if stale_pending is not None
                    else AIfordableWatcherState.IDLE
                ),
                request_id=(
                    stale_pending.request_id
                    if stale_pending is not None
                    else None
                ),
            )

        if stale_pending is not None and claim.envelope.request_id != stale_pending.request_id:
            return AIfordableWatcherOutcome(
                state=AIfordableWatcherState.RECOVERY_REQUIRED,
                request_id=stale_pending.request_id,
            )

        existing = self.results.get(claim.envelope.request_id)
        if existing is not None:
            if existing.fingerprint != claim.fingerprint:
                return AIfordableWatcherOutcome(
                    state=AIfordableWatcherState.RECOVERY_REQUIRED,
                    request_id=claim.envelope.request_id,
                    operation=claim.envelope.operation,
                )
            rebound = AIfordableDurableResult(
                request_id=existing.request_id,
                fingerprint=existing.fingerprint,
                relay_version=claim.version,
                owner_generation=claim.owner_generation,
                action=existing.action,
                result_code=existing.result_code,
                result_payload=existing.result_payload,
            )
            self.results.put(rebound)
            return self._deliver(
                claim,
                rebound,
                success_state=AIfordableWatcherState.REPLAYED,
            )

        produced = self._execute_read_only(claim)
        try:
            durable = self.results.put(produced)
        except AIfordableResultStoreError as exc:
            raise AIfordableWatcherRuntimeError(
                "AIfordable control result could not be persisted safely"
            ) from exc

        return self._deliver(
            claim,
            durable,
            success_state=AIfordableWatcherState.COMPLETED,
        )

    def _execute_read_only(
        self,
        claim: AIfordableClaim,
    ) -> AIfordableDurableResult:
        operation = claim.envelope.operation

        if operation in {
            AIfordableControlOperation.FABRIC_RUN_WORK_UNIT,
            AIfordableControlOperation.FABRIC_GET_WORK_UNIT,
            AIfordableControlOperation.FABRIC_CANCEL_WORK_UNIT,
        }:
            return self._result(
                claim,
                action=AIfordableTerminalAction.FAIL,
                code="fabric_control_reserved",
                payload={"reason": "fabric_control_reserved"},
            )

        try:
            if operation is AIfordableControlOperation.RUNTIME_STATUS:
                raw_result = self.executor.runtime_status()
            elif operation is AIfordableControlOperation.RUNTIME_DOCTOR:
                raw_result = self.executor.runtime_doctor()
            else:
                raise AIfordableWatcherRuntimeError(
                    "AIfordable control operation is unsupported"
                )
        except BridgeExecutionAdapterError:
            return self._result(
                claim,
                action=AIfordableTerminalAction.FAIL,
                code="execution_failed",
                payload={"reason": "execution_failed"},
            )

        try:
            return self._result(
                claim,
                action=AIfordableTerminalAction.COMPLETE,
                code="ok",
                payload={"result": raw_result},
            )
        except AIfordableResultStoreError:
            return self._result(
                claim,
                action=AIfordableTerminalAction.FAIL,
                code="unsafe_result",
                payload={"reason": "unsafe_result"},
            )

    @staticmethod
    def _result(
        claim: AIfordableClaim,
        *,
        action: AIfordableTerminalAction,
        code: str,
        payload: dict[str, object],
    ) -> AIfordableDurableResult:
        return AIfordableDurableResult(
            request_id=claim.envelope.request_id,
            fingerprint=claim.fingerprint,
            relay_version=claim.version,
            owner_generation=claim.owner_generation,
            action=action,
            result_code=code,
            result_payload=payload,
        )

    def _deliver(
        self,
        claim: AIfordableClaim,
        result: AIfordableDurableResult,
        *,
        success_state: AIfordableWatcherState,
    ) -> AIfordableWatcherOutcome:
        try:
            self._send_stored(result)
        except AIfordableTransportError:
            return AIfordableWatcherOutcome(
                state=AIfordableWatcherState.DEFERRED,
                request_id=result.request_id,
                operation=claim.envelope.operation,
            )

        self.results.acknowledge(
            result.request_id,
            result.fingerprint,
        )
        return AIfordableWatcherOutcome(
            state=success_state,
            request_id=result.request_id,
            operation=claim.envelope.operation,
        )

    def _send_stored(self, result: AIfordableDurableResult) -> None:
        self.relay.submit_terminal_result(
            request_id=result.request_id,
            expected_version=result.relay_version,
            owner_generation=result.owner_generation,
            action=result.action.value,
            result_code=result.result_code,
            result_payload=result.result_payload,
        )

    def run_forever(
        self,
        *,
        idle_sleep_seconds: float = DEFAULT_IDLE_SLEEP_SECONDS,
    ) -> None:
        if (
            isinstance(idle_sleep_seconds, bool)
            or not isinstance(idle_sleep_seconds, (int, float))
            or not 0.1 <= float(idle_sleep_seconds) <= _MAX_IDLE_SLEEP_SECONDS
        ):
            raise ValueError("idle sleep interval is outside the supported range")

        failure_count = 0
        while True:
            try:
                outcome = self.run_once()
            except AIfordableTransportError:
                failure_count += 1
                time.sleep(reconnect_delay_seconds(failure_count))
                continue

            failure_count = 0
            if outcome.state in {
                AIfordableWatcherState.IDLE,
                AIfordableWatcherState.DEFERRED,
            }:
                time.sleep(float(idle_sleep_seconds))
            elif outcome.state is AIfordableWatcherState.RECOVERY_REQUIRED:
                raise AIfordableWatcherRuntimeError(
                    "AIfordable watcher recovery is required"
                )


def _ensure_private_directory(path: Path) -> None:
    if path.exists() and path.is_symlink():
        raise AIfordableWatcherRuntimeError(
            "AIfordable result directory is unsafe"
        )
    try:
        path.mkdir(mode=0o700, parents=False, exist_ok=True)
        os.chmod(path, 0o700)
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise AIfordableWatcherRuntimeError(
            "AIfordable result directory is unavailable"
        ) from exc
    if not path.is_dir() or path.is_symlink() or mode != 0o700:
        raise AIfordableWatcherRuntimeError(
            "AIfordable result directory is unsafe"
        )
