from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from .bridge_mcp_executor import LocalMCPClient, LocalMCPConfig
from .bridge_processor import BridgeExecutionAdapterError

_FABRIC_TOOLS = frozenset(
    {
        "host_inspect",
        "external_target_preflight",
        "external_target_inspect",
        "operational_snapshot",
        "run_work_unit",
        "get_work_unit",
        "cancel_work_unit",
        "ci_runner_guest_status",
        "ci_runner_guest_enroll",
        "ci_runner_guest_start",
        "ci_runner_guest_stop",
    }
)
_ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_STATES = {"complete", "blocked", "failed"}
_STATUSES = {"running", "cancel_requested", "complete", "blocked", "failed"}
_STAGES = {"reconcile", "modify", "validate", "commit", "push", "report"}
_OUTCOMES = {"success", "blocked", "failed"}
_CHECKPOINTS = {"preflight", "pre_commit", "pre_push"}
_HANDOFF_RE = re.compile(r"^[0-9a-f]{32}$")
_CI_GUEST_STATES = {
    "ready",
    "registered",
    "running",
    "stopped",
    "blocked",
    "recovery_required",
}
_CI_GUEST_OPERATIONS = {"status", "enroll", "start", "stop"}


class FabricBridgeError(RuntimeError):
    """Safe Fabric bridge failure without endpoint/token/provider detail."""


@dataclass(frozen=True, slots=True)
class FabricBridgeConfig:
    endpoint: str
    bearer_token: str
    request_timeout_seconds: float = 120.0

    def __post_init__(self) -> None:
        if not isinstance(self.bearer_token, str) or len(self.bearer_token) < 32:
            raise ValueError("Runner Fabric bearer token must contain at least 32 characters")

    def to_mcp_config(self) -> LocalMCPConfig:
        return LocalMCPConfig(
            endpoint=self.endpoint,
            bearer_token=self.bearer_token,
            request_timeout_seconds=self.request_timeout_seconds,
        )


