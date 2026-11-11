# #540 — Stale MCP session: no automatic tool replay, verified next generation

## Identity
- parent: Runner-MCP #540 / #590
- owner: Runner-MCP connected-client communication lane, 2026-10-10
- scope: `src/runner_mcp/bridge_mcp_executor.py` and matching unit tests
- legacy context: #540 catalog drift, RMCP-MCP-0005 live first failed edge UNKNOWN

## Defect / safety goal
Current loopback `LocalMCPClient._call_tool` transparently resends any prior `tools/call` after receiving HTTP 404 on a session. This includes `self_update`, `run_tests`, `sync_project` or service mutations. Intermediaries may return ambiguous 404 after an action has crossed an execution boundary; whether a side effect happened cannot be inferred from an HTTP status code. Such silent retries risk duplicate actions and skip caller-level reconciliation.

## Owned change
- Drop in-flight MCP tool request on observed stale session. Return only fixed `MCP_SESSION_STALE_EFFECT_UNKNOWN_RECONNECT_REQUIRED` error with no URL, service, request or job arguments.
- Discard cached session, peer build/interface, protocol and registered tool names. NEVER transparently replay the old JSON-RPC ID/payload, even for normally read-only tools.
- Mark client requiring a **verified** next-generation reconnect. The next independent explicit caller invocation must run handshake, real `tools/list` schema and exact `build_identity` compatibility check, even when initial client configuration opted out of optional preflight. Missing/mismatched proof fails before tool dispatch.
- No new retry daemon, alternate endpoint, auto-discovery, bypass, provider call or host mutation; no lifecycle changes.

## Negative acceptance
1. Both read-only and mutating calls stop after original 404; exact three requests only: initialize, initialized, tools/call; no immediate second request.
2. Public error fixed category; no private URL, prompt, token, project path, task payload, request ID.
3. State is reset with mandatory verified requalification on a separately initiated future request.
4. Changed peer schema is blocked before any tool call; source-appropriate compatibility preflight is mandatory.
5. Preserve existing normal zero-stale success, peer versions and exact JSON-RPC response-ID checks; full exact-head CI (Ruff, pytest, release artifact, clean demo, attribution).
6. Failure Museum and handovers updated. Operational #540/#590 remain OPEN until actual installed process catalog, same-route request/response delivery and approved A6/A7 physical release evidence.

## Dependencies and boundaries
Fabric #1398/#1400 manages trusted issuer/lease/fencing (different chat); host admission #642, AIfordable #370 real Claude worker, Fabric #972 real Q7, Fabric A6/#942 and A7/#943 protected rollout remain separate. No Desktop Commander, shell, tunnel restart, credentials or production write access. Do not infer live repair from local CI.
