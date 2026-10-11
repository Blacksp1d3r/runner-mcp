# #642 — Trusted MCP tool-dispatch admission (child TASK)

Status: BLOCKED_ON_TRUSTED_POLICY_SOURCE; source-only oracle exists via merged #641; expanded synthetic tests #654 and mandatory independent-identity source gate #656 are CI-green but not merged. Owner: Runner-MCP #642; Fabric owns host-policy/identity issuance. Do not overlap other agents' host authority work.

## Intended intercept
Real `MCPServer.call_tool(name, arguments, context)` is the narrow boundary **before** ToolManager/handler invocation. Current `build_mcp` constructs `MCPServer` and registers tools, `runner_mcp_interface_schema_digest` independently hashes advertised schemas. A wrapper/subclass is insufficient unless the real authenticated request route provably enters it. Never filter tools/list to simulate host restrictions.

## Required verified dependencies before executable binding
- First-party immutable service identity (never MCP arguments or sandbox environment), authenticated signed/provenance-checked host permit and expiry bound to actual executing process's source commit, release artifact and interface schema; private qualified authority and refresh/revocation semantics; stale evidence fails closed.
- Prevent cross-host policy replay: #656 adds a REQUIRED `verified_service_asset_id` input to the SOURCE-ONLY oracle and rejects mismatch with `QualifiedHostToolPolicy.service_asset_id`; adversarial tests also reject forged Python equality/hash, tool-name, schema and policy subclasses. **This is not independent host attestation:** the actual first-party source of the ID, authenticated/signed permit, real MCP dispatch integration, and original-client ACK remain unqualified. Never supply the host ID from MCP tool arguments, the permit itself, or a caller-controlled environment. Shared source/schema alone never authorizes a policy issued for another host.
- Explicit owner-reviewed bootstrap transition: no deployment with a missing permit that would unexpectedly lock out both control instances; do not substitute an all-allow policy or silently bypass admission.
- Confirm actual installed MCP SDK call_tool dispatch entry, invocation/result/context/error contract under the CI-built artifact before adding interception; project currently permits `mcp>=2.0,<3` (not a single pinned SDK version), so grep of `MCPServer.call_tool` alone is NOT runtime proof. Test real authenticated pre-handler deny, cancellation and exceptional response across supported SDK builds; no private SDK monkeypatch.
- Stable correlation ID for audited deny and *same originating client* structured `HOST_TOOL_NOT_PERMITTED` response. HTTP 200/ingress without client receipt is insufficient; no replay or alternate-host redirect.

## Implementation order once dependencies are proven
1. Obtain qualified immutable policy snapshot from first-party host authority, not a caller-supplied host selector.
2. Verify process identity and exact registered tool schema against permit; evaluate the merged `evaluate_host_tool_admission` on every invocation before handler effects.
3. For denial, emit bounded structured code and audit correlation; preserve normal schema and existing emergency-stop, human approvals, Fabric lease/fencing and project guards.
4. Synthetic integration through a real authenticated MCP transport with primary denies five actually registered OCR tool names and lab permits only under its independently authenticated policy, both advertising identical tools/list schema/digest; side-effect counter remains zero for deny. Negative missing/stale/forged policy/host/schema, lost response and original-client receipt.
5. CI on exact feature head with tests, Ruff, artifact, isolated demo; independently review before any rollout. Live fleet canary remains gated by #509/#590, Fabric #942/#943 and #341.

## Out of scope
No separate policy issuer/daemon, updater, fabricated release signature, generic host/path/shell, runtime restart, tunnel modification, live production install or Claude dispatch. Keep #438 unmerged pending independent corrected acknowledgment semantics. Failure Museum existing RMCP-F-0002 for A6; PR #654 introduced test-fixture incident RMCP-F-0025.

Next safe action: Fabric/AIfordable authority owner documents a verifiable, expiring host permit/active runtime binding. Then implement the dispatcher seam in a small isolated source PR using this contract.
