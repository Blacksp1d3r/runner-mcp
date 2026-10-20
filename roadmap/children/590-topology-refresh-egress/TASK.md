# #590 — Topology refresh credential egress hardening

## Scope and owner
- Parent: Runner-MCP #590 connector reliability/security
- Child PR: #668, stacked on release PR #661, source-only
- Boundary: `src/runner_mcp/tunnel_topology_refresh.py` and targeted tests
- Do not mix with #651's already-merged LocalMCPClient transport fix

## Source problem
The fixed relay topology request carries a private credential in `X-AIfordable-Runner-Credential` and previously used default `urllib.request.urlopen`. Python standard-library redirects on POST 301/302/303 may forward that header to another URL. Default proxy handlers may use environment proxy settings. The risk has only been reproduced offline with synthetic values; no real credential leakage is known.

## Bounded acceptance
1. A private, per-call urllib opener explicitly disables proxies and redirects without changing process-global handlers.
2. Every 30x, including same-origin and cross-origin changes, terminates without forwarding credentials, retrying or persisting new topology evidence.
3. Synthetic tests cover hostile proxy variables, 301/302/303/307/308 and secret-free error reporting. Existing tests for valid attestation, TTL, binding and strict config must remain passing.
4. A unique patch version above 0.1.4 is consistently reflected in package and registry metadata. Candidate is 0.1.5.
5. Exact-head Ruff, pytest, tool-catalogue baseline, attribution and clean Ubuntu install must pass; independent review and protected merge separately required.

## Boundaries
Do not run topology-refresh on the real server before a reviewed release. No host/tunnel/process/credential mutations from this source child. Do not deploy PR #668 or treat a stacked draft as a production release. The user-installed 0.1.4 has a previous-venv recovery copy and remains separate from this child. Claude Q7 and original-client 95-tool catalogue activation remain gated.
