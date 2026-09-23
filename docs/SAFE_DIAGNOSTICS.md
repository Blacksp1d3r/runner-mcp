# Safe watcher diagnostics contract

This contract defines the only information Runner MCP long-running watcher,
notifier, and supervisor components may place in normal operator diagnostics.
It is intentionally category-only. The purpose is to make lifecycle and
failure state observable without creating a second path for private runtime
data to escape.

The executable contract lives in `runner_mcp.safe_diagnostics`.
`render_safe_diagnostic()` accepts only enum members for component, event,
and optional error category. It has no arbitrary message, exception, payload,
metadata, identifier, path, URL, or context field.

## Allow-listed components

- `github_watcher`
- `completion_watcher`
- `cron_supervisor`

These are generic product component names, not hostnames or systemd unit names.

## Allow-listed event categories

Lifecycle:

- `lifecycle_started`
- `lifecycle_stopped`

Cycle outcome:

- `cycle_healthy`
- `cycle_degraded`
- `cycle_uninitialized`

Bounded retry class:

- `retry_timeout`
- `retry_rate_limited`
- `retry_unavailable`
- `retry_exhausted`

Supervisor restart:

- `supervisor_restart_requested`
- `supervisor_restart_handoff`
- `supervisor_restart_failed`

When a failure needs a stable identity beyond the event category, consumers
must use one of the bounded `DiagnosticErrorCategory` values. They must never
append `str(exc)`, `repr(exc)`, traceback text, or caller-supplied data.

## Forbidden output

Normal operator diagnostics must never contain:

- request or result payloads, including serialized bridge envelopes;
- request IDs, result IDs, job IDs, replay fingerprints, or mailbox object IDs;
- filesystem paths, repository paths, backup paths, or config locations;
- URLs, repository names, GitHub refs, API endpoints, or destination details;
- credentials, tokens, authorization headers, environment values, or secrets;
- hostnames, IP addresses, usernames, service-account names, or service-unit names;
- arbitrary exception text, subprocess stderr/stdout, or stack traces;
- notification message bodies, mentions, issue numbers, or other destination identity;
- test logs or deployment logs.

A component may still raise a bounded typed exception to its caller. This
contract concerns normal long-running operator diagnostics and must not be
used as permission to broaden exception or API output elsewhere.

## Production consumers and remaining integrations

The contract is integrated incrementally so each component can be reviewed for
event mapping and rate/noise behavior without changing the safe schema:

1. `GitHubWatcherRuntime.run_forever()` in `github_runtime.py` is integrated
   for lifecycle start, watcher cycle state and bounded restart failure.

2. `run_cron_component()` in `cron_autostart.py` is integrated for
   supervisor lock already-held state, component exec handoff and bounded
   start/restart failure. It never emits the selected component, argv,
   executable/config path or caught exception text.

3. `CompletionNotifierRuntime.run_forever()` in `completion_delivery.py`
   remains the next bounded integration for lifecycle, healthy/degraded cycle
   state and bounded restart failure.

4. The CLI entry points that currently print the fixed
   `"... watcher running/stopped"` messages may later delegate those lifecycle
   messages to the same renderer. This is not required to adopt the contract.

The server/uvicorn HTTP access logger is intentionally outside this first
contract. Its request logging has different data-shape and privacy concerns
and should be reviewed separately rather than silently folded into watcher
diagnostics.

## Integration rule

Production integrations must pass enum values directly and may not construct a
diagnostic from caught exception text. New components remain separate small
slices so their event mapping and rate/noise behavior can be reviewed without
changing the safe schema.
