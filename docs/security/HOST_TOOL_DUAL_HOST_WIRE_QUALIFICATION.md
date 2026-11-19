# Runner-MCP #642 — synthetic dual-host real HTTP preflight (TEST ONLY)

This test extension is **not** a new service, A7 host-witness implementation,
signed policy issuer, or approval to run tools on a production host.

On the source-only #1014 SDK guard and #1015 authenticated wire tests:

- The exact registered real `build_mcp()` tool schema digest is measured by
  the existing `runner_mcp_interface_schema_digest` helper in a disposable
  process, rather than forged as a fixed test hash.
- A synthetic PRIMARY and LAB each create a real Starlette app with a private
  injected policy and the **same** authenticated `tools/list` catalogue.
- PRIMARY lacks permission for `read_project_file`: an authenticated call is
  rejected before file access, with a bounded audit denial.
- LAB has a synthetic allowlist for this same tool: the disposable file read
  succeeds. This is an in-process simulation ONLY, not a real qualification.
- Replaying LAB's permit onto PRIMARY is refused as
  `host_identity_mismatch` at the SDK HTTP dispatch.
- No grant is sourced from an MCP request field; both synthetic inputs are
  injected through the previously built internal-only test seam.

**#669 owner boundary:** the existing active-wheel owner provenance candidate
is [draft #1004](https://github.com/Blacksp1d3r/runner-mcp/pull/1004),
which remains unmerged and contains original A7/D-0037 hard-stop conditions.
Its 0.1.175 candidate metadata now trails main 0.1.176. Do not rebase,
rewrite, publish or activate draft #1004 from this test workstream. A
qualified first-party provider must eventually combine independent active
wheel/process attestation, signed expiring host policy, exact service asset,
runtime revision, schema, caller/route and existing A7/A6 recovery gates.

This PR changes tests and documentation ONLY, not the published version,
tool authorization policy, server behavior or production configuration.
