# Changelog

All notable user-visible changes to Runner MCP will be documented here.

Runner MCP is under active development. Until the first tagged release, changes are collected under **Unreleased**.

## Unreleased

### Added

- security-first self-hosted MCP server foundation;
- allow-listed project registry and safe project file access;
- external operator emergency stop and retention safety policy;
- predefined asynchronous test profiles with bounded scrubbed logs;
- allow-listed staging service controls;
- PostgreSQL backup and migration controls;
- staging-only deployment and one-step code rollback;
- built-in project adapter foundation;
- short-lived local human approval gates for higher-risk staging actions;
- GitHub mailbox bridge protocol with a strict allow-list;
- bounded bridge result envelopes and replay protection;
- strict terminal task-completion events with deterministic notification IDs;
- watcher heartbeat, replay lifecycle and fail-closed restart-recovery primitives;
- transport-neutral bridge processor with explicit allow-listed executor and durable-result ordering;
- fixed-host GitHub mailbox transport with strict JSON/base64 validation and create-once results;
- incremental GitHub mailbox watcher with explicit bootstrap and restart-safe cursor reconciliation;
- loopback-only MCP bridge executor with strict JSON/SSE parsing and bounded test polling;
- interactive setup, doctor, guide and configuration-management CLI;
- public CI for this public repository;
- Fools2Tools project identity;
- five-minute local demo, release checklist and launch-readiness documentation.

### Security

- arbitrary shell input is not part of the normal MCP or mailbox interfaces;
- unknown MCP arguments fail closed;
- bridge requests/results reject duplicate keys and non-standard JSON constants;
- bridge results are bounded and conservatively scrubbed;
- duplicate mailbox request IDs cannot be silently re-executed;
- notification delivery is separated from task execution so a delivery retry cannot rerun the task;
- ambiguous or missing-result watcher recovery states do not automatically re-execute operational actions;
- result persistence/finalization failures do not authorize bridge action replay;
- GitHub mailbox transport failures are classified and kept inside the persistence/recovery boundary;
- watcher restarts reuse cursor/replay state and never treat process restart as permission to replay actions;
- bridge execution cannot target a non-loopback MCP endpoint and never fetches test logs;
- production mutations remain disabled;
- database restore remains unimplemented rather than being automated unsafely.

### Known limitations

- service auto-start packaging is still being improved;
- guided private-tunnel/reverse-proxy onboarding is not yet one-click;
- untrusted public-fork code is not sandboxed for execution on a privileged persistent runner;
- PostgreSQL restore/PITR orchestration and automated retention pruning are not implemented;
- the private mailbox watcher still needs to migrate fully to the shared public protocol implementation.

## Release format

When the first release is tagged, move the relevant entries from **Unreleased** into a section such as:

```text
## 0.1.0 - YYYY-MM-DD
```

Release notes should link to the exact validated tag/commit and call out security-boundary changes explicitly.
