# Runner-MCP #642 — source-only authenticated HTTP wire rehearsal

The previously merged #1014 proves direct Python SDK `MCPServer.call_tool`
interception. This TEST-ONLY continuation now exercises a real HTTP
`initialize` / `notifications/initialized` / `tools/list` /
`tools/call` flow using the existing Starlette `create_app` and
`TestClient` on disposable files.

- With a deliberately unqualified internal host evidence provider, the
  already registered `read_project_file` remains advertised yet
  `tools/call` returns `HOST_TOOL_NOT_PERMITTED`, the actual handler is not
  invoked, and a bounded refusal is written to the existing audit.
- Failure in the synthetic private evidence provider is rejected without
  leaking exception details.
- An app built with the normal default provider argument unchanged remains
  compatible with the existing authenticated read handler.

No real signed policy, physical server, active loaded-wheel attestation,
real Claude/Qwen tool/ACK, update or deployment. The opt-in is not permitted
on a production host until #642's independent service and runtime provenance
has been verified. This is strictly tests/docs, so it introduces no release
code change and must keep the project's version reservation intact.
