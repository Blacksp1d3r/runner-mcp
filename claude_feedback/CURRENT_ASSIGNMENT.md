# Claude continuous assignment queue

Last reconciled: 2026-09-22.

This file is Claude's persistent work queue for Runner MCP. It is intentionally designed so the user can simply say:

> Read `claude_feedback/CURRENT_ASSIGNMENT.md` and continue with the next unfinished task. When one task is complete, update the same file with the result and continue automatically with the next unfinished task unless a real blocker or coordination conflict requires stopping.

## Mandatory operating rule

Before starting or resuming work:
1. read `AGENTS.md`;
2. read `roadmap/ROADMAP.md`;
3. read `roadmap/DEPENDENCIES.md`;
4. read `handover/CURRENT_STATE.md`;
5. read `handover/SESSION_HANDOFF.md`;
6. read `handover/AGENT_EXCHANGE.md`;
7. read `decisions/DECISIONS.md`;
8. reconcile current GitHub PRs/issues/CI;
9. return here and take the first unfinished task whose prerequisites are satisfied.

GitHub current state wins if this file is stale.

## Continuous execution protocol

For every task below:
- create a fresh focused branch from the latest appropriate `main`;
- keep unrelated changes out;
- run the relevant focused tests and the full required validation;
- open a focused PR;
- follow CI to a terminal state when possible;
- do not merge your own PR unless the user or integrator explicitly instructs you to merge;
- write the outcome back into this file under that task: PR number, head commit, test/CI evidence, remaining blocker if any;
- add/update a concise project-wide handoff in `handover/AGENT_EXCHANGE.md` only when the result materially affects another agent;
- then continue automatically with the next unfinished task in this file.

Do not wait for the user between independent tasks. Stop only when:
- the next task would conflict with an open ChatGPT/self-update branch or PR;
- a real security defect requires integrator review beyond the smallest fail-closed fix;
- a required external/manual action is needed;
- GitHub/CI state is ambiguous enough that proceeding could duplicate or overwrite work.

## Coordination boundary with ChatGPT

ChatGPT currently owns:
- PR #45 and self-update recovery-state visibility;
- private watcher recovery/reconciliation;
- live private-host self-update bootstrap/proof;
- `self_update.py`, restart/activation behavior and self-update mailbox contract unless explicitly reassigned.

Claude must not modify those areas while that work is open.

---

## Task 1 — direct Settings/adapter regression coverage — COMPLETE

Completed in PR #42, merged as `3653e22f9618f0e00374ee3d008c5c435c94acdc`.

Evidence:
- 26 additional direct regression tests;
- no production-code changes;
- CI fully green.

No further action.

---

## Task 2 — installer/operator robustness — CURRENT

Goal: improve local operator installation failure handling without changing authority.

Scope:
- detect missing `sudo` before `install-operator.sh` attempts cross-account delegation;
- add deterministic regression coverage for the missing-sudo path without depending on the CI host actually lacking sudo;
- review reinstall/overwrite messaging and improve only verified confusing cases;
- preserve service-account validation, wrapper ownership recognition, symlink refusal and private-config separation;
- review whether existing failure output accidentally prints private paths or host-specific details and add regression coverage if needed.

Do not:
- add automatic sudo installation/configuration;
- add privilege escalation helpers;
- add uninstall/destructive cleanup;
- touch self-update/restart/activation code.

Acceptance:
- focused installer tests green;
- Ruff/full pytest green;
- normal PR CI green;
- no authority expansion.

After opening the PR and recording evidence here, continue to Task 3 without waiting for merge.

---

## Task 3 — secure I/O inventory and regression plan — NEXT

This is a design/inventory task, not a mass refactor.

Goal: inventory every atomic/private file-write path and determine which semantics are truly shareable.

Deliverable:
- create/update a dedicated document under `docs/` or `claude_feedback/`;
- enumerate each private/atomic writer and its caller;
- classify:
  - create-only vs overwrite;
  - expected file/dir mode;
  - symlink/no-follow behavior;
  - parent-directory requirements;
  - temp/staging strategy;
  - atomic replace expectations;
  - fsync/durability expectations;
  - locking/concurrency assumptions;
  - crash/recovery semantics;
  - cleanup semantics;
- identify semantic classes that can safely share primitives;
- identify call sites that should remain specialized;
- propose regression tests required before any migration.

Do not refactor all writers in this task.

Acceptance:
- inventory is traceable to current code;
- no secrets/private deployment values;
- proposed helpers preserve or strengthen fail-closed behavior.

After the PR/evidence is recorded here, continue to Task 4.

---

## Task 4 — safe watcher diagnostics contract — NEXT

Goal: design a minimal category-only diagnostic/logging contract for long-running watcher/notifier/supervisor components.

