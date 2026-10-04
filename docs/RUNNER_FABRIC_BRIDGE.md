# Optional Runner Fabric bridge

Runner MCP can optionally expose a narrow transport bridge to a **separately running Runner Fabric**
instance on the same host.

This does not move Runner Fabric orchestration into Runner MCP. Runner MCP remains the
security-first MCP transport/execution product; Runner Fabric remains the orchestration/control
plane.

## Why

Without a coarse Fabric tool boundary, an AI client may need many individual GitHub/Git/test/status
operations to complete one repository task. Those calls bypass Runner Fabric's GitHub Gateway,
cache, single-flight deduplication, webhook state and API budget manager.

With the bridge configured, the client can use one bounded Fabric work-unit instead:

```text
AI client
  |
  | fabric_run_work_unit(...)
  v
Runner MCP
  |
  | loopback MCP, fixed three-tool allow-list
  v
Runner Fabric
  |
  +-- reconcile
  +-- modify bounded change plan
  +-- validate / bounded repair
  +-- commit
  +-- push
  +-- report
```

## Private configuration

The bridge is disabled by default.

When Runner Fabric's local MCP endpoint is available, configure both values in Runner MCP's private
runtime environment:

```text
RUNNER_MCP_FABRIC_RESOURCE_URL=http://127.0.0.1:PORT/mcp
RUNNER_MCP_FABRIC_BEARER_TOKEN=<private-strong-token>
```

The endpoint is deliberately loopback-only in this first bridge. The token must contain at least
32 characters. Neither value is returned by MCP tools or written to audit output.

Do not commit real endpoints, ports or tokens to this repository.

## Exposed tools

Exactly three additional tools are registered when the bridge is configured:

- `fabric_run_work_unit`
- `fabric_get_work_unit`
- `fabric_cancel_work_unit`

When the bridge is not configured, these tools are not registered and the normal Runner MCP tool
surface remains unchanged.

Runner MCP validates both request bounds and the bounded Fabric response shape. Unknown Fabric
response fields fail closed rather than being forwarded to the AI client.

## Deliberately not exposed

The bridge does **not** add:

- generic GitHub API calls;
- Git commands;
- arbitrary shell or executable selection;
- arbitrary filesystem paths;
- arbitrary test commands;
- workflow/check polling primitives;
- provider URLs, headers or tokens.

Those are internal implementation details owned by Runner Fabric and its GitHub Gateway.

## Authority

The bridge is transport only. It does not make a reserved or denied Fabric capability available.

Runner Fabric remains responsible for work-unit policy, current fencing, approvals, credentials,
workspace isolation, source-control authority, audit and recovery. Runner MCP only forwards the
bounded request and bounded result.


## Managed Fabric update artifact access

Managed Runner Fabric updates are separate from the loopback work-unit bridge. Runner MCP verifies
an exact successful canonical GitHub Actions run and exact named update artifact before applying a
bundle.

The private `RUNNER_MCP_GITHUB_TOKEN` used by Runner MCP must be able to read the
`Blacksp1d3r/Runner-Fabric` repository's Actions metadata and artifacts. For a fine-grained token
or GitHub App installation this means repository access to Runner Fabric plus **Actions: Read**
(and normal repository metadata read access). Do not grant write/admin rights merely to make update
downloads work.

Use the read-only `fabric_update_readiness(commit)` tool before a managed update when diagnosing
access. It returns only the requested commit and `artifact_ready=true` on success. Failures are
bounded to categories such as:

- `actions_run_unavailable` — the exact canonical successful run cannot be read or selected;
- `artifact_metadata_unavailable` — the exact named non-expired artifact cannot be read or selected;
- `artifact_download_unavailable` — the selected archive cannot be safely downloaded.

No GitHub token, repository response body, redirect URL, artifact ID or private runtime detail is
returned through these categories.
