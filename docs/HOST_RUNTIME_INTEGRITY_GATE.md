# Host runtime integrity gate design

Status: design-only boundary for issue #155. No runtime authority is added by this document.

## Purpose

Runner MCP must not interpret a successful package reinstall as proof that a host is healthy. A live incident produced intermittent Python import corruption and process crashes alongside crash evidence from an unrelated system binary. Before an operator enables managed autostart after an install/recovery incident, Runner MCP needs a small local-only integrity decision that is independent of package installation.

## Decision surface

The gate returns exactly one public state:

- `host_integrity_clear`: the fixed diagnostics completed, the application runtime stress gate passed, and no in-window crash evidence matched the fixed process classes.
- `runtime_smoke_failed`: the repeated Runner MCP/Python stress gate failed at least once.
- `recent_process_crash_evidence`: fixed local diagnostics found in-window crash evidence for Python or a fixed unrelated system-process class.
- `diagnostics_unavailable`: the fixed diagnostic source could not be queried or its output could not be safely classified.

Anything except `host_integrity_clear` blocks automatic service activation. This is not a health certificate for hardware; it is only a bounded activation gate.

## Local-only authority

The gate is invoked only from a local operator install/recovery/autostart path. It is not an MCP tool, bridge action, mailbox action, Agent Bus action, Fabric work-unit operation or remote status expansion.

The caller cannot supply:

- journal query text, unit names, process names or executable paths;
- time windows;
- files, hosts, URLs or providers;
- shell/argv/environment values;
- arbitrary diagnostic commands.

## Fixed evidence window

Use a fixed look-back of 30 minutes immediately before the gate invocation. The implementation may inspect only kernel/system crash metadata needed to classify fatal process events. It must not return raw records.

A process crash older than the fixed window does not block a later activation by itself. A new crash resets the effective clean interval. The operator cannot shorten the interval through CLI input.

## Fixed process classes

Classification is intentionally coarse:

1. Python runtime: executable identity equivalent to the supported CPython runtime.
2. Unrelated system process: a small reviewed allow-list of package/system utilities whose crash demonstrates the problem is not confined to Runner MCP.

The exact executable identifiers belong in code constants and tests, not caller input. Runner MCP service crashes remain covered by the runtime stress gate and normal service status.

## Diagnostic adapter contract

Production implementation should use one injected adapter with a fixed method such as `recent_fatal_process_classes()`. The adapter owns the platform-specific journal query. Its result is only a set of internal enum values plus whether the query completed.

The parser must:

- cap subprocess runtime;
- cap captured bytes before parsing;
- reject malformed/oversized output;
- never propagate stdout/stderr, journal text or `str(exc)`;
- never expose process IDs, usernames, paths, hosts, kernel addresses or stack traces.

Tests inject the adapter; CI must not depend on its own journal.

## Activation ordering

1. install/recovery completes without activating managed services;
2. repeated application runtime stress completes;
3. host diagnostic adapter runs;
4. gate returns one bounded state;
5. only `host_integrity_clear` may proceed to autostart installation/enablement.

A failure does not uninstall packages, delete evidence, reboot, run memory tests, alter permissions, repair filesystems or retry indefinitely.

## False-positive policy

Fail closed for the 30-minute window. The escape hatch is human diagnosis plus time/evidence, not a force flag in remote control. If a legitimate unrelated crash matches the fixed class, the operator waits for a clean interval or performs host diagnostics and retries locally.

`diagnostics_unavailable` is distinct from crash evidence so operators know the gate lacks proof rather than falsely reporting a crash.

## Tests required before implementation

- clear adapter + passing runtime stress -> `host_integrity_clear`;
- one Python fatal event -> `recent_process_crash_evidence`;
- one fixed unrelated-system fatal event -> same blocked state;
- event outside the fixed window -> does not block;
- malformed, oversized, timed-out or unavailable diagnostics -> `diagnostics_unavailable`;
- any failed stress iteration -> `runtime_smoke_failed` regardless of later successes;
- sensitive literals injected into adapter failures never appear in public output;
- remote protocol/action enums do not gain a host-diagnostic action;
- autostart enable path cannot execute after any blocked state.

## Explicitly not proven

This design does not prove RAM, CPU, storage, kernel or hypervisor health. It does not identify the root cause of the live incident. It only prevents Runner MCP from converting insufficient or contradictory runtime evidence into automatic service activation.
