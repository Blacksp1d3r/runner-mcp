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

## Rate-limit / takeover protocol

Claude availability is opportunistic, not a project dependency.

Every unfinished task may use these status values:
- `UNCLAIMED`
- `CLAUDE_IN_PROGRESS`
- `CHATGPT_IN_PROGRESS`
- `PR_OPEN`
- `PAUSED_LIMIT`
- `BLOCKED`
- `COMPLETE`

When starting a task, record the status plus `Claimed by`, `Branch` and `PR` when known.

If Claude hits a usage/rate limit or is otherwise unavailable:
- do not treat that as a project blocker;
- ChatGPT may take over an assigned task when it becomes the next dependency/blocker;
- before takeover, reconcile GitHub branches/PRs and inspect any Claude work already pushed;
- if no conflicting active work exists, set `CHATGPT_IN_PROGRESS` and continue;
- if a useful Claude branch exists and the user has confirmed Claude is unavailable, ChatGPT may continue/review that branch rather than duplicate it;
- if Claude later resumes, he must re-read this file and skip any task currently claimed by ChatGPT or already completed.

Likewise, Claude may pick up a previously unclaimed task after ChatGPT moves elsewhere, but may never duplicate an active ChatGPT branch/PR.

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

## Task 2 — installer/operator robustness — COMPLETE

Status: `COMPLETE`. Claimed by: Claude. PR: #46 (`claude/installer-operator-robustness`, head `9922bf4786992f82ce0c7469ddf039fa9cbef393`).

Evidence:
- `install-operator.sh` now detects a missing `sudo` right after confirming the service account exists via `getent`, before any filesystem mutation, instead of failing later with a raw `sudo: command not found`;
- reviewed reinstall/overwrite messaging and existing failure-output paths for private-path leakage per the task checklist; found no confusing case and no leakage beyond the operator's own local `$HOME` path on their own terminal, so no unrequested change was made;
- added a deterministic regression test for the missing-sudo path that does not depend on the CI host actually lacking `sudo` (shrinks `PATH` to a minimal binary set so `command -v sudo` genuinely cannot resolve it, regardless of the host);
- Ruff green; full pytest suite 753 passed, 1 deselected (see below);
- PR #46 CI fully green: Ruff and pytest / Clean five-minute demo / Built release artifact all `success`; `mergeable_state: clean`;
- `self_update.py`/restart/activation untouched.

One pre-existing, unrelated sandbox-only test failure was found and documented rather than silently worked around: `tests/security/test_self_update_install.py::test_real_project_wheel_can_stage_without_index` fails identically on unmodified `main` in this execution sandbox (confirmed via `git stash`) but is green in the real GitHub CI for the same commit — a sandbox build/network-isolation limitation in `self_update_install.py`, which this task does not own or touch.

Not merged — awaiting integrator/user merge decision per the "do not merge your own PR" rule.

---

## Task 3 — secure I/O inventory and regression plan — COMPLETE

Status: `COMPLETE`. Claimed by: Claude. PR: #47 (`claude/secure-io-inventory`, head `d14b6265`).

