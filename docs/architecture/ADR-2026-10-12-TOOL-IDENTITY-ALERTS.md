# ADR 2026-10-12 — Tool identity, negotiated contracts and actionable alerts

Status: PROPOSED / SOURCE-ONLY. Owner: Runner-MCP #665. Fleet counterpart: Runner-Fabric #1471.
Dependencies: #590 live request lineage; #642 host admission; #661 version gate; #663 version allocator; #664 legacy contracts; Fabric #942/#943 safe releases.

## Decision

MCP standard `tools/list` and `tools/call` retain their existing names and wire semantics. **Never prefix executable tool names with a magic code.** A string or language-independent 'magic code' cannot prove identity, prevent collisions or authenticate a server. Instead, introduce an opt-in first-party namespace `com.aifordable.runner-mcp`, plus immutable *registry* tool identifiers and independent contract revisions. The namespace is a classifier, not a credential.

Example *illustrative only* (not assigned): namespace=`com.aifordable.runner-mcp`, id=`RMCP-0042`, name=`fabric_update_readiness`, contract_revision=1. **Do not invent IDs for existing tools in production.** The actual ID/name binding requires a reviewed immutable registry before use.

An actual serving build is identified by the authenticated service asset, running code commit, immutable release artifact/payload digest, registered tool schema digest and local policy generation. SemVer alone is not a build identity. Obtain build evidence from a first-party attested source, not arbitrary caller-supplied metadata.

## Boundaries and negotiation

1. On authenticated connection, receive and verify server identity, actual running build, schema and allowed capabilities. Compare to approved, versioned tool-contract registry.
2. Clients without this extension keep ordinary MCP behavior. Until an old client/server is qualified, expose only separately reviewed safe read-only compatibility operations, never guessing IDs or escalating to a shell.
3. Tool routing checks authenticated host/tenant policy and authoritative actual registry name/ID/revision/schema *before any execution*. An optional extension must not become an authorization bypass or rename existing registered tools.
4. Client cache is bound to authenticated host, session, build, policy generation and catalogue hash; change/reconnect invalidates the cache. No transparent replay of mutating tools after unknown-effect transport failure.
5. An unknown tool is **not automatically proof of a version mismatch**: causes include bad routing, disabled policy, malicious call, stale cache and unregistered tool. Report evidence and distinct classification, never speculate.

## Typed fault taxonomy (sanitized)

| Code | Determination | Action |
| --- | --- | --- |
| UNKNOWN_TOOL | Authenticated target has no registered name/ID | Reject, request bounded requalification |
| VERSION_MISMATCH | Verified actual build/contract incompatible with expected | Reject, mark fleet skew and alert |
| SCHEMA_MISMATCH | Verified name/ID exists but schema digest disagrees | Reject, alert |
| TOOL_DISABLED | Known tool disallowed by verified host policy | Reject, audit; do not suggest upgrade |
| UNTRUSTED_TOOL_IDENTITY | Claimed ID/namespace/host cannot be authenticated | Reject; security alert |
| TOOL_FAILED | Tool accepted but handler failed | Return typed safe error; retain request lineage |
| RUNTIME_UNREACHABLE | Authenticated endpoint not reached / timeout | Return delivery-unknown where applicable; no automatic replay |
| STALE_INVENTORY | Last attested observation exceeds agreed freshness | Flag evidence quality; not 'patched' or 'online' |

A reporting envelope has fixed `code`, `request_id` (opaque), `target_asset_id` (opaque scoped ID), `expected_build`, `observed_build` (safe fingerprints only), `tool_id`, `contract_revision`, `first_seen`, `last_seen`, `occurrences`, `delivery_state`; omit fields not securely established. Never log arguments, secrets, paths or private customer data in GitHub.

## Alerts and autonomous operation

Runner-MCP emits bounded event evidence; Fabric owns the durable tenant-scoped event ledger, deduplication, severity, escalation, customer notification and delivery/ACK audit. Cluster repeated events by tenant + asset + code + tool + expected/observed fingerprint; a repeated incident updates counts, not a flood of messages. Alert on first **verified** skew, sustained transport failure, and repeated suspicious unknown/forged calls with rate limits. A stale or offline client must remain in inventory as unknown/outdated rather than disappearing or being marked healthy.

Do not auto-upgrade or self-restart from an error code. Rollout requires first-node rollback escrow, A6/A7 and original-client result+ACK. An alert may trigger a review or gated release eligibility check; not direct mutation. An AI should be consulted only on an actionable unresolved incident or code change, not routine heartbeat polling.

## Negative acceptance matrix

- Same `0.1.3` but different immutable code/schema → incompatible, no false success.
- Recognized name with foreign ID; duplicated ID; unknown name; unknown contract revision → deny with no handler side effects.
- Known disabled tool → TOOL_DISABLED, never UNKNOWN_TOOL or generic version mismatch.
- Forged namespace/asset/build handshake and old session replay → deny, audit, no privilege increase.
- Legacy compliant N/N-1 tool calls → keep wire behavior; unsupported tools reject without fallback.
- Failed MCP response after unknown effect → no transparent retry; original-client response lineage recorded.
- Two tenants with same tool fault → strictly separate counters, notifications and access.
- Offline client, missing observed build, ambiguous route → remain UNKNOWN/STALE; never assert update succeeded.
- Fault storm → bounded rate and deduplicated alert; delivery and acknowledgement separately evidenced.
- Independently validate actual isolated `tools/list` + schema digest against release manifest, not only static 95-name AST receipt.

## Implementation sequencing and handoff

A. Approve protocol and immutable registry ownership; keep docs-only until #661/#663 version conveyor is integrated to avoid another tool/code change under shared `0.1.3`.
B. Pure typed registry + deterministic negative tests in isolated source branch and **new unique version**. Preserve published v1 MCP contracts.
C. Verified in-process actual catalogue and authenticated host negotiation, with denial before side effects.
D. Fabric #1471 inventory migrations, event ingest, de-dup alerts and notification ACK tests.
E. Safe limited pilot only after #590 live route and A6/A7 rollback gates, never an unapproved production push.

Handover: This ADR is architectural design only; there is no new tool, wire extension, runtime guard or alert running. Existing installed host identity / fleet parity unqualified. Exact next task is implementation child registration after review and merge sequencing #661 → #663 → unique version for #665.
