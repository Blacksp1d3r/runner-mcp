# Completion feedback contract

Runner MCP separates execution from notification.

A task result is authoritative. A notification is only a small, safe signal that the result reached a terminal state.

This separation matters because a failed notification must never cause the task to run again.

## Goals

Completion feedback exists so an operator does not need to poll every chat, pull request or mailbox result manually.

The generic contract supports terminal states only:

- `succeeded`
- `failed`
- `cancelled`

There is deliberately no `running` state in the completion event.

## Public event shape

The reusable implementation is in `runner_mcp.completion_feedback`.

A test completion event looks like:

```json
{
  "event_version": 1,
  "event_id": "0123456789abcdef0123456789abcdef",
  "source": "mailbox_result",
  "operation": "run_tests",
  "project": "demo",
  "profile": "unit",
  "state": "succeeded",
  "requires_attention": false
}
```

The event is intentionally small.

It does not contain:

- filesystem paths;
- hostnames or URLs;
- credentials or tokens;
- service names;
- environment values;
- raw process output;
- raw logs;
- database details.

## Deterministic event ID

The event ID is derived from a private source record identifier plus a fixed source type.

The source identifier itself is not exposed in the event.

This gives notification transports a stable idempotency key. A transport can mark a notification with that event ID and detect that the same completion was already delivered.

The notification event ID does not authorize any Runner MCP action.

## Execution and delivery are independent

The expected flow is:

1. Runner MCP executes or observes the task.
2. The authoritative result is persisted.
3. A completion event is derived from that persisted result.
4. A notification transport checks whether this event ID was already delivered.
5. The transport publishes a small user-facing notification.
6. Delivery failure may be retried without re-running the task.

A transport must never retry an operational action merely because notification delivery failed.

## Source/operation binding

Completion sources and operations are fail-closed bound:

- `mailbox_result` -> `run_tests`
- `test_job` -> `run_tests`
- `migration_job` -> `apply_migration`
- `deployment_job` -> `deploy_staging`
- `rollback_job` -> `rollback_release`

This prevents a validly shaped event from misrepresenting one kind of work as another.

The mailbox allow-list itself is unchanged. The presence of a completion-event type for migration/deployment/rollback does not make those actions available through the GitHub mailbox.

## Attention semantics

`requires_attention` is derived from the terminal state:

- succeeded -> false
- failed -> true
- cancelled -> true

A sender cannot independently set this flag to hide a failed result.

## Transport requirements

A notification transport should:

- use the deterministic event ID as an idempotency marker;
- serialize deliveries per destination when concurrent duplicate delivery is possible;
- retry only notification transport failures;
- keep retries bounded;
- never include private runtime information;
- keep delivery failure separate from task success/failure;
- preserve a link or reference only when that reference is safe for the destination.

Deployment-specific destinations remain private configuration.

Examples include a private GitHub issue/inbox, a future chat notification adapter, or another operator-controlled channel.

## Relationship to replay protection

Request replay protection and notification deduplication solve different problems.

Request replay protection prevents a task from executing twice.

Completion-event deduplication prevents the same finished task from notifying the operator twice.

Both use stable identifiers, but notification delivery must never call the execution path.

## Relationship to heartbeat/recovery

Completion feedback also differs from watcher liveness.

A heartbeat answers: "is the transport/watcher alive?"

Completion feedback answers: "did this task reach a terminal result?"

Stale-request recovery and heartbeat are tracked separately so a transport outage cannot be mistaken for a task result.

## Current pilot

A project-local CI pattern has already demonstrated user-facing success/failure/cancellation notifications.

A private GitHub mailbox notifier also exists for `run_tests` results. The next acceptance criterion is an end-to-end run in which a fresh Runner MCP test result produces exactly one notification through the deterministic completion-event ID.
