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

## v0.1.178 — audit privacy for unregistered tool names

An MCP client controls the `tools/call.params.name` string. An unregistered
name may itself contain private markers or malicious log content. The private
dispatch must NOT record that arbitrary name in the durable existing
`AuditEvent`. Only an exact built-in string contained in the SDK's **actual
registered** tool catalogue (and bounded to 96 chars) is logged by name;
otherwise the audit field is the neutral literal `unknown_tool`. When private
identity lookup fails before the catalogue is observed, the catalogue remains
unknown and the same neutral label applies. The categorical refusal reason
and request correlation remain intact.

The guard still returns fixed `HOST_TOOL_NOT_PERMITTED`, and recognized
denied OCR tools retain their exact audit names. New SDK and authenticated HTTP
tests exercise a client-injected synthetic sensitive marker, absent policy
and failed evidence provider. No secret or path ever becomes a policy input or
new feature. This patch is not a replacement for the unmerged #669 original
host/wheel witness, independent signed permit or deployment approval.

## v0.1.179 — SDK tool-catalogue generation recheck

The private guard reads `list_tools()` for the allowed names, then obtains
the interface-schema digest from a provider which itself may read
`list_tools()` again. A concurrent tool registration or tool schema change
could otherwise combine names and schema from *different* SDK generations in
one policy decision.

After the digest provider returns, the guard now takes a second SDK tool
snapshot and compares canonical `(name, input_schema, output_schema)` tuples
against the initial one. Any discrepancy rejects the whole invocation as
`host_tool_catalogue_changed`, records the generic `unknown_tool` audit
identity and returns fixed `HOST_TOOL_NOT_PERMITTED` before the handler.
If unchanged, it proceeds to the existing private owner/policy second read
and original admission logic. Synthetic tests cover name replacement,
input-schema drift and stable catalogue/authorized execution.

This is a conservative application-level readback, **not** an atomic
registry lock, process-generation seal, or qualified signed host permit.
#669's original wheel/host attestation and A7 owner gate remain separate;
no existing production service enables the private host guard.


## v0.1.180 — independent schema snapshots across async catalogue checks

The v0.1.179 readback previously retained references to SDK descriptor
schema dictionaries. If the SDK reused descriptors and mutated an input or
output schema **in place** during the awaited digest operation, the earlier
and later comparisons could both observe the new value and incorrectly
accept it. The first catalogue observation now deep-copies both schema
structures before awaiting the digest provider. The second observation is
compared to those independent values; mutation yields the same bounded
`host_tool_catalogue_changed` denial and neutral audit tool label.

Disposable regressions mutate top-level and nested input schema content
through deliberately shared SDK descriptor objects while digest verification
awaits. Neither may reach the handler; the existing stable-catalogue test
continues to permit one synthetic execution. This is not an atomic SDK
registry lock, signed host policy, active-wheel provenance, or deployment
approval. #669, A7, I7 and actual server processes remain untouched.
