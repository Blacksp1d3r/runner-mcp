from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from .bridge_protocol import (
    BridgeAction,
    BridgeProtocolError,
    BridgeRequest,
    BridgeResult,
    BridgeResultState,
    parse_bridge_request,
    serialize_bridge_result,
)
from .bridge_replay import (
    BridgeReplayError,
    BridgeReplayLedger,
    ReplayDecision,
    ReplayState,
)


class BridgeExecutionAdapterError(RuntimeError):
    """Safe adapter boundary error; message is never published."""


class BridgeResultSinkError(RuntimeError):
    """Safe durable-result transport boundary error; message is never published."""


class BridgeExecutor(Protocol):
    """Explicit allow-listed execution surface for the mailbox processor."""

    def list_projects(self) -> Any: ...

    def safety_status(self) -> Any: ...

    def project_status(self, project: str) -> Any: ...

    def project_capabilities(self, project: str) -> Any: ...

    def list_test_profiles(self, project: str) -> Any: ...

    def run_tests(self, project: str, suite: str) -> Any: ...

    def queue_status(self) -> Any: ...

    def worker_status(self) -> Any: ...

    def job_status(self, job_id: str) -> Any: ...

    def cancel_job(self, job_id: str) -> Any: ...


class BridgeResultSink(Protocol):
    """Transport-specific durable result writer."""

    def persist_result(self, request_id: str, result_json: str) -> None: ...


class BridgeProcessState(StrEnum):
    COMPLETED = "completed"
    ALREADY_COMPLETED = "already_completed"
    AMBIGUOUS = "ambiguous"
    PERSISTENCE_FAILED = "persistence_failed"
    FINALIZE_FAILED = "finalize_failed"


@dataclass(frozen=True, slots=True)
class BridgeProcessOutcome:
    request_id: str
    action: BridgeAction
    state: BridgeProcessState
    serialized_result: str | None = None

    @property
    def requires_recovery(self) -> bool:
        return self.state in {
            BridgeProcessState.AMBIGUOUS,
            BridgeProcessState.PERSISTENCE_FAILED,
            BridgeProcessState.FINALIZE_FAILED,
        }


class BridgeProcessor:
    """Transport-neutral request processor with replay-safe lifecycle ordering."""

    def __init__(
        self,
        *,
        ledger: BridgeReplayLedger,
        executor: BridgeExecutor,
        result_sink: BridgeResultSink,
    ) -> None:
        self._ledger = ledger
        self._executor = executor
        self._result_sink = result_sink

    def process(self, payload: str | bytes) -> BridgeProcessOutcome:
        request = parse_bridge_request(payload)
        claim = self._ledger.claim(request)

        if claim.decision == ReplayDecision.DUPLICATE:
            if claim.state == ReplayState.COMPLETED:
                return BridgeProcessOutcome(
                    request_id=request.request_id,
                    action=request.action,
                    state=BridgeProcessState.ALREADY_COMPLETED,
                )
            return BridgeProcessOutcome(
                request_id=request.request_id,
                action=request.action,
                state=BridgeProcessState.AMBIGUOUS,
            )

        result_json = self._execute_to_safe_result(request)

        try:
            self._result_sink.persist_result(request.request_id, result_json)
        except BridgeResultSinkError:
            return BridgeProcessOutcome(
                request_id=request.request_id,
                action=request.action,
                state=BridgeProcessState.PERSISTENCE_FAILED,
                serialized_result=result_json,
            )

        try:
            self._ledger.complete(request)
        except BridgeReplayError:
            return BridgeProcessOutcome(
                request_id=request.request_id,
                action=request.action,
                state=BridgeProcessState.FINALIZE_FAILED,
                serialized_result=result_json,
            )

        return BridgeProcessOutcome(
            request_id=request.request_id,
            action=request.action,
            state=BridgeProcessState.COMPLETED,
            serialized_result=result_json,
        )

    def _execute_to_safe_result(self, request: BridgeRequest) -> str:
        try:
            raw_result = self._execute(request)
        except BridgeExecutionAdapterError:
            return self._serialize_failure(
                request,
                error_code="EXECUTION_FAILED",
                summary="The allow-listed Runner MCP action failed",
            )

        success = BridgeResult(
            request_id=request.request_id,
            action=request.action,
            state=BridgeResultState.COMPLETED,
            data={"result": raw_result},
        )
        try:
            return serialize_bridge_result(success)
        except BridgeProtocolError:
            return self._serialize_failure(
                request,
                error_code="UNSAFE_RESULT",
                summary="Runner MCP returned a result that cannot be published safely",
            )

    def _execute(self, request: BridgeRequest) -> Any:
        if request.action == BridgeAction.LIST_PROJECTS:
            return self._executor.list_projects()

        if request.action == BridgeAction.SAFETY_STATUS:
            return self._executor.safety_status()

        if request.action == BridgeAction.PROJECT_STATUS:
            assert request.project is not None
            return self._executor.project_status(request.project)

        if request.action == BridgeAction.PROJECT_CAPABILITIES:
            assert request.project is not None
            return self._executor.project_capabilities(request.project)

        if request.action == BridgeAction.LIST_TEST_PROFILES:
            assert request.project is not None
            return self._executor.list_test_profiles(request.project)

        if request.action == BridgeAction.RUN_TESTS:
            assert request.project is not None
            assert request.profile is not None
            return self._executor.run_tests(request.project, request.profile)

        if request.action == BridgeAction.QUEUE_STATUS:
            return self._executor.queue_status()

        if request.action == BridgeAction.WORKER_STATUS:
            return self._executor.worker_status()

        if request.action == BridgeAction.JOB_STATUS:
            assert request.job_id is not None
            return self._executor.job_status(request.job_id)

        if request.action == BridgeAction.CANCEL_JOB:
            assert request.job_id is not None
            return self._executor.cancel_job(request.job_id)

        raise BridgeProtocolError("unsupported bridge action")

    def _serialize_failure(
        self,
        request: BridgeRequest,
        *,
        error_code: str,
        summary: str,
    ) -> str:
        result = BridgeResult(
            request_id=request.request_id,
            action=request.action,
            state=BridgeResultState.FAILED,
            error_code=error_code,
            summary=summary,
        )
        return serialize_bridge_result(result)
