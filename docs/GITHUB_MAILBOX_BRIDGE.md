# GitHub mailbox bridge

Date documented: 2026-09-20

Runner MCP can be used with a private GitHub mailbox pattern when a direct private MCP connection is not available or is not the preferred transport.

The intended chain is:

```text
AI client
  -> GitHub request mailbox
  -> server-side watcher
  -> Runner MCP
  -> configured project
  -> GitHub result mailbox
  -> AI client
```

This is a transport pattern, not a bypass around Runner MCP. The watcher must stay narrow and must submit only allow-listed Runner MCP operations.

## Why this exists

The bridge provides a zero-additional-service-cost path for controlled development work while keeping the Runner MCP host private.

It avoids depending on a general-purpose remote desktop or remote shell connector for routine code/test work. GitHub remains the code collaboration surface, while Runner MCP remains the local execution and safety boundary.

The bridge does not require a public inbound Runner MCP port. A private watcher can pull requests and push sanitized results using credentials stored only on the host.

## What belongs where

Public Runner MCP repository:

- protocol rules;
- request validation;
- security invariants;
- generic examples with placeholders;
- tests proving that unsupported input fails closed.

Private GitHub mailbox/configuration:

- actual request and result branches or repositories;
- deployment-specific watcher configuration;
- credentials;
- any operational metadata that could reveal private infrastructure.

Runner MCP host:

- the watcher process;
- private Runner MCP configuration;
- project roots;
- test executables;
- credentials and tokens;
- job storage and logs.

Real infrastructure details must never be copied into the public repository.

## Supported bridge actions

Protocol version 1 deliberately exposes only:

- `list_projects`
- `safety_status`
- `project_status`
- `project_capabilities`
- `sync_project`
- `list_test_profiles`
- `run_tests`
- `queue_status`
- `worker_status`
- `job_status`
- `cancel_job`

The bridge must not accept:

- arbitrary shell commands;
- executable paths;
- environment-variable names or values;
- filesystem paths;
- service names;
- arbitrary MCP tool names;
- migration, deployment, rollback or restore requests.

High-risk migration/deployment/rollback flows keep their existing Runner MCP approval model and are not enabled through the mailbox bridge.

## Request shape

A request is a small UTF-8 JSON object.

Examples:

```json
{
  "protocol_version": 1,
  "request_id": "req-001",
  "action": "project_status",
  "project": "demo"
}
```

```json
{
  "protocol_version": 1,
  "request_id": "req-002",
  "action": "run_tests",
  "project": "demo",
  "profile": "unit"
}
```

A source synchronization request is commit-pinned and accepts no branch, path, remote or command input:

