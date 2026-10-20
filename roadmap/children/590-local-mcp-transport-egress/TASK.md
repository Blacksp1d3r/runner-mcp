# #590 — Secure local MCP bearer transport against proxies and redirects

## Identity, owner, scope
- Parent: Runner-MCP #590 / #540, privacy and connector-return path reliability
- Status: UNCLAIMED pending safe scheduling
- Owner lane: Runner-MCP local MCP HTTP client, **not** Fabric #1398/#1400
- Files to inspect: `src/runner_mcp/bridge_mcp_executor.py`, bounded unit HTTP transport tests
- Related independently merged Fabric [#1446](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1446) precedent: same private bearer egress protection for Fabric Q7

## Observed source boundary
`LocalMCPConfig` restricts the initial endpoint to localhost, yet `LocalMCPClient._post()` currently calls `urllib.request.urlopen(request, ...)`. Standard urllib defaults can consult environment proxy variables and follow HTTP 3xx redirects to another endpoint. The first-party bearer is attached before this call. A loopback-only configured URL is **not sufficient** to prove the bearer never travels to a different network destination. This is source-code exposure risk; there is no observation of actual data exfiltration.

## Proposed bounded implementation
1. Introduce a closed first-party no-proxy, no-redirect urllib opener: `build_opener(ProxyHandler({}), HTTPRedirectHandler subclass whose redirect_request always returns None)`. Keep fixed loopback endpoint and send to it only.
2. Reject every 30x as categorized secret-free transport failure; do not retry or follow a new address, even another local path. Preserve stale-session uncertainty handling from PR #650 and never broaden service/user/host authority.
3. Use one well-defined transport seam so existing synthetic tests can inject a fake opener without any internet access. Avoid process-global urllib opener mutations; preserve thread-local/client concurrency isolation.
4. Regression tests: hostile `HTTP_PROXY/HTTPS_PROXY/NO_PROXY` cannot introduce a ProxyHandler; external and same-host redirect rejected before second request; bearer never appears in public error; existing session build/schema preflight remains enforced; no original work-unit replay after 404.

## Acceptance/gates
Source-only exact-head Ruff/pytest, artifact, clean demo and attribution; separate PR from #650 to avoid editing same active file concurrently. Add central Failure Museum record after actual merge. Live physical #590/#540 remain OPEN pending connected client/catalog generation and first-party ingress→response-delivery receipt. Fabric A6 #942/A7 #943 still block active fleet rollout, Fabric #1398/#1400 authorization separate; AIfordable #370/ Fabric #972 real Claude Q7 NO_DISPATCH.

## Forbidden
No live proxy/tunnel configuration change, no direct host login, no token access or logging, no retries, no paid API, no generic remote commands.
