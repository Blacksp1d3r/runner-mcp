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
- `list_test_profiles`
- `run_tests`

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

Rules:

- unknown JSON fields are rejected;
- duplicate JSON keys are rejected;
- the request body is size-bounded;
- project and profile identifiers use the same safe identifier shape as Runner MCP configuration;
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
  "summary": "The predefined test profile did not complete successfully"
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
- an explicit `BridgeExecutor` with exactly the six mailbox-allow-listed operations;
- a `BridgeResultSink` that receives only request ID plus the already-scrubbed serialized result.

The executor interface deliberately does not expose a generic `invoke(tool_name, args)` method.

For `run_tests`, the executor method is `run_tests_to_completion(project, suite)`. A private adapter may implement this by starting the configured Runner MCP test profile and polling its existing bounded job-status API until terminal state. The mailbox itself does not gain `test_status` or log-fetch actions.

Processing order is fixed:

1. parse strict request;
2. claim replay ID;
3. execute one explicit allow-listed operation;
4. build and scrub the result envelope;
5. persist the safe result through the transport sink;
6. mark replay lifecycle completed.

If step 5 fails, step 6 does not happen and the action is never automatically rerun. If step 6 fails after a durable result exists, restart recovery sees the transport result and must not rerun the action.