```json
{
  "protocol_version": 1,
  "request_id": "req-sync",
  "action": "sync_project",
  "project": "demo",
  "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

The sync operation is staging-only, requires a clean working tree, rejects submodules, verifies that `origin` matches the configured GitHub repository, fetches only through that configured origin, verifies the commit is reachable from `origin/*`, and refuses to run while tests for that project are queued or active.

For Python projects, `list_test_profiles` may also expose the fixed adapter presets `pytest` and `ruff` when the corresponding executable is safely detected inside the project virtual environment. These presets take no mailbox-supplied executable, argv, cwd or environment input. `custom` is never implicitly exposed.

A successful `run_tests` request accepts the predefined test job and returns its opaque job ID immediately. The mailbox does not wait for the test process to finish. Later status or cancellation uses a separate request:

```json
{
  "protocol_version": 1,
  "request_id": "req-003",
  "action": "job_status",
  "job_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Rules:

- unknown JSON fields are rejected;
- duplicate JSON keys are rejected;
- the request body is size-bounded;
- project and profile identifiers use the same safe identifier shape as Runner MCP configuration;
- job actions accept only a validated opaque Runner MCP job ID;
- action-specific arguments are enforced;
- the action itself comes from a fixed enum, never directly from user-supplied tool text.

The public implementation is in `runner_mcp.bridge_protocol`.

## Result shape

Protocol version 1 also defines a strict result envelope. Results are UTF-8 JSON, size-bounded and tied to the original `request_id` and action.

A successful result has this general shape:

```json
{
  "protocol_version": 1,
  "request_id": "req-001",
  "action": "project_status",
  "state": "completed",
  "data": {
    "project": "demo",
    "healthy": true
  }
}
```

A failed result uses a small safe error code instead of raw exception or process output:

```json
{
  "protocol_version": 1,
  "request_id": "req-002",
  "action": "run_tests",
  "state": "failed",
  "error_code": "TEST_FAILED",
  "summary": "The allow-listed Runner MCP action failed"
}
```

Result rules:

- unknown fields and duplicate keys fail closed;
- failed results cannot carry arbitrary data payloads;
- result collections, nesting and string sizes are bounded;
- keys associated with credentials, environment values, commands, executable paths, service units, hosts, URLs and similar private metadata are redacted;
- absolute filesystem locations and URLs found in result values are redacted;
- unsupported result value types are rejected;
- serialization is capped before anything is written to the mailbox.

The bridge result scrubber is a second boundary, not a replacement for safe Runner MCP tool output.

## Replay protection

The public package includes a small local replay ledger in `runner_mcp.bridge_replay`.

For each accepted request it stores only:

- the request ID;
- a SHA-256 fingerprint of the canonical validated request;
- the allow-listed action name;
- lifecycle state: `claimed` or `completed`;
- the first-seen timestamp;
- a completion timestamp only after the safe result is durable.

Project names, profile names, paths, credentials and result data are not stored in the replay ledger.

Behavior is fail-closed:

- a new request ID is claimed once;
- the same ID with the same fingerprint is reported as a duplicate and must not be re-executed;
- the same ID with changed content is rejected;
- corrupt or oversized ledger data is rejected;
- the ledger file is restricted to the service account and symlink targets are refused;
- capacity exhaustion blocks new execution rather than silently forgetting earlier request IDs.

The private watcher should claim a request before invoking Runner MCP, persist the bounded safe result, then mark the request completed. A duplicate completed request must never run again.

A claimed request with no result after watcher restart is treated as ambiguous and is not automatically re-executed. A completed request with a missing transport result is also not re-executed; the watcher may republish a previously persisted safe result if one exists.

See [WATCHER_RESILIENCE.md](WATCHER_RESILIENCE.md) for heartbeat, stale-request classification and restart recovery.

## When to use the bridge

Use the GitHub mailbox bridge for ordinary project inspection and predefined test execution when the AI client can work with GitHub but cannot directly reach the private Runner MCP service.

For source changes, use GitHub directly. Do not send source code through the operational mailbox.

For local status and tests, use the mailbox bridge.

For high-risk state changes, use the existing local approval workflow instead of expanding the mailbox allow-list.

## Watcher requirements

A compatible private watcher should:

1. read only from its configured request mailbox;
2. validate every request using the strict Runner MCP bridge protocol;
3. map the action through the fixed allow-list;
4. invoke Runner MCP without constructing a shell command;
5. write only sanitized result data to the result mailbox;
6. claim the request ID through replay protection before execution;
7. never execute a duplicate request again;
8. serialize only the bounded, scrubbed result envelope;
9. never copy private paths, credentials, environment values or raw unsafe logs into GitHub;
10. mark replay lifecycle completed only after the safe result is durable;
11. classify ambiguous or missing-result restart states without blind re-execution;
12. publish only the sanitized heartbeat contract for watcher liveness;
13. retry only transient transport operations, never the Runner MCP action itself;
14. stop mutating work when Runner MCP's operator emergency stop is active.

The reusable processing core is now transport-neutral in `runner_mcp.bridge_processor`. It enforces request parsing, replay lifecycle, explicit allow-listed execution, result scrubbing, durable result persistence ordering and fail-closed recovery states. GitHub polling, credentials, branch names, result locations and supervisor configuration remain private transport concerns.

## Proven operating pattern

On 2026-09-20 the private mailbox pattern was successfully piloted as the standard development transport across multiple configured projects. The public repository records only the generic architecture and guarantees; private branch/repository names, host details and operational credentials remain outside the public codebase.


## Transport-neutral processor

`BridgeProcessor` accepts three local components:

- a shared `BridgeReplayLedger`;
- an explicit `BridgeExecutor` with exactly the ten mailbox-allow-listed operations;
- a `BridgeResultSink` that receives only request ID plus the already-scrubbed serialized result.

The executor interface deliberately does not expose a generic `invoke(tool_name, args)` method.

For `run_tests`, the executor starts the configured allow-listed test profile and returns the accepted Runner MCP job record immediately. Test execution continues in the bounded Runner MCP scheduler. The mailbox exposes only safe `job_status` and `cancel_job` follow-up actions plus aggregate `queue_status` and `worker_status`; raw test-log retrieval is not a mailbox action.

Processing order is fixed:

1. parse strict request;
2. claim replay ID;
3. execute one explicit allow-listed operation;
4. build and scrub the result envelope;
5. persist the safe result through the transport sink;
6. mark replay lifecycle completed.

If step 5 fails, step 6 does not happen and the action is never automatically rerun. If step 6 fails after a durable result exists, restart recovery sees the transport result and must not rerun the action.


## Fixed-host GitHub transport

The reusable GitHub transport is implemented in `runner_mcp.github_mailbox`.

It deliberately accepts configuration for only:

- a validated `owner/repository` identifier;
- a validated request ref;
- a validated result ref;
- a runtime GitHub token;
- a bounded HTTP timeout.

The API origin is fixed to GitHub. Request/result/heartbeat paths are generated internally below the mailbox root. A caller cannot supply an arbitrary URL, filesystem path, executable, service name or shell command.

GitHub response handling is fail-closed:

- API responses are size-bounded;
- duplicate JSON keys are rejected;
- `NaN` and other non-standard JSON constants are rejected;
- file SHA and base64 metadata are validated;
- normal GitHub line-wrapped base64 is accepted after whitespace removal and strict decode validation;
- request payload ID must match the request filename;
- conflicting pre-existing result content is never overwritten.

Result publication implements the public `BridgeResultSink` boundary. GitHub read/write transport failures during result persistence become a safe persistence-recovery outcome in `BridgeProcessor`; they do not authorize action replay.

Heartbeat publication uses only the bounded public watcher-heartbeat schema.

Repository names, refs, credentials and supervisor/service configuration remain deployment-specific private configuration. The public package contains no real installation values.


## Incremental request discovery

The GitHub transport exposes the current request-ref commit SHA and a bounded fast-forward compare operation.

The watcher stores the last safely handled request-ref SHA locally. On each cycle it compares that SHA with the current request head and considers only added or modified direct JSON request files below the fixed request mailbox.

The compare fails closed when:

- the request ref is not a strict fast-forward from the cursor;
- the compare response may be truncated;
- a request file is deleted or renamed;
- a nested or malformed request path appears;
- a request ID is malformed or duplicated.

This avoids repeatedly scanning historical mailbox contents and reduces GitHub API load without weakening replay protection.


## Loopback MCP executor

The reusable local executor is implemented in `runner_mcp.bridge_mcp_executor`.

It is intentionally narrower than a general MCP client:

- the endpoint must be loopback-only and use the `/mcp` path;
- bearer credentials are supplied separately and never embedded in the URL;
- only the fixed bridge operations are exposed by the executor;
- internal tool dispatch is private and allow-listed;
- `run_tests` returns the accepted job without terminal polling;
- `job_status` and `cancel_job` accept only a validated opaque job ID;
- `get_test_log` is not called by the bridge executor.

For a test run, the executor returns only safe persisted job metadata. Raw logs, local paths, commands and private runtime details are not added to the mailbox result.

MCP JSON/SSE parsing is strict and bounded. Invalid session/job identifiers or transport/server/tool failures become generic adapter errors; raw response bodies and exception details are not propagated into the bridge result.

This executor lets a private watcher become a thin bootstrap over public Runner MCP components rather than maintaining its own duplicate request validator, MCP handshake or generic tool-dispatch logic.


## Private-config runtime and CLI

The reusable runtime is implemented in `runner_mcp.github_runtime` and is exposed through the normal `runner-mcp` CLI.

Private mailbox configuration is managed with:

```text
runner-mcp github-mailbox configure
runner-mcp github-mailbox status
runner-mcp github-mailbox remove
```

The repository identifier and refs are stored with the GitHub token in the existing private runtime environment. By default the token is entered through a hidden prompt. For a secure operator pipeline, `github-mailbox configure --token-stdin` can instead read one token from standard input. There is deliberately no `--token` argument, so credentials do not need to appear in process arguments or shell history. Runner MCP does not echo the token. The status command reports only whether the mailbox is configured.

Watcher lifecycle is managed with:

```text
runner-mcp github-watcher bootstrap
runner-mcp github-watcher once
runner-mcp github-watcher run
```

Bootstrap is explicit. It records the current request-ref head and does not replay historical mailbox requests.

Continuous mode separates request polling from heartbeat publication. Request polling can therefore remain responsive without creating a heartbeat commit on every cycle. Heartbeat intervals are bounded, and state changes can trigger an immediate heartbeat refresh.

The runtime derives its replay ledger and cursor locations inside the private configuration directory. It reuses the existing private Runner MCP bearer credential for loopback MCP access and never prints either credential.

Setup overwrite preserves already-configured mailbox and database secrets. Explicit Runner MCP bearer-token rotation rotates only that bearer credential and does not erase unrelated private secrets.
