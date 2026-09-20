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
6. record request IDs so the same request cannot be executed twice accidentally;
7. never copy private paths, credentials, environment values or raw unsafe logs into GitHub;
8. stop mutating work when Runner MCP's operator emergency stop is active.

The watcher is not yet part of the public package. The public protocol is intentionally separated first so an existing private pilot can migrate to shared, tested validation without weakening its current safety boundary.

## Proven operating pattern

On 2026-09-20 the private mailbox pattern was successfully piloted as the standard development transport across multiple configured projects. The public repository records only the generic architecture and guarantees; private branch/repository names, host details and operational credentials remain outside the public codebase.
