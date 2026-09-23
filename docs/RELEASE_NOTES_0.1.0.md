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
- local-only abandonment of strictly valid unclaimed mailbox requests and bounded quarantine of malformed historical requests without executor replay, ledger reset or generic cursor reset;
- race-safe malformed-request quarantine that rechecks the request head before cursor advancement;
- short per-job private test temporary directories for local IPC/Unix-socket runtimes, with restrictive permissions, log redaction and terminal cleanup;
- managed non-root autostart using systemd user services when available or a lock-protected managed cron fallback;
- interactive setup, doctor, guide, operator wrapper, Quickstart and a clean five-minute demo;
- canonical-main-only commit-pinned self-update with fixed lint/unit gates and local no-dependency installation;
- recoverable activation markers that preserve pending restart intent when fixed-component re-exec fails;
- staged target/baseline wheels plus durable install transactions, verified rollback for caught package failures and fail-closed pending recovery after unproven interruption;
- local-only `self-update-recovery` requiring the emergency stop; it is intentionally unavailable through MCP/mailbox control;
- bounded `runtime_status` and `runtime_doctor` visibility without exposing commits, package versions or private artifact/environment details.
## Why the boundaries matter

Runner MCP intentionally separates source collaboration, operational requests, execution and human approval.

The GitHub mailbox accepts only its documented fixed action enum. It does not accept shell commands, executable paths, filesystem paths, environment values, service names or arbitrary MCP tool names from the request.

Ambiguous recovery states do not authorize rerunning work. A claimed request with no durable result remains fail-closed. Local recovery can publish only bounded terminal failures after exact request/replay checks; it never invokes the original action. A malformed historical request can be quarantined only when every sibling request in the current backlog already has a matching durable result and the request head remains unchanged through final verification.

Notification delivery is similarly separate from execution. Retrying a notification cannot rerun the task.

## Upgrade notes

This is the first tagged alpha, so there is no earlier public release to migrate from.

Operators testing development snapshots should nevertheless review the following before upgrading:

- use the current protocol-v1 mailbox request shape;
- keep existing watcher replay/cursor state; do not delete or reset it during upgrades;
- use the explicit resolve/abandon/quarantine operator paths for exceptional mailbox recovery rather than replaying or clearing state;
- replace any legacy private pilot watcher with the shared Runner MCP watcher runtime;
- use explicit watcher/bootstrap commands rather than silently skipping historical mailbox state;
- if using autostart, remove or migrate unmanaged Runner MCP cron entries before enabling the managed cron backend;
- keep all private repository/ref/token, project paths and executable definitions in private host configuration;
- treat any Python/build/runtime dependency-contract change as a local bootstrap/manual upgrade event: the current self-update path uses `--no-deps --no-index --no-build-isolation` and is only eligible for contract-preserving Runner MCP code updates. See `docs/SELF_UPDATE_COMPATIBILITY.md`.
## Known limitations

- Runner MCP is not a sandbox for hostile or untrusted project code;
- production mutations remain disabled;
- database restore and PostgreSQL PITR/WAL orchestration are not implemented;
- automated backup/release retention pruning is not implemented;
- guided private-tunnel/TLS onboarding is not yet one-click;
- managed-cron removal stops future supervision but deliberately does not blindly terminate an already-running component;
- the optional completion notifier needs a private GitHub destination and credential;
- public launch/registry/community publication remains a separate human-controlled step;
- the newest recovery-capable private-host self-update baseline and full live recovery matrix have not yet been freshly re-proven for this release candidate. Until that proof is completed, do not interpret the code/CI recovery coverage as a claim that same-commit/no-op, forward update, activation retry and interrupted package-install recovery have all been demonstrated on the current private deployment.
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

The current pre-tag release-candidate baseline has green compile, Ruff, pytest, whitespace, clean-demo and built-artifact jobs. Reconfirm every check on the exact final tag commit; record exact test counts only in dated release evidence.

Record the exact passing test count and commit SHA in the GitHub release notes when the tag is created.

## Security reporting

Use the repository security policy for vulnerability reports. Do not put real hostnames, addresses, usernames, paths, tokens, credentials, database endpoints, service identifiers or customer data in public issues.