class FabricBridgeClient:
    """Fixed bounded proxy to a loopback Runner Fabric MCP endpoint."""

    def __init__(self, config: FabricBridgeConfig) -> None:
        if not isinstance(config, FabricBridgeConfig):
            raise TypeError("config must be FabricBridgeConfig")
        self._mcp_config = config.to_mcp_config()
        self._local = threading.local()


    def host_inspect(self) -> dict[str, Any]:
        """Return bounded read-only Runner Fabric host/browser inspection."""

        try:
            result = self._client()._call_tool("host_inspect", {})
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError("Runner Fabric host inspection failed") from exc
        return _validate_host_inspection(result)

    def external_target_preflight(self) -> dict[str, Any]:
        """Return bounded config-only external-target preflight state."""

        try:
            result = self._client()._call_tool("external_target_preflight", {})
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError("Runner Fabric external target preflight failed") from exc
        return _validate_external_target_preflight(result)

    def external_target_inspect(self) -> dict[str, Any]:
        """Return bounded read-only external-target HTTPS qualification."""

        try:
            result = self._client()._call_tool("external_target_inspect", {})
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError("Runner Fabric external target inspection failed") from exc
        return _validate_external_target_inspection(result)

    def operational_snapshot(self) -> dict[str, Any]:
        """Return bounded read-only end-to-end operational state."""

        try:
            result = self._client()._call_tool("operational_snapshot", {})
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError(
                "Runner Fabric operational snapshot failed"
            ) from exc
        return _validate_operational_snapshot(result)

    def ci_runner_guest_status(self) -> dict[str, Any]:
        """Return bounded isolated CI guest state."""

        return self._call_ci_guest("ci_runner_guest_status", {})

    def ci_runner_guest_enroll(self, handoff_id: str) -> dict[str, Any]:
        """Enroll the isolated CI guest using one opaque handoff ID."""

        if (
            not isinstance(handoff_id, str)
            or _HANDOFF_RE.fullmatch(handoff_id) is None
        ):
            raise FabricBridgeError("CI guest handoff id is invalid")
        return self._call_ci_guest(
            "ci_runner_guest_enroll",
            {"handoff_id": handoff_id},
        )

    def ci_runner_guest_start(self) -> dict[str, Any]:
        """Start the isolated CI guest listener."""

        return self._call_ci_guest("ci_runner_guest_start", {})

    def ci_runner_guest_stop(self) -> dict[str, Any]:
        """Stop the isolated CI guest listener."""

        return self._call_ci_guest("ci_runner_guest_stop", {})

    def _call_ci_guest(
        self,
        tool: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            result = self._client()._call_tool(tool, arguments)
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError(
                "Runner Fabric CI guest request failed"
            ) from exc
        return _validate_ci_guest_result(result)

    def run_work_unit(
        self,
        *,
        work_unit_id: str,
        project_id: str,
        work_item_id: str,
        expected_revision: str,
        change_plan_id: str,
        validation_profile: str = "foundation",
        correction_budget: int = 1,
        landing_mode: str = "managed_branch_push",
    ) -> dict[str, Any]:
        _semantic_id(work_unit_id, "work_unit_id")
        _semantic_id(project_id, "project_id")
        _semantic_id(work_item_id, "work_item_id")
        _semantic_id(change_plan_id, "change_plan_id")
        _revision(expected_revision)
        if validation_profile != "foundation":
            raise FabricBridgeError("unsupported validation profile")
        if landing_mode != "managed_branch_push":
            raise FabricBridgeError("unsupported landing mode")
        if isinstance(correction_budget, bool) or not isinstance(correction_budget, int):
            raise FabricBridgeError("correction budget must be an integer")
        if not 0 <= correction_budget <= 3:
            raise FabricBridgeError("correction budget is outside the supported range")

        payload = {
            "work_unit_id": work_unit_id,
            "project_id": project_id,
            "work_item_id": work_item_id,
            "expected_revision": expected_revision,
            "change_plan_id": change_plan_id,
            "validation_profile": validation_profile,
            "correction_budget": correction_budget,
            "landing_mode": landing_mode,
        }
        result = self._call_result("run_work_unit", payload)
        if result["expected_revision"] != expected_revision:
            raise FabricBridgeError("Runner Fabric returned a mismatched expected revision")
        return result

    def get_work_unit(self, work_unit_id: str) -> dict[str, Any]:
        _semantic_id(work_unit_id, "work_unit_id")
        result = self._call_view(
            "get_work_unit",
            {"work_unit_id": work_unit_id},
            expected_work_unit_id=work_unit_id,
        )
        return result

    def cancel_work_unit(self, work_unit_id: str) -> dict[str, Any]:
        _semantic_id(work_unit_id, "work_unit_id")
        result = self._call_view(
            "cancel_work_unit",
            {"work_unit_id": work_unit_id},
            expected_work_unit_id=work_unit_id,
        )
        return result

    def _client(self) -> LocalMCPClient:
        client = getattr(self._local, "client", None)
        if client is None:
            client = LocalMCPClient(
                self._mcp_config,
                allowed_tools=_FABRIC_TOOLS,
                client_name="runner-mcp-fabric-bridge",
            )
            self._local.client = client
        return client

    def _call_result(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._client()._call_tool(tool, arguments)
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError("Runner Fabric request failed") from exc
        return _validate_result(result)

    def _call_view(
        self,
        tool: str,
        arguments: dict[str, Any],
        *,
        expected_work_unit_id: str,
    ) -> dict[str, Any]:
        try:
            result = self._client()._call_tool(tool, arguments)
        except BridgeExecutionAdapterError as exc:
            raise FabricBridgeError("Runner Fabric request failed") from exc
        return _validate_view(result, expected_work_unit_id=expected_work_unit_id)



def _validate_ci_guest_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    _exact_keys(
        value,
        {
            "contract_version",
            "operation",
            "state",
            "runner_name",
            "registered",
            "running",
            "isolation_green",
            "network_green",
            "mutation_enabled",
        },
        "CI guest result",
    )
    if (
        value["contract_version"]
        != "runner.fabric/ci-runner-guest-execution/v1alpha1"
    ):
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    if value["operation"] not in _CI_GUEST_OPERATIONS:
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    if value["state"] not in _CI_GUEST_STATES:
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    runner_name = value["runner_name"]
    if (
        not isinstance(runner_name, str)
        or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", runner_name)
    ):
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    for field in (
        "registered",
        "running",
        "isolation_green",
        "network_green",
        "mutation_enabled",
    ):
        if not isinstance(value[field], bool):
            raise FabricBridgeError(
                "Runner Fabric returned invalid CI guest result"
            )
    if value["running"] and not value["registered"]:
        raise FabricBridgeError(
            "Runner Fabric returned invalid CI guest result"
        )
    _validate_bounded_json(value)
    return value


def _canonical_uuid(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise FabricBridgeError(f"Runner Fabric returned invalid {field}")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise FabricBridgeError(f"Runner Fabric returned invalid {field}") from exc
    if str(parsed) != value:
        raise FabricBridgeError(f"Runner Fabric returned invalid {field}")
    return value


def _validate_external_target_preflight(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned invalid external target preflight")
    _exact_keys(
        value,
        {
            "schemaVersion",
            "ready",
            "targetAllocationId",
            "environmentId",
            "mutationEnabled",
            "networkChecked",
        },
        "external target preflight",
    )
    if value["schemaVersion"] != "runner.fabric/external-target-preflight/v1":
        raise FabricBridgeError("Runner Fabric returned invalid external target preflight")
    if value["ready"] is not True:
        raise FabricBridgeError("Runner Fabric external target preflight is not ready")
    if value["mutationEnabled"] is not False or value["networkChecked"] is not False:
        raise FabricBridgeError("Runner Fabric external target preflight is not read-only")
    _canonical_uuid(value["targetAllocationId"], "target allocation id")
    _canonical_uuid(value["environmentId"], "environment id")
    _validate_bounded_json(value)
    return value


def _validate_external_target_inspection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    _exact_keys(
        value,
        {
            "schemaVersion",
            "contractVersion",
            "targetAllocationId",
            "environmentId",
            "reachability",
            "readiness",
            "observedAt",
            "reasonCode",
            "releaseRevision",
            "evidenceRefs",
            "liveMutationEnabled",
        },
        "external target inspection",
    )
    if value["schemaVersion"] != "runner.fabric/external-target-live-qualification/v1":
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    if value["contractVersion"] != "runner.fabric/external-target-inspection/v1alpha1":
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    if value["liveMutationEnabled"] is not False:
        raise FabricBridgeError("Runner Fabric external target inspection must be read-only")
    _canonical_uuid(value["targetAllocationId"], "target allocation id")
    _canonical_uuid(value["environmentId"], "environment id")
    if value["reachability"] not in {"reachable", "unreachable", "unknown"}:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    if value["readiness"] not in {"ready", "degraded", "not-ready", "unknown"}:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    observed_at = value["observedAt"]
    if not isinstance(observed_at, str):
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    try:
        observed = datetime.fromisoformat(observed_at)
    except ValueError as exc:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection") from exc
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    reason = value["reasonCode"]
    if not isinstance(reason, str) or _REASON_RE.fullmatch(reason) is None:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    release = value["releaseRevision"]
    if release is not None:
        _revision(release)
    evidence = value["evidenceRefs"]
    if not isinstance(evidence, list) or len(evidence) > 16:
        raise FabricBridgeError("Runner Fabric returned invalid external target inspection")
    for reference in evidence:
        _reference(reference, "evidence reference")
    _validate_bounded_json(value)
    return value


def _validate_host_inspection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    _exact_keys(
        value,
        {"schema_version", "mutation_enabled", "host", "browsers"},
        "host inspection",
    )
    if value["schema_version"] != "runner.fabric/host-inspection/v1":
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    if value["mutation_enabled"] is not False:
        raise FabricBridgeError("Runner Fabric host inspection must be read-only")

    host = value["host"]
    if not isinstance(host, dict):
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    required_host_keys = {
        "id",
        "display_name",
        "freshness",
        "cpu",
        "memory",
        "swap",
        "pressure",
        "filesystems",
        "disks",
        "network",
        "uptime_seconds",
        "oom_kills",
        "process_count",
        "collector",
    }
    if set(host) != required_host_keys:
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    host_id = host["id"]
    if not isinstance(host_id, str) or _ID_RE.fullmatch(host_id) is None:
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    if not host_id.startswith("host:"):
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")
    if not isinstance(host["display_name"], str) or not 1 <= len(host["display_name"]) <= 160:
        raise FabricBridgeError("Runner Fabric returned invalid host inspection")

    browsers = value["browsers"]
    if not isinstance(browsers, list) or len(browsers) != 4:
        raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
    expected_runtimes = {"chromium", "chrome", "firefox", "webkit"}
    seen: set[str] = set()
    for browser in browsers:
        if not isinstance(browser, dict):
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        keys = set(browser)
        if keys not in (
            {"runtime", "state", "cache_ready"},
            {"runtime", "state", "cache_ready", "version"},
        ):
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        runtime = browser["runtime"]
        state = browser["state"]
        cache_ready = browser["cache_ready"]
        if runtime not in expected_runtimes or runtime in seen:
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        seen.add(runtime)
        if state not in {"available", "unverified", "unavailable"}:
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        if not isinstance(cache_ready, bool):
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        version = browser.get("version")
        if state == "available":
            if not isinstance(version, str) or not 1 <= len(version) <= 160:
                raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
        elif version is not None:
            raise FabricBridgeError("Runner Fabric returned invalid browser inspection")

    if seen != expected_runtimes:
        raise FabricBridgeError("Runner Fabric returned invalid browser inspection")
    _validate_bounded_json(value)
    return value


def _validate_bounded_json(value: object) -> None:
    forbidden_fragments = {
        "path",
        "token",
        "secret",
        "credential",
        "password",
        "authorization",
        "private_key",
        "endpoint",
        "url",
        "argv",
        "command",
        "shell",
        "executable",
    }
    stack: list[object] = [value]
    nodes = 0
    while stack:
        current = stack.pop()
        nodes += 1
        if nodes > 4096:
            raise FabricBridgeError("Runner Fabric host inspection is too large")
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    raise FabricBridgeError("Runner Fabric host inspection is invalid")
                lowered = key.casefold()
                if any(fragment in lowered for fragment in forbidden_fragments):
                    raise FabricBridgeError("Runner Fabric host inspection contains private detail")
                stack.append(item)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if len(current) > 512 or any(ord(char) < 32 and char not in "\t" for char in current):
                raise FabricBridgeError("Runner Fabric host inspection is invalid")
            if current.startswith("/") or "\\" in current:
                raise FabricBridgeError("Runner Fabric host inspection contains private detail")
        elif current is not None and not isinstance(current, (int, float, bool)):
            raise FabricBridgeError("Runner Fabric host inspection is invalid")

    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FabricBridgeError("Runner Fabric host inspection is invalid") from exc
    if len(raw) > 64 * 1024:
        raise FabricBridgeError("Runner Fabric host inspection is too large")


def _validate_view(
    value: object,
    *,
    expected_work_unit_id: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned an invalid work-unit view")
    _exact_keys(
        value,
        {"work_unit_id", "project_id", "work_item_id", "status", "result"},
        "work-unit view",
    )
    _semantic_id(value["work_unit_id"], "work_unit_id")
    if value["work_unit_id"] != expected_work_unit_id:
        raise FabricBridgeError("Runner Fabric returned a mismatched work-unit identifier")
    _semantic_id(value["project_id"], "project_id")
    _semantic_id(value["work_item_id"], "work_item_id")
    status = value["status"]
    if not isinstance(status, str) or status not in _STATUSES:
        raise FabricBridgeError("Runner Fabric returned an invalid work-unit status")
    result = value["result"]
    if status in {"running", "cancel_requested"}:
        if result is not None:
            raise FabricBridgeError("Runner Fabric returned inconsistent work-unit state")
        return value
    if result is None:
        raise FabricBridgeError("Runner Fabric returned inconsistent work-unit state")
    validated_result = _validate_result(result)
    if validated_result["state"] != status:
        raise FabricBridgeError("Runner Fabric returned inconsistent work-unit state")
    return value


def _validate_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned an invalid work-unit result")
    _exact_keys(
        value,
        {
            "state",
            "expected_revision",
            "commit_revision",
            "pushed_revision",
            "change_reference",
            "report_reference",
            "corrections_used",
            "reported",
            "evidence",
        },
        "work-unit result",
    )
    state = value["state"]
    if not isinstance(state, str) or state not in _STATES:
        raise FabricBridgeError("Runner Fabric returned an invalid work-unit state")
    _revision(value["expected_revision"])
    for key in ("commit_revision", "pushed_revision"):
        if value[key] is not None:
            _revision(value[key])
    for key in ("change_reference", "report_reference"):
        if value[key] is not None:
            _reference(value[key], key)
    corrections = value["corrections_used"]
    if isinstance(corrections, bool) or not isinstance(corrections, int):
        raise FabricBridgeError("Runner Fabric returned invalid correction evidence")
    if not 0 <= corrections <= 3:
        raise FabricBridgeError("Runner Fabric returned invalid correction evidence")
    if not isinstance(value["reported"], bool):
        raise FabricBridgeError("Runner Fabric returned invalid report evidence")
    evidence = value["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 32:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    for item in evidence:
        _validate_evidence(item)
    return value


def _validate_evidence(value: object) -> None:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    _exact_keys(
        value,
        {
            "stage",
            "outcome",
            "reason_code",
            "attempt",
            "checkpoint",
            "revision",
            "reference",
        },
        "stage evidence",
    )
    if value["stage"] not in _STAGES:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    if value["outcome"] not in _OUTCOMES:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    reason = value["reason_code"]
    if not isinstance(reason, str) or _REASON_RE.fullmatch(reason) is None:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    attempt = value["attempt"]
    if isinstance(attempt, bool) or not isinstance(attempt, int) or not 0 <= attempt <= 3:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    checkpoint = value["checkpoint"]
    if checkpoint is not None and checkpoint not in _CHECKPOINTS:
        raise FabricBridgeError("Runner Fabric returned invalid stage evidence")
    revision = value["revision"]
    if revision is not None:
        _revision(revision)
    reference = value["reference"]
    if reference is not None:
        _reference(reference, "reference")


def _exact_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise FabricBridgeError(f"Runner Fabric returned invalid {label}")


def _semantic_id(value: object, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise FabricBridgeError(f"{field} is invalid")
    return value


def _revision(value: object) -> str:
    if not isinstance(value, str) or _REVISION_RE.fullmatch(value) is None:
        raise FabricBridgeError("revision is invalid")
    return value


def _reference(value: object, field: str) -> str:
    if not isinstance(value, str) or _REFERENCE_RE.fullmatch(value) is None:
        raise FabricBridgeError(f"{field} is invalid")
    return value



def _validate_operational_snapshot(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    _exact_keys(
        value,
        {
            "schema_version",
            "observed_at",
            "busy",
            "degraded",
            "unknown_layers",
            "layers",
            "mutation_enabled",
            "execution_enabled",
        },
        "operational snapshot",
    )
    if value["schema_version"] != "runner.fabric/operational-snapshot/v1":
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    if value["mutation_enabled"] is not False or value["execution_enabled"] is not False:
        raise FabricBridgeError("Runner Fabric operational snapshot must be read-only")
    observed_at = value["observed_at"]
    if isinstance(observed_at, bool) or not isinstance(observed_at, int) or observed_at < 0:
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    if not isinstance(value["busy"], bool) or not isinstance(value["degraded"], bool):
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    unknown = value["unknown_layers"]
    layers = value["layers"]
    if not isinstance(unknown, list) or len(unknown) > 32:
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    if not isinstance(layers, list) or len(layers) > 32:
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    seen: set[str] = set()
    for item in layers:
        if not isinstance(item, dict):
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        _exact_keys(
            item,
            {
                "layer",
                "health",
                "queued",
                "claimed",
                "running",
                "waiting_for_result",
                "waiting_for_ack",
                "retrying",
                "pending_count",
                "capacity_total",
                "capacity_available",
                "oldest_pending_age_seconds",
                "last_activity_age_seconds",
                "reason_code",
            },
            "operational layer",
        )
        layer = item["layer"]
        if not isinstance(layer, str) or _ID_RE.fullmatch(layer) is None or layer in seen:
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        seen.add(layer)
        if item["health"] not in {"healthy", "degraded", "unavailable", "unknown"}:
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        counts = (
            "queued",
            "claimed",
            "running",
            "waiting_for_result",
            "waiting_for_ack",
            "retrying",
            "pending_count",
        )
        for key in counts:
            count = item[key]
            if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 1_000_000:
                raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        if item["pending_count"] != sum(item[key] for key in counts[:-1]):
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        for key in ("capacity_total", "capacity_available"):
            capacity = item[key]
            if capacity is not None and (
                isinstance(capacity, bool)
                or not isinstance(capacity, int)
                or not 0 <= capacity <= 1_000_000
            ):
                raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        if (
            item["capacity_total"] is not None
            and item["capacity_available"] is not None
            and item["capacity_available"] > item["capacity_total"]
        ):
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        for key in ("oldest_pending_age_seconds", "last_activity_age_seconds"):
            age = item[key]
            if age is not None and (
                isinstance(age, bool)
                or not isinstance(age, int)
                or not 0 <= age <= 31 * 24 * 60 * 60
            ):
                raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
        reason = item["reason_code"]
        if reason is not None and (
            not isinstance(reason, str) or _ID_RE.fullmatch(reason) is None
        ):
            raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    if any(
        not isinstance(item, str) or item not in seen
        for item in unknown
    ):
        raise FabricBridgeError("Runner Fabric returned invalid operational snapshot")
    _validate_bounded_json(value)
    return value
