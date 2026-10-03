# First-party ChatGPT/Codex control path

Runner MCP and Runner Fabric are the normal control path for recurring development operations.

The intended chain is:

`ChatGPT/Codex plugin -> Runner MCP MCP -> coarse Fabric work-unit -> Agent Bus / Fabric`

Broad remote host tooling is break-glass only. It is not the normal orchestration path and must not
be used to bypass a blocked Runner MCP or Runner Fabric policy decision.

## Existing authority boundary

This plugin packaging does not create a new backend.

Runner MCP already exposes the three coarse Fabric tools only when the private Fabric bridge is
configured:

- `fabric_run_work_unit`
- `fabric_get_work_unit`
- `fabric_cancel_work_unit`

Runner Fabric remains responsible for orchestration, policy, fencing, validation, source mutation,
audit and recovery. Runner MCP remains responsible for its MCP authentication, bounded bridge
validation and audit boundary.

Do not add generic shell, arbitrary Git/GitHub forwarding, arbitrary paths, environment injection or
provider credentials to make a client integration more convenient.

## Generate a private plugin package

The package is generated locally. Do not commit generated connection metadata.

### Already registered MCP app

After registering the Runner MCP connection in an eligible ChatGPT/workspace developer environment,
render the local package with its technical application identifier:

```text
runner-mcp plugin-package registered-app \
  --app-id <registered-app-id> \
  --output <private-output-directory>
```

The command accepts the browser-facing `plugin_asdk_app_...` form and stores the canonical package
identifier. The generated `.app.json` is local connection metadata and should remain private.

### HTTP MCP for Codex or a self-hosted agent environment

Use a reachable HTTPS MCP endpoint, or loopback HTTP when the agent executor runs on the same host:

```text
runner-mcp plugin-package http \
  --url https://example.invalid/mcp \
  --bearer-env RUNNER_MCP_PLUGIN_TOKEN \
  --output <private-output-directory>
```

The package stores only the environment-variable name. It never reads or writes the bearer-token
value.

Do not place a bearer token in command arguments, JSON manifests, skill files or source control.

## Private connectivity

Runner MCP remains self-hosted and local-first.

Do not:
- make a public bind merely to satisfy a plugin client;
- commit a private endpoint, tunnel URL, registered application identifier or bearer token;
- reconstruct Agent Bus credentials in the client;
- use a third-party MCP directory or gateway as a required runtime dependency.

Use a reviewed private connectivity mechanism appropriate to the client environment. If the current
ChatGPT account/workspace cannot attach the private MCP server with the required tool permissions,
keep the package prepared and use an eligible first-party client/runtime rather than weakening Runner
MCP.

## Agent workflow

The generated skill tells the agent to:

1. submit one bounded semantic repository change through `fabric_run_work_unit`;
2. use `fabric_get_work_unit` only when status is actually needed instead of tight polling;
3. use `fabric_cancel_work_unit` only for an explicit cancellation or safety reason;
4. treat Fabric policy, fencing, approval, emergency-stop and validation results as authoritative;
5. never replace a denied action with a broad remote-control shortcut.

Direct GitHub connector choreography may remain a bootstrap/fallback path while the first-party
plugin is being connected, but the target architecture is the coarse Fabric work-unit boundary.

## Generated-package safety

The packager:
- creates the package root with mode 0700;
- creates package files with mode 0600;
- rejects unsafe or credential-bearing endpoint URLs;
- accepts external HTTP only over HTTPS and permits plain HTTP only for loopback;
- refuses to overwrite a non-empty directory unless it is a package previously created by Runner MCP;
- does not accept a bearer-token value as an argument;
- keeps output location hidden unless `--show-output-location` is explicitly requested.

Generated plugin packages contain local connection metadata and should not be treated as public
release artifacts.
