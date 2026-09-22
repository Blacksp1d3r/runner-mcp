# Feedback for Claude

This directory is the handoff point for Claude reviews and parallel work on Runner MCP.

Read this directory together with the current `main` branch, `AGENTS.md`, `roadmap/ROADMAP.md` and `handover/CURRENT_STATE.md`. Do not treat the older `claude/roadmap-review-suggestions-xxbhfo` branch as current state: that review was based on commit `319259c7...`, before later self-update and activation-recovery work.

## Review outcome

Claude's previous read-only review was useful. The low-risk findings that were independently revalidated have already been merged through PR #41:

- CI smoke/artifact jobs now depend on core validation;
- README exposes CI status and clarifies when the operator wrapper is unnecessary;
- roadmap status drift was cleaned up and status ownership was made explicit;
- `audit.py` has direct unit coverage, including its 0600 permission contract;
- `install.sh` reports venv creation failure more clearly and performs a post-install self-check.

The merged review cleanup is `0e66368ca1377359019de1d594833377892db7aa`; the handover follow-up is `74e8e0691b50653586cc1d2bba97a262cf7b2747`.

## Suggestions that remain useful, but need separate hardening work

These are not rejected. They were deliberately not merged as mechanical "quick wins":

- centralizing private/atomic file writes in a shared `secure_io` layer;
- scrubbed watcher lifecycle diagnostics/logging;
- reducing repetitive CLI confirmation logic;
- improving direct unit coverage of settings validation and adapters;
- making release/check tooling easier to run locally.

For the first two, preserve the current fail-closed behavior and do not broaden what is logged or exposed. Existing write paths have different lifecycle/failure semantics and must be inventoried before consolidation.

## Suggestions not to pursue now

Do not spend time on these unless the roadmap explicitly changes:

- dynamic third-party adapter/plugin discovery;
- a `doctor --verbose` mode that exposes private paths;
- a generic audited-tool decorator without a dedicated audit-contract design;
- broad `server.py` or `cli.py` module splitting only for aesthetics;
- a second full roadmap status table that duplicates per-phase status;
- production mutations, arbitrary shell, database restore or generic process/package control.

## Coordination rule

ChatGPT is currently taking the self-update installation/recovery path forward. Claude should prefer work that does not touch the self-update implementation unless a task below explicitly says otherwise. Use a fresh branch from current `main`, keep changes bounded, run the full relevant test set, and open a PR instead of committing unrelated work directly to `main`.

When a task changes implemented behavior, update `handover/CURRENT_STATE.md`. Update the roadmap only when the architectural status actually changes.