Evidence:
- `docs/SECURE_IO_INVENTORY.md` added: 30 writer functions across 14 non-self-update modules, each with create-only/overwrite, mode, temp/atomic-replace strategy, symlink safety, locking, fsync, and crash/cleanup semantics, traced to `file:line`;
- six semantic classes identified (ledger stores; mkstemp-based atomic writers — proposed as the shared target primitive; fixed-name-temp writers; high-churn job-metadata writers, gated on an explicit maintainer durability decision; one-shot directory/lock creators; create-only writers, which must stay distinguishable from overwrite to avoid a correctness regression);
- four write paths explicitly identified as not migration candidates, with reasons (`deployment_manager._activate_release`'s symlink+directory-fsync pattern as the reference, not a target for generalization; `_create_release`'s tar extraction; `audit.py`'s append-only log, separately flagged as the weakest-postured writer found and worth its own security review; everything in `self_update.py`/`self_update_install.py`);
- 7 categories of regression test proposed for any future migration (mode enforcement, symlink refusal, create-only/overwrite, concurrent-writer safety, crash simulation, fsync-invocation, orphan-temp characterization);
- no production code changed; Ruff green; full pytest suite 753 passed, 1 deselected (same pre-existing sandbox-only failure as Task 2, unrelated — this PR touches only a markdown file).

Handoff: two durability gaps found in `self_update.py`/`self_update_install.py` (both inventoried but out of scope to fix here) were surfaced to the self-update workstream via a new `handover/AGENT_EXCHANGE.md` entry rather than fixed in this PR.

Not merged — awaiting integrator/user merge decision.

---

## Task 4 — safe watcher diagnostics contract — COMPLETE

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

Status: `COMPLETE`. PR: #49, merged as `57d9f114dcab22df434aaa051796ae036b71ebb9`.

Evidence:
- category-only `safe_diagnostics` contract added with enum-only component/event/error fields;
- lifecycle, cycle outcome, bounded retry and supervisor-restart categories are allow-listed;
- dynamic strings are rejected without echoing rejected values;
- forbidden output and current consumers are documented in `docs/SAFE_DIAGNOSTICS.md`;
- security tests prove sensitive literals cannot flow through the renderer;
- production watcher logging integration deliberately remains a separate reviewed slice;
- CI green: Ruff/pytest, built release artifact and clean five-minute demo.

---

## Task 5 — CLI confirmation helper deduplication — COMPLETE

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

Status: `COMPLETE`. PR: #50, merged as `07d9a4b1041cd20e7b2201aa4a83b674a1a1c85c`.

Evidence:
- one narrow `_require_removal_confirmation` helper handles only ordinary REMOVE-style configuration removals;
- nine exact existing removal phrases migrated without changing prompt text, stripping behavior, exception class/message, or successful return behavior;
- setup YES, emergency-stop UNLOCK, one-action APPROVE, watcher ABANDON/QUARANTINE/RESOLVE, and RECOVER SELF UPDATE remain separate and unchanged;
- focused tests cover exact acceptance, surrounding-whitespace behavior, rejection cases and exact cancellation-exception identity;
- CI green: Ruff/pytest, built release artifact and clean five-minute demo.

---

## Claude capacity policy — 2026-09-22

To conserve Claude Code quota, analysis/design-heavy tasks should be done in normal Claude chat and returned as findings only. Claude Code must not claim tasks explicitly marked `CHAT REVIEW`. ChatGPT remains the default implementer unless the user explicitly assigns a CODE task to Claude Code. A rate-limited Claude session is never a project blocker.



## Task 6 — documentation / CLI contract drift audit — COMPLETE

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

Status: `COMPLETE`. PR #53 merged as `0c46bbefb8fcad6ae5c7f87450e638c40492a41a`.

Evidence:
- corrected the demonstrated `runtime_doctor` omission in README and the canonical public bridge action list;
- verified all 34 protocol-v1 bridge actions are named in the bridge documentation;
- audited public operator examples with no unknown top-level `runner-mcp` command;
- removed the stale evergreen pre-tag pytest count from the release-notes draft;
- exact PR-head CI green across validation, built artifact and clean demo.

Then continue to Task 7.

---

## Task 7 — dependency-set compatibility review for self-update `--no-deps` — COMPLETE

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

Status: `COMPLETE`. PR #54 merged as `69e604935bfe0fef0dd61b48dfdde76fed8f46ba`.

Evidence:
- `docs/SELF_UPDATE_COMPATIBILITY.md` inventories Python, build, runtime and dev/test dependency contracts;
- pure code, changed constraints, new dependencies, minimum-version increases, removals, interpreter/build changes and test-tool changes are classified;
- dependency/build/interpreter contract changes remain local bootstrap/manual events under the current `--no-deps --no-index --no-build-isolation` design;
- a conservative exact-contract compatibility marker/preflight is proposed without implementing it;
- safe observability is limited to bounded readiness/error categories, not installed versions or private environment details;
- release checklist links dependency changes to the bootstrap contract;
- exact PR-head CI green across validation, built artifact and clean demo.

Record the design PR/evidence here, then continue to Task 8.

---

## Task 8 — local release-check convenience — COMPLETE

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

Status: `COMPLETE`. PR: #52, merged as `d6821ddb0773b586b6a106b66b2e18154c90cc7a`.

Evidence:
- `bash scripts/release-check.sh` runs compile, Ruff, pytest, committed/staged/unstaged whitespace checks, built-artifact smoke and clean-demo smoke in fail-fast order;
- orchestration tests prove exact order and immediate stop on first failure;
- documentation explicitly keeps GitHub CI on the exact commit authoritative;
- clean demo now uses an isolated temporary project virtualenv and no longer creates/deletes the developer repository's `.venv`;
- final current-head CI green: Ruff/pytest, whitespace, built release artifact and clean five-minute demo.

---

## Task 9 — release-candidate hygiene dry run — COMPLETE

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

Status: `COMPLETE`. PR #55 merged as `358f8f6345a7ff6f094eb6c8e4d7db4b9943aed7`.

Evidence:
- `claude_feedback/RELEASE_CANDIDATE_DRY_RUN.md` records the package/docs/privacy/artifact/changelog/dependency/live-proof review;
- no current public-repository code/package blocker was found;
- required-before-tag work is explicit: changelog/release-note finalization, exact-candidate CI and privacy review, dependency-bootstrap discipline, and truthful handling of the remaining private-host self-update proof;
- optional follow-up work is separated from the release gate;
- no tag, release or external artifact was created;
- exact PR-head CI green across validation, built artifact and clean demo.

When complete, update this file and `handover/AGENT_EXCHANGE.md` with the remaining release blockers.

---

## Parallel work queue — authorized 2026-09-23

The user authorized continuation and parallel queue expansion. This section supersedes the old proposed-future-task holding area.

### Scheduling rules

- Keep at least several prerequisite-safe tasks ready when useful; do not let one external/private-host blocker drain the whole queue.
- Claim before editing. Never duplicate an active branch/PR from another agent.
- ChatGPT owns the release/private-host/self-update critical lane unless explicitly reassigned.
- Claude Code should be used for bounded high-value implementation; Claude Chat should be preferred for analysis/review to conserve Code quota.
- A Claude usage/rate limit is never a project blocker: ChatGPT may take over after GitHub reconciliation.
- Tasks in different lanes may run in parallel only when their file/semantic ownership does not conflict.
- Every task still follows branch -> tests -> PR -> CI -> evidence -> handoff. Do not tag or publish a release without explicit user authorization.

### Task 10 — private-host v0.1.0 live self-update/recovery proof — CHATGPT lane

Status: `BLOCKED` pending a usable private-host execution path or bounded operator-assisted commands.

Goal:
- prove the newest recovery-capable baseline on the private host;
- prove same-commit/no-op;
- prove one forward update;
- prove activation retry;
- deliberately interrupt package installation once and prove persisted transaction recovery.

Safety:
- never generically reset replay/cursor/transaction state;
- do not expose secrets/private paths in public evidence;
- keep the release-note limitation until this is freshly proven.

This blocker does not prevent Tasks 11–16.

---

### Task 11 — self-update compatibility preflight — CODE lane

Status: `UNCLAIMED`.

Preferred executor: Claude Code when capacity is available; ChatGPT may take over.

Goal:
Implement the conservative fail-closed compatibility marker/preflight designed in `docs/SELF_UPDATE_COMPATIBILITY.md`.

Acceptance:
- exact current runtime/dependency/build/interpreter contract can be compared without resolving/installing dependencies;
- pure code updates with unchanged contract remain eligible;
- dependency/build/interpreter contract changes fail closed into a bounded bootstrap-required category;
- remote/mailbox callers gain no pip/index/path/package-manager arguments;
- no installed versions, environment paths or private host details leak;
- focused security/regression tests plus full required validation.

Do not perform dependency upgrades in this task.

---

### Task 12 — safe diagnostics production integration — CODE lane

Status: `UNCLAIMED`.

Preferred executor: ChatGPT or Claude Code, but not concurrently with another agent touching the same watcher/supervisor files.

Goal:
Integrate the existing category-only `safe_diagnostics` contract into a smallest useful production watcher/notifier/supervisor slice.

Acceptance:
- only allow-listed categories reach normal operator logs;
- no payloads, paths, URLs, credentials, environment values, host/service names, arbitrary exception text or stack traces;
- tests inject sensitive literals and prove they cannot escape;
- no change to watcher replay/recovery semantics.

Keep this separate from Task 10.

---

### Task 13 — secure I/O follow-up: append-only audit durability review — CHAT REVIEW

Status: `UNCLAIMED`.

Preferred executor: Claude Chat; no code changes.

Goal:
Review the append-only audit writer identified by `docs/SECURE_IO_INVENTORY.md` as the weakest-postured non-self-update writer.

Deliverable:
- threat/failure model;
- durability and symlink/concurrency assessment;
- concrete tests that would prove a fix;
- smallest recommended implementation boundary;
- explicit note if no change is warranted.

Do not modify code. Record findings for an integrator to turn into a later CODE task.

---

### Task 14 — secure I/O migration candidate selection — CHAT REVIEW

Status: `UNCLAIMED`.

Preferred executor: Claude Chat; no code changes.

Goal:
Using `docs/SECURE_IO_INVENTORY.md`, choose the next coherent non-self-update writer family suitable for a shared safe-write primitive.

Deliverable:
- exact candidate functions/files;
- semantic differences that must be preserved (create-only vs overwrite, locking, modes);
- migration hazards;
- regression-test matrix;
- suggested bounded CODE slice.

Exclude `self_update.py`, `self_update_install.py`, release symlink activation and tar extraction.

---

### Task 15 — release/package consumer-path audit — CHAT REVIEW

Status: `UNCLAIMED`.

Preferred executor: Claude Chat.

Goal:
Independently review the v0.1.0 package from a fresh consumer/operator perspective without publishing it.

Check:
- package metadata and Python requirement;
- install/entry-point assumptions;
- README -> Quickstart -> five-minute demo path;
- offline/no-index artifact smoke assumptions;
- bootstrap boundary for dependency changes;
- public privacy/security wording.

Return only demonstrated defects or ambiguities. Do not create a tag/release.

---

### Task 16 — adversarial bridge/protocol regression review — CHAT REVIEW

Status: `UNCLAIMED`.

Preferred executor: Claude Chat.

Goal:
Review protocol-v1 action validation and bridge allow-listing for parser differentials and accidental capability expansion.

Focus:
- unknown fields/actions;
- case/abbreviation ambiguity;
- duplicate/extra identifiers;
- request-id/action mismatch;
- dangerous argument smuggling;
- bounded error output.

Deliverable:
a concise adversarial test matrix and any demonstrated gaps. No implementation in this task.

---

## Queue refill rule

When fewer than three prerequisite-safe `UNCLAIMED` tasks remain, the integrator should review the roadmap, current findings and open PRs and add new bounded tasks before the queue drains completely. New work must be dependency-safe and must not be invented merely to keep agents busy.

When a CHAT REVIEW demonstrates a real defect, add a separate CODE task with explicit files, acceptance criteria and ownership rather than silently expanding the review.

