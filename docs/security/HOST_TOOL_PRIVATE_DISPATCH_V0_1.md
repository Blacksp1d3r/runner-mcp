# Runner-MCP #642 — private MCPServer.call_tool pre-dispatch seam

This is an **inactive, explicit opt-in source integration**. The normal
`create_app` and `build_mcp` accept no qualified host evidence by default
and continue to instantiate the existing `MCPServer`. No new tool name,
policy store, endpoint, daemon, environment override or deployment is added.

With an internal, independently qualified `host_dispatch_evidence_provider`,
`build_mcp` selects `HostAdmissionMCPServer`, which intercepts the SDK's
canonical `call_tool` method **before** registered handlers execute. It
reuses the *already merged* `evaluate_host_tool_admission` oracle, obtains
the actual tool catalogue from `list_tools()` and the actual local interface
schema digest via `runner_mcp_interface_schema_digest`, and uses an in-process
clock rather than any caller-supplied timestamp. A mismatch or missing
authority returns fixed `HOST_TOOL_NOT_PERMITTED` and writes one existing
`AuditEvent` with the bounded reason. Audit failure never permits execution.
An async tool-catalogue or schema read may overlap a private owner/policy
rotation. The guarded SDK dispatch therefore re-observes the same internal
first-party evidence provider after those awaits and compares the complete
host/policy/revision facts before calling the original tool handler. A
revoked/replaced permit, changed host/loaded revision or failed second read
remains denied and audited (no side effects). This is NOT a kernel-atomic
lease, a signature, or independent physical provenance: only a bounded
recheck before this single SDK dispatch.

A positive oracle result does not bypass OperatorSafetyGuard, approvals,
leases, emergency stop, project allowlists or A7.

**Critical missing first-party operational witness:** No production provider
exists for signed expiring host policy + independently verified exact
service-asset ID and *loaded running wheel/process* source revision. Current
`installed_source_revision` deliberately returns None: self-update history
is not current loaded-wheel provenance. Constructing `HostDispatchEvidence`
in a test is not authentication, signing, host qualification or release
admission. Do not enable or configure this in an actual service until those
inputs are independently attested, recorded and approved.

Disposable tests prove SDK interception, no handler side effects on denial,
audit denial record, fail-closed audit errors, catalogue unchanged, foreign
policy/revision/schema rejection. They are not a real client/worker or
physical host qualification.

# Scope and gates
- #642 remains open until a verified provider and actual wire-level
  tools/call denial/readback on a qualified test host.
- No active host override or live policy loader.
- No deployment, A7, I7, cron, systemd, runner or server restart.
- Requires next-patch release reservation and exact-head full CI.
