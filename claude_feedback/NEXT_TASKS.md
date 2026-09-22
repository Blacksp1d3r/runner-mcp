# Parallel task queue for Claude

The tasks below are ordered to maximize useful parallel progress while minimizing conflicts with the current self-update hardening work.

## Task 1 — direct configuration and adapter regression coverage — completed

Completed in PR #42, merged as `3653e22f9618f0e00374ee3d008c5c435c94acdc`. Claude added 26 direct regression tests without production-code changes; CI was fully green.

Goal: strengthen direct tests around existing public contracts without changing runtime behavior.

Scope:
- add focused unit tests for `Settings.from_mapping()` validation branches that are currently covered only indirectly;
- expand adapter registry/capability tests for unknown adapter IDs, known adapter enumeration and relevant fail-closed edge cases;
- do not loosen error handling or expose private values in assertions/output;
- avoid touching self-update code;
- keep implementation changes to production code at zero unless a test exposes a real defect.

Acceptance:
- Ruff green;
- full pytest green;
- no weakened security assertions;
- concise PR explaining exactly which previously indirect contracts now have direct coverage.

## Task 2 — installer/operator robustness — current

Goal: improve operator-facing failure messages without changing authority.

Candidate checks:
- detect missing `sudo` before `install-operator.sh` attempts cross-account delegation;
- add regression tests for that failure path;
- review whether reinstall messaging can be clearer without adding implicit destructive behavior;
- keep all service-account and wrapper ownership/symlink protections intact.

Do not add automatic sudo configuration, privilege escalation, uninstall, or destructive cleanup.

## Task 3 — secure I/O inventory and migration plan

Design/review task first, not a mass refactor.

Goal: map every atomic/private write implementation and classify its semantics.

Deliverable:
- a document under this directory or `docs/` listing each write path;
- classify create-only vs overwrite, symlink behavior, mode enforcement, lock/fsync expectations and crash semantics;
- identify the smallest safe common primitives;
- propose regression tests before any consolidation.

Do not replace all call sites in the same PR. A later implementation slice can migrate one semantic class at a time.

## Task 4 — safe watcher diagnostics contract

Design a minimal operational logging contract for long-running watcher/notifier processes.

Requirements:
- category/lifecycle-only events such as start, stop, cycle result, retry class and supervisor restart;
- no request payloads, paths, URLs, credentials, environment values, service names, raw exceptions or stack traces;
- if exception information is needed, prefer a bounded allow-listed error category over `str(exc)`;
- document what must never be logged;
- include test strategy for scrubbing/privacy.

Prefer a design + tests-first PR before adding broad logging calls.

## Task 5 — CLI confirmation deduplication

A bounded refactor is acceptable after Tasks 1-2.

Goal: replace repeated destructive confirmation input with one helper while preserving exact confirmation phrases and exception types.

Requirements:
- behavior must remain byte-for-byte equivalent from the user's point of view;
- cover every migrated call site with existing or new tests;
- no changes to approval semantics or high-risk action authorization.

## Task 6 — local release-check convenience

Optional, lower priority.

Goal: provide one developer command/script that runs the already-existing local release checks (compile, Ruff, pytest, whitespace and artifact/demo checks where practical).

It must remain a convenience wrapper, not a replacement for GitHub CI or the release checklist, and must not introduce paid services or new secrets.

## Task 7 — documentation/CLI contract drift audit

Goal: detect stale user-facing commands and capability claims without rewriting the documentation wholesale.

Scope:
- compare README, QUICKSTART and the main operational docs against the current argparse/MCP surfaces;
- identify commands/options that are stale, missing or contradictory;
- fix only verified drift;
- prefer links to one canonical explanation instead of duplicating long command sequences;
- do not add another global status table or exact test counts to evergreen prose.

Acceptance:
- every changed claim is traceable to current code/tests;
- documentation-only unless a real CLI defect is found;
- no private deployment details.

## Task 8 — dependency-set compatibility review

Design/review task; do not upgrade dependencies just for freshness.

Goal: support the self-update `--no-deps` model by documenting what dependency-set changes would require explicit operator/bootstrap action.

Deliverable:
- inventory runtime vs dev dependencies from `pyproject.toml`;
- identify which kinds of future changes cannot be safely delivered by the current no-deps self-update;
- propose a fail-closed compatibility/version marker or preflight contract if useful;
- no automatic dependency installation and no package-manager arguments exposed to mailbox/MCP clients.

Coordinate with ChatGPT before touching self-update implementation.

## Task 9 — release-candidate hygiene dry run

Lower priority; do after the implementation-oriented tasks above.

Goal: walk the release checklist against the then-current main and report only concrete blockers/drift.

Check:
- README/Quickstart/release notes consistency;
- package metadata and built-artifact smoke;
- public-repository hygiene;
- exact tag candidate must remain human-selected after green CI.

Do not create a tag/release or publish externally without an explicit user instruction.

## Coordination / do-not-conflict note

The current highest-priority functional roadmap item is staged/rollback-capable Runner MCP self-update installation plus live bootstrap/proof. Unless explicitly reassigned, leave `self_update.py`, restart/activation handling and the self-update bridge contract to ChatGPT's current workstream.

If a task reveals a security defect rather than a maintainability issue, stop expanding the scope: document the defect precisely, add the narrowest failing regression test possible, and make the smallest fail-closed fix.
