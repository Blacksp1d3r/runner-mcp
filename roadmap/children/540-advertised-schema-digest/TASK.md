# #540 — exact active advertised MCP schema digest (source child)

## Scope and owner
Runner-MCP connector communication owner. Server-side single-session source test only. Runner-MCP #540 live client-catalogue generation and fleet/host permission gates #642 remain independently blocked. Fabric #942/#943 release safety, #1398/#1400 authorization, #972 and AIfordable #370 real worker are separate owners.

## Contract
At server initialization the build identity `interface_schema_digest` is computed from the active `mcp.list_tools()` registrations sorted by tool name, retaining exact `input_schema` and `output_schema` structures. Compare independently to the *actual advertised* authenticated HTTP `tools/list` response in the same initialized MCP session, using the canonical sorted JSON hash. Do not infer schema provenance from a hand-maintained list or package version.

## Verification
- Assert exact response JSON-RPC IDs and no errors; tools/list does not expose duplicate tool names.
- Require source-merged Q7 preflight and first-party build/status/doctor tools to be actually advertised in the isolated session.
- Hash actual advertised tool name+inputSchema+outputSchema; compare against active build identity fingerprint.
- Deny leakage of bearer and temporary source path in build identity.
- Exact-head Ruff/pytest, built artifact, clean demo, attribution before merge.

## Live limitations
An isolated ASGI test does not prove any deployed host uses this source revision, that the ChatGPT client's cached catalogue is refreshed, that the tunnel routes to the right machine, or that request and response travel along one approved path. Production #540 and #590 require independently trusted release/process/catalogue fingerprints, stale-session negative proof and A6/A7 rollback-ready live convergence, plus private per-request correlated receipts. No server, tool client, tunnel or worker live mutation.
