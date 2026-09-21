# Runner MCP v0.1.0 release notes draft

This file is a release-candidate draft. Do not treat it as a published release announcement until the exact tagged commit has passed the full public validation workflow.

Runner MCP is a security-first, self-hosted MCP service for controlled development and staging operations. Its normal interfaces expose configured capabilities rather than a general-purpose remote shell.

## What is included

The first alpha release includes:

- authenticated MCP with strict argument validation and bounded output;
- allow-listed project inspection and safe file access;
- predefined asynchronous test profiles with persistent bounded jobs;
- fair multi-project test scheduling with explicit parallel-safe opt-in;
- external operator emergency stop and rollback/retention safeguards;
- controlled staging service, PostgreSQL backup/migration, deployment and one-step rollback foundations;
- short-lived local approval gates for higher-risk staging actions;
- built-in project adapters and safe capability inspection;
- versioned GitHub mailbox protocol with replay protection, restart-safe cursor handling and bounded concurrent request workers;
- commit-pinned allow-listed project synchronization through the mailbox;
- safe queue/worker/job observability and cancellation;
- independent exactly-once completion notification delivery;
- explicit fail-closed recovery for already-claimed mailbox requests whose result is missing, without action replay;
- managed non-root autostart using systemd user services when available or a lock-protected managed cron fallback;
- interactive setup, doctor, guide, operator wrapper, Quickstart and a clean five-minute demo.

## Why the boundaries matter

Runner MCP intentionally separates source collaboration, operational requests, execution and human approval.

The GitHub mailbox accepts only its documented fixed action enum. It does not accept shell commands, executable paths, filesystem paths, environment values, service names or arbitrary MCP tool names from the request.

Ambiguous recovery states do not authorize rerunning work. A claimed request with no durable result remains fail-closed. The local recovery command can publish only a terminal safe failure after exact request/replay checks; it does not invoke the original action.

Notification delivery is similarly separate from execution. Retrying a notification cannot rerun the task.

## Upgrade notes

This is the first tagged alpha, so there is no earlier public release to migrate from.

Operators testing development snapshots should nevertheless review the following before upgrading:

- use the current protocol-v1 mailbox request shape;
- keep existing watcher replay/cursor state; do not delete or reset it during upgrades;
- replace any legacy private pilot watcher with the shared Runner MCP watcher runtime;
- use explicit watcher/bootstrap commands rather than silently skipping historical mailbox state;
- if using autostart, remove or migrate unmanaged Runner MCP cron entries before enabling the managed cron backend;
- keep all private repository/ref/token, project paths and executable definitions in private host configuration.

## Known limitations

- Runner MCP is not a sandbox for hostile or untrusted project code;
- production mutations remain disabled;
- database restore and PostgreSQL PITR/WAL orchestration are not implemented;
- automated backup/release retention pruning is not implemented;
- Runner MCP guides private tunnel/reverse-proxy/VPN choices but deliberately leaves third-party provisioning, credentials and host network policy external;
- managed-cron removal stops future supervision but deliberately does not blindly terminate an already-running component;
- the optional completion notifier needs a private GitHub destination and credential;
- public launch/registry/community publication remains a separate human-controlled step.

## Validation required for the release tag

Before publishing v0.1.0, the exact tag commit must have all of these green:

- Python 3.12 compile;
- Ruff;
- complete pytest suite;
- whitespace validation;
- clean Ubuntu 24.04 five-minute demo;
- built wheel and source-distribution validation;
- clean install from the built wheel with CLI smoke checks;
- public-repository privacy review.

Record the exact passing test count and commit SHA in the GitHub release notes when the tag is created.

## Security reporting

Use the repository security policy for vulnerability reports. Do not put real hostnames, addresses, usernames, paths, tokens, credentials, database endpoints, service identifiers or customer data in public issues.
