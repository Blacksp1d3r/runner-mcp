"""Opt-in, non-deployed MCPServer.call_tool boundary for #642.

No untrusted MCP argument, hostname, environment variable, historical update
marker or policy dataclass can attest a live service identity. The evidence
provider is exclusively internal and must be independently qualified by the
owner before activation. The normal server has NO provider and is unchanged.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import time

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .audit import AuditEvent, AuditLogger, utc_timestamp
from .host_tool_admission import (
    HostToolAdmission,
    QualifiedHostToolPolicy,
    evaluate_host_tool_admission,
)
from .http_middleware import current_request_id


@dataclass(frozen=True, slots=True)
class HostDispatchEvidence:
    """Structural facts, not proof of signatures, loaded wheel, or host origin."""

    verified_service_asset_id: str | None
    runtime_source_revision: str | None
    policy: QualifiedHostToolPolicy | None


class HostAdmissionMCPServer(MCPServer):
    """Qualified private SDK interception; never a new MCP tool endpoint."""

    def __init__(
        self,
        *args: object,
        evidence_provider: Callable[[], HostDispatchEvidence],
        schema_digest_provider: Callable[[MCPServer], Awaitable[str]],
        audit: AuditLogger,
        **kwargs: object,
    ) -> None:
        if not callable(evidence_provider) or not callable(schema_digest_provider):
            raise TypeError("private host-admission providers are required")
        if not hasattr(audit, "append") or not callable(audit.append):
            raise TypeError("private audit logger is required")
        super().__init__(*args, **kwargs)
        self._host_admission_evidence_provider = evidence_provider
        self._host_admission_digest_provider = schema_digest_provider
        self._host_admission_audit = audit

    async def call_tool(
        self, name: str, arguments: dict[str, object], context: object | None = None
    ) -> object:
        """Check on EVERY SDK call, before any registered handler can run."""
        # A denied tools/call name is client-controlled. Never audit that raw
        # string unless the SDK itself has declared it as a known tool.
        names: frozenset[str] = frozenset()
        try:
            evidence = self._host_admission_evidence_provider()
            if type(evidence) is not HostDispatchEvidence:
                raise ValueError("private evidence unavailable")
            # Derived from THIS registered SDK catalogue, not the policy or client.
            actual_tools = await self.list_tools()
            names = frozenset(tool.name for tool in actual_tools)
            actual_schema = await self._host_admission_digest_provider(self)
            if type(actual_schema) is not str:
                raise ValueError("live schema digest unavailable")
            # list_tools() and the digest provider can await I/O. A first-party
            # owner/lease/policy generation may change while awaiting them.
            # Read the private witness again immediately before dispatch.
            latest = self._host_admission_evidence_provider()
            if type(latest) is not HostDispatchEvidence:
                raise ValueError("post-schema private evidence unavailable")
            if latest != evidence:
                verdict = HostToolAdmission(
                    False, "host_admission_evidence_changed", "HOST_TOOL_NOT_PERMITTED"
                )
            else:
                verdict = evaluate_host_tool_admission(
                    name,
                    registered_tool_names=names,
                    verified_service_asset_id=latest.verified_service_asset_id,
                    runtime_source_revision=latest.runtime_source_revision,
                    runtime_interface_schema_sha256=actual_schema,
                    policy=latest.policy,
                    now_epoch=int(time()),
                )
        except Exception:  # noqa: BLE001 - untrusted private evidence must fail closed
            # No sensitive exception values, source paths or policy data leak.
            verdict = HostToolAdmission(
                False, "host_admission_evidence_unavailable", "HOST_TOOL_NOT_PERMITTED"
            )
        if not verdict.allowed:
            try:
                self._host_admission_audit.append(
                    AuditEvent(
                        current_request_id(),
                        (
                            name
                            if type(name) is str
                            and len(name) <= 96
                            and name in names
                            else "unknown_tool"
                        ),
                        None,
                        "authenticated-client",
                        "denied:" + verdict.reason_code,
                        utc_timestamp(),
                    )
                )
            except Exception:  # noqa: BLE001 - no audit failure may permit action
                # No unrecorded deny, but audit failure must NEVER permit a tool.
                raise ToolError("HOST_TOOL_NOT_PERMITTED") from None
            raise ToolError("HOST_TOOL_NOT_PERMITTED")
        return await super().call_tool(name, arguments, context)
