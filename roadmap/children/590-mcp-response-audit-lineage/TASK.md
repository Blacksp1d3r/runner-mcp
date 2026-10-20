# Runner-MCP #590 — authenticated MCP response/audit lineage child

## Goal
Prove for one same authenticated local MCP session that a successful `list_projects` and a synthetic degraded `runtime_status` each retain a unique request ID and W3C trace context from ingress to the HTTP response, including an exact matching bounded server audit record. This narrows the source-side diagnosis of mixed successes and opaque live connected failures.

## Owned scope / separation
Runner-MCP #590 server-side source regression only; not tunnel-client deployment, live host fingerprinting, Fabric #1398/#1400 leases, AIfordable #370 rootless worker, Q7 real Fabric #972, or host-admission #642. No service restart, no tunnel retry, no project work or model use.

## Method
1. Use a first-party in-process real authenticated MCP HTTP TestClient, with one initialized MCP session.
2. Call an allowlisted read-only successful `list_projects`, then deliberately make one isolated synthetic `SelfUpdateManager.runtime_status` fail with private-looking text and invoke `runtime_status`.
3. Require two distinct response `X-Request-ID` values, same caller-provided trace ID with independent server-side child spans; strict JSON-RPC results, local audit unique matching records by request-ID and result class.
4. Deny leakage of private exception text, local test paths or bearer values.
5. Validate with exact-head Ruff/pytest, artifact, clean demo, commit attribution. Record results and Failure Museum/diagnostics.

## Interpretation
Green **only rules out** request↔audit mismatch *for this isolated server implementation*. It does NOT prove that the current ChatGPT connector's failed request reached the deployed server, or that tunnel HTTP 200 acceptance returned to the originating client. For operational #590, qualify operator-owned first-party deployed build/interface hash, client advertised tools/list schema, and one opaque-ID known-good/failing request through dispatcher, exact server process, response-delivery and client using current A6/A7 safe rollout. If any edge lacks evidence, classify UNKNOWN; do not guess a second server or restart.

## Dependencies
Runner-MCP #540 stale catalogue generation; #642 host-local policies; Fabric A6 #942, A7 #943 protected release; #381 Claude coding worker. Keep #381/#590 OPEN until physical acceptance.