Requirements:
- define allow-listed event categories for lifecycle, cycle outcome, bounded retry class and supervisor restart;
- explicitly define forbidden output:
  - request/result payloads;
  - paths;
  - URLs;
  - credentials/tokens;
  - environment values;
  - host/service-unit names;
  - arbitrary exception text;
  - stack traces in normal operator logs;
- where failures need identity, use stable bounded error categories rather than `str(exc)`;
- define tests proving sensitive literals are not logged;
- identify which current components would consume the contract.

Preferred output:
- design + tests-first PR;
- production logging calls only if they are tiny, mechanically safe and fully covered;
- otherwise leave implementation for a later separately reviewed slice.

Do not touch self-update watcher recovery semantics.

After recording PR/evidence here, continue to Task 5.

---

## Task 5 — CLI confirmation helper deduplication — NEXT

Goal: remove repeated confirmation-input code without changing any destructive/privileged approval behavior.

Scope:
- inventory exact current confirmation phrases and exception/return behavior;
- introduce one narrow internal helper only if behavior can remain equivalent;
- migrate only clearly identical confirmation patterns;
- preserve exact phrases such as existing unlock/recovery confirmations;
- add regression tests for accepted, rejected and whitespace/input edge cases.

Do not:
- merge different approval concepts into one generic authorization system;
- change high-risk action policy;
- modify self-update recovery behavior owned by ChatGPT; if that call site would need editing, leave it unchanged and document why.

Acceptance:
- user-visible behavior unchanged for migrated commands;
- focused + full tests green.

Then continue to Task 6.

---

## Task 6 — documentation / CLI contract drift audit — NEXT

Goal: make public operator documentation match current code without duplicating state.

Audit:
- README;
- QUICKSTART;
- install/operator docs;
- CLI command/options shown to users;
- MCP/tool capability claims;
- public bridge documentation.

Rules:
- verify every changed claim against current code/tests;
- fix only demonstrated drift;
- prefer canonical links over duplicate long instructions;
- do not add evergreen exact test counts;
- do not expose private host/deployment details;
- do not document PR #45 behavior as merged until GitHub shows it on main.

Acceptance:
- documentation-only unless a real CLI defect is discovered;
- if a real code defect appears, stop that expansion, open a minimal separate regression/fix PR and record it here.

Then continue to Task 7.

---

## Task 7 — dependency-set compatibility review for self-update `--no-deps` — NEXT

This is analysis/design only. Do not edit self-update implementation.

Goal: make explicit which future dependency changes cannot safely ride through the current `pip --no-deps` self-update path.

Deliverable:
- inventory runtime dependencies vs dev/test dependencies from current packaging metadata;
- classify changes:
  - pure Runner-MCP code update;
  - compatible dependency already present;
  - new runtime dependency;
  - minimum-version increase;
  - dependency removal;
  - interpreter requirement change;
- define which classes require manual/bootstrap action;
- propose a fail-closed package/runtime compatibility marker or preflight contract if worthwhile;
- identify where compatibility state should be surfaced without exposing private environment details.

Do not:
- upgrade dependencies merely for freshness;
- allow mailbox clients to pass pip/package-manager arguments;
- change self-update implementation in this task.

Record the design PR/evidence here, then continue to Task 8.

---

## Task 8 — local release-check convenience — NEXT

Goal: provide one developer/operator command or script that runs the existing local release validation sequence consistently.

Candidate checks:
- compile;
- Ruff;
- pytest;
- whitespace;
- package build/artifact smoke;
- clean demo where practical.

Rules:
- convenience wrapper only;
- GitHub CI/release checklist remain authoritative;
- no secrets, network credentials or paid services;
- no automatic tagging, publishing or release creation;
- fail immediately and clearly on a failed component.

Acceptance:
- tests for orchestration/exit behavior where appropriate;
- documentation states CI remains authoritative.

Then continue to Task 9.

---

## Task 9 — release-candidate hygiene dry run — NEXT

Goal: inspect whether the current repository is release-candidate clean without actually releasing anything.

Check:
- package metadata;
- README/Quickstart/release checklist consistency;
- public-repository privacy hygiene;
- built artifact smoke;
- changelog/unreleased state;
- open PRs that materially block a candidate;
- dependency/bootstrap caveats;
- private-host/live-proof requirements from the roadmap.

Output:
- concise report in `claude_feedback/` or `docs/`;
- classify findings as blocking / required-before-tag / optional-follow-up;
- do not rank by subjective severity beyond those operational categories;
- do not create tags/releases or publish artifacts externally.

When complete, update this file and `handover/AGENT_EXCHANGE.md` with the remaining release blockers.

---

## Queue completion rule

When Tasks 2–9 are all complete:
- re-read current GitHub state;
- update this file so every task has PR/evidence/status;
- write one final `handover/AGENT_EXCHANGE.md` entry summarizing what Claude completed and what remains with ChatGPT/user;
- do not invent additional implementation work just to stay busy;
- if useful new work is discovered, add it under a clearly marked `Proposed future tasks` section for integrator review rather than starting it automatically.
