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

Status: `COMPLETE`. PR #62 merged as `9dd453f275a0096ef1af358af8124d1bd60e9194`.

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

Status: `COMPLETE`. PR #60 merged as `67973b14dbcbbae5a7ee2d0a6b8ce37942a5724b`.

Evidence:
- integrated the enum-only safe diagnostics contract into `GitHubWatcherRuntime` as the first bounded production slice;
- lifecycle start, healthy/degraded/uninitialized cycle state and self-update restart failure use only allow-listed component/event/error categories;
- the injected diagnostic sink receives only rendered category strings; no exception text, IDs, paths, URLs, payloads, counts or private runtime context are accepted;
- watcher replay/recovery behavior was not changed;
- focused runtime tests cover bounded uninitialized and recovery-required output;
- exact PR-head CI run 35869924479 green: Ruff/pytest/whitespace, built release artifact and clean five-minute demo.

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

Status: `COMPLETE`. Review: `claude_feedback/TASK13_AUDIT_DURABILITY_REVIEW.md`. A dedicated CODE follow-up is required.

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

Status: `COMPLETE`. Review: `claude_feedback/TASK14_SECURE_IO_MIGRATION_REVIEW.md`. A bounded CODE follow-up is queued.

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

Status: `COMPLETE`. Review: `claude_feedback/TASK15_CONSUMER_PATH_AUDIT.md`. Documentation/evidence drift follow-up queued.

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

Status: `COMPLETE`. Review: `claude_feedback/TASK16_BRIDGE_ADVERSARIAL_REVIEW.md`. No runtime defect demonstrated; regression-test hardening queued.

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

### Task 17 — harden append-only audit writer — CODE lane

Status: `COMPLETE`. PR #73 merged as `22e6d309a94db783d11ff26b882dea305c33c0f7`; exact head CI run 35891213181 fully green after one import-order fix.

Preferred executor: ChatGPT or Claude Code after reconciling Task 13 findings.

Source review:
`claude_feedback/TASK13_AUDIT_DURABILITY_REVIEW.md`.

Goal:
Harden `AuditLogger.append` without changing event schema, server call sites, retention/rotation, or other secure-I/O families.

Acceptance:
- audit target is opened append-only with private mode and symlink refusal;
- opened target is verified as a regular file;
- cooperating processes serialize whole JSONL records with a file-level exclusive lock;
- short writes cannot silently truncate a record;
- successful append performs `fsync`; fsync failure propagates;
- adversarial tests prove symlink target contents/mode are untouched, concurrent records do not interleave, and existing JSONL order/schema remain unchanged;
- no automatic repair/truncation, rotation, retention or parent-directory policy expansion in this slice.

---

### Task 18 — extract private atomic-replace primitive + migrate completion state — CODE lane

Status: `COMPLETE`. PR #76 merged as `5c4f5db350cdafa99066bdb091866b7d6979a7a9`; exact PR head `97fcde693d6264171920c386d10e9e63403a9a9a`; exact-head CI run 35894315537 fully green (Ruff, whitespace, 794 pytest tests, built release artifact, clean demo).

Preferred executor: ChatGPT or Claude Code after reconciling Task 14 findings.

Source review:
`claude_feedback/TASK14_SECURE_IO_MIGRATION_REVIEW.md`.

Goal:
Extract the existing strong Class B private-file overwrite mechanics and migrate config/approval plus completion-delivery private JSON state without changing higher-level policy semantics.

Acceptance:
- one internal same-directory random-temp atomic replace primitive with 0600 mode, symlink refusal, file fsync before replace and bounded errors;
- config-manager and approval-manager preserve their existing higher-level locks, serialization and state ordering;
- completion-delivery preserves size/schema checks while replacing predictable non-fsynced temp writes with the shared primitive;
- security tests cover permissive umask, symlink referent preservation, fsync-before-replace, failure cleanup and bounded error output;
- do not touch autostart, high-churn job metadata, in-place ledgers, create-only writers, deployment activation/tar extraction or self-update.

---

### Task 19 — reconcile self-update/release consumer documentation — CODE/DOC lane

Status: `COMPLETE`. PR #70 merged as `4f2ac941fe87346747d5e615df1ba26dc8359237`; exact PR-head CI run 35886054525 green.

Preferred executor: ChatGPT.

Source review:
`claude_feedback/TASK15_CONSUMER_PATH_AUDIT.md`.

Goal:
Remove demonstrated v0.1.0 documentation/evidence drift without changing runtime behavior or publishing anything.

Acceptance:
- `docs/SELF_UPDATE_COMPATIBILITY.md` describes the exact compatibility preflight as implemented, not merely recommended future work;
- README mentions the unchanged compatibility-contract gate and local bootstrap/manual path for dependency/build/interpreter drift;
- release/artifact documentation does not call the current clean wheel install offline/no-index unless a real wheelhouse-based offline test is added;
- source-clone `./install.sh` remains the documented pre-publication consumer path;
- no dependency changes, tag, release or package publication.

---

### Task 20 — exhaustive bridge protocol adversarial regression matrix — CODE/TEST lane

Status: `COMPLETE`. PR #77 merged as `4bfd71d85cb5228ba328ee17fc60414c84c43e0a`; exact PR head `666a399803db41bae4deae73fc4f205de5e97854`; exact-head CI run 35895116909 fully green (Ruff, whitespace, 1203 pytest tests, built release artifact, clean demo).

Preferred executor: ChatGPT or Claude Code.

Source review:
`claude_feedback/TASK16_BRIDGE_ADVERSARIAL_REVIEW.md`.

Goal:
Pin the current fail-closed bridge protocol contract with exhaustive adversarial tests; do not broaden or redesign the protocol.

Acceptance:
- every BridgeAction has a known-valid minimal request fixture;
- every syntactically valid non-owned optional field is injected per action and rejected;
- action case/prefix/hyphen variants are rejected;
- duplicate request_id, uppercase self_update commit and request-side NaN/Infinity are rejected;
- rejected requests cannot reach executor invocation;
- no action enum, alias, normalization, identifier-regex, replay-state or capability changes.

---

### Task 21 — migrate managed autostart unit writes to shared private replace — CODE lane

Status: `COMPLETE`. PR #78 merged as `22e14fff99a4f02a30f2edf9abffd98a8b1792ea`; exact PR head `01ee0c0bfeaeae8f3a07a47f4162d4f9560304ab`; exact-head CI run 35903107229 fully green (Ruff, whitespace, 1207 pytest tests, built release artifact, clean demo).

Preferred executor: ChatGPT or Claude Code after Task 18.

Source:
`claude_feedback/TASK14_SECURE_IO_MIGRATION_REVIEW.md`.

Goal:
Migrate only `autostart._write_managed_unit` to the shared private atomic-replace primitive while preserving the existing Runner MCP managed-marker ownership refusal.

Acceptance:
- existing unmanaged unit content is never overwritten;
- managed-marker inspection/refusal semantics remain unchanged;
- private mode and atomic replacement use the shared primitive;
- symlink referents remain untouched;
- write/fsync/replace failures are bounded and preserve the previous unit;
- focused TOCTOU/adversarial regression coverage is added where the current ownership check permits meaningful proof;
- do not touch cron, job metadata, ledgers, create-only writers, deployment activation, tar extraction or self-update.

---

### Task 22 — integrate category-only diagnostics into cron supervisor — CODE lane

Status: `COMPLETE`. PR #79 merged as `1bfeb9e7e8991058fb82a31b6d93b94f77c5ba72`; exact PR head `65e15a9654e131073d8e90dc90cfa5e0536b9781`; exact-head CI run 35903803377 fully green (Ruff, whitespace, 1208 pytest tests, built release artifact, clean demo).

Preferred executor: Claude Code or ChatGPT; keep separate from Task 18 and Task 20.

Source:
`docs/SAFE_DIAGNOSTICS.md` and the existing `runner_mcp.safe_diagnostics` contract.

Goal:
Integrate the existing category-only diagnostics contract into the smallest useful `run_cron_component()` supervisor slice without exposing paths, argv, component-specific private values or exception text.

Acceptance:
- only allow-listed `cron_supervisor` component/event/error enums are rendered;
- lock-already-held, exec handoff and bounded start/restart failure states are observable without private context;
- no argv, executable/config path, service identity beyond the existing generic enum, environment value or raw exception text is emitted;
- tests inject sensitive literals and prove they cannot escape;
- no change to cron ownership, locking, command construction or execution authority.

---

### Task 23 — integrate category-only diagnostics into completion watcher — CODE lane

Status: `COMPLETE`. PR #80 merged as `873f905c64cdfbfc0ec6ac4b5091c04877b84d59`; exact PR head `595bb6466e7eca50b4b21a9dbc8695a59b248c11`; exact-head CI run 35914643900 fully green (Ruff, whitespace, 1211 pytest tests, built release artifact, clean demo).

Preferred executor: ChatGPT or Claude Code after Task 18.

Source:
`docs/SAFE_DIAGNOSTICS.md`.

Goal:
Integrate the existing safe diagnostics contract into `CompletionNotifierRuntime.run_forever()` only.

Acceptance:
- lifecycle and healthy/degraded cycle state use only allow-listed completion-watcher categories;
- restart failure is reported only through the bounded diagnostics contract;
- no repository, issue, mention, token, event/job ID, path, URL or exception text can reach the sink;
- delivery/replay/idempotency behavior is unchanged;
- focused sensitive-literal regression tests plus required validation.


---

### Task 24 — asynchronous completion-delivery expansion review — CHAT REVIEW

Status: `COMPLETE`. PR #81 merged as `d9f7d40f952ab39478d4a0286d317f160d6b46ce`; exact PR head `22d5e9a7c7e5ab854b81d84b7b9997202837caf4`; exact-head CI run 35915217076 fully green (Ruff, whitespace, 1211 pytest tests, built release artifact, clean demo). Review: deployment + rollback are safe candidates for one bounded completion-delivery CODE slice; migration remains blocked pending a durable persisted migration-job source.

Preferred executor: Claude Chat or ChatGPT review; no code changes.

Source:
Phase 3.8.1 `Next` in `roadmap/ROADMAP.md`.

Goal:
Determine whether existing persisted terminal metadata for migration, deployment and rollback jobs can be consumed by the completion-delivery runtime without widening execution authority or weakening idempotency.

Deliverable:
- inventory each candidate job class and its persisted terminal metadata;
- identify source/operation binding and stable deduplication inputs;
- identify privacy or replay hazards;
- classify each class as safe candidate, blocked, or requiring a separate prerequisite;
- propose the smallest bounded CODE slice only when evidence supports one.

Do not modify delivery/runtime code in this review and do not add new execution authority.

---

### Task 25 — private connectivity/TLS onboarding contract review — CHAT REVIEW

Status: `COMPLETE`. PR #82 merged as `f2c1d6a135133033ab1e0059f9a92cfec3021d88`; exact PR head `38b3143d53d49c58af896adfe96b943e34c2ee5a`; exact-head CI run 35948648167 fully green (Ruff, whitespace, 1211 pytest tests, built release artifact, clean demo). Review: runtime/network safety is already loopback-first; remaining gap is privacy-safe guided connectivity/documentation reconciliation without network mutation.

Preferred executor: Claude Chat or ChatGPT review; no code changes.

Source:
Phases 3.5 and 3.6 `Still planned` in `roadmap/ROADMAP.md`.

Goal:
Turn the remaining guided private-tunnel/TLS onboarding item into a concrete, infrastructure-neutral contract without exposing private deployment details or opening inbound access by default.

Deliverable:
- audit current README/Quickstart/connectivity guidance and CLI capabilities;
- define safe supported onboarding states and explicit non-goals;
- preserve loopback/private defaults and outbound-connectivity preference;
- identify any documentation drift or smallest future implementation slice;
- keep real hosts, ports, service names and credentials out of public examples.

Do not change network exposure, firewall state, certificates or deployment configuration in this review.


---

### Task 26 — bounded service journal/log access contract review — CHAT REVIEW

Status: `COMPLETE`. PR #83 merged as `b08a0b10afcce754440c37025230773da72c6c05`; exact PR head `faa5126548021c9294e3a395c6b71344505e545d`; exact-head CI run 35949004101 fully green (Ruff, whitespace, 1211 pytest tests, built release artifact, clean demo). Review conclusion: remote/MCP service-journal access remains deferred; explicit per-service log-read opt-in plus a reusable bounded text-redaction primitive are prerequisites.

Preferred executor: Claude Chat or ChatGPT review; no code changes.

Source:
Phase 4 in `roadmap/ROADMAP.md`: “Journal/log access remains a later bounded addition.”

Goal:
Define whether and how bounded staging service journal/log access can be added without exposing arbitrary unit names, paths, secrets, raw unbounded output or generic process-control authority.

Deliverable:
- inventory current service aliases/status/health boundaries and existing log-scrubbing primitives;
- define a bounded read-only request/response contract, or document why one should remain deferred;
- identify safe pagination/size/time limits and redaction requirements;
- preserve fixed service aliases and deny arbitrary journalctl arguments, units and filesystem paths;
- propose a separate CODE task only if the review demonstrates a safe minimal slice.

Do not modify service/runtime code and do not add remote process-control capability.


---

### Task 27 — database restore/recovery boundary review — CHAT REVIEW

Status: `CHATGPT_IN_PROGRESS`. Claimed by: ChatGPT. Branch: `chatgpt/task27-database-restore-review`. PR: pending.

Preferred executor: Claude Chat or ChatGPT review; no code changes.

Source:
Phase 5 and Phase 7 in `roadmap/ROADMAP.md`: database restore, WAL/PITR orchestration/verification and database restore/recovery workflow remain deferred.

Goal:
Define the safety and approval boundary for any future database restore/recovery capability without implementing restore or broadening mailbox authority.

Deliverable:
- distinguish one-backup restore, WAL/PITR and deployment rollback boundaries;
- identify required local/operator approvals, emergency-stop behavior and pre-restore evidence;
- define what metadata may be surfaced safely without paths, DSNs or database contents;
- preserve the rule that automatic production database restore is prohibited;
- identify prerequisites and the smallest future implementation slice, if any.

Do not execute a restore, change database state, add mailbox restore actions or expose credentials/paths.


---

### Task 28 — deployment/rollback completion delivery integration — CODE lane

Status: `UNCLAIMED`. Dependency satisfied: Task 24 is `COMPLETE` on main.

Preferred executor: ChatGPT or Claude Code.

Source:
`claude_feedback/TASK24_COMPLETION_DELIVERY_EXPANSION_REVIEW.md`.

Goal:
Extend completion delivery to persisted asynchronous deployment and rollback jobs only, using strict read-only scanning and the existing deterministic completion-event/ledger model.

Acceptance:
- scan deployment job metadata directly; do not instantiate `DeploymentJobRunner` from the notifier;
- require exact 32-lowercase-hex filename/job-id match, explicit `operation` (`deploy` or `rollback`), safe project identifier, known terminal state and timezone-aware `finished_at`;
- map deploy -> `DEPLOYMENT_JOB/DEPLOY_STAGING`, rollback -> `ROLLBACK_JOB/ROLLBACK_RELEASE`;
- map completed -> succeeded, stopped -> cancelled, error/interrupted -> failed; ignore queued/running;
- preserve the notifier bootstrap cutoff, deterministic event IDs, local delivery ledger and remote marker idempotency;
- never include job `result`, `error_category`, commit/release/path/URL data in completion events or notification bodies;
- adjust non-test notification rendering so it omits `Test profile: None` and renders only safe allow-listed operation/state information;
- reject symlinks, unsafe identifiers, missing/unknown operation, job-id mismatch, malformed/oversized metadata, duplicate keys, NaN/Infinity and invalid terminal timestamps;
- migration completion remains out of scope until a separate persisted migration-job substrate exists;
- no deployment/rollback execution authority, MCP/mailbox actions or replay semantics may change.

Required validation:
focused security/regression tests plus full Ruff/pytest/whitespace, built artifact and clean demo.


---

### Task 29 — privacy-safe guided connectivity reconciliation — CODE/DOC lane

Status: `UNCLAIMED`. Dependency satisfied: Task 25 is `COMPLETE` on main.

Preferred executor: ChatGPT or Claude Code.

Source:
`claude_feedback/TASK25_CONNECTIVITY_TLS_ONBOARDING_REVIEW.md`.

Goal:
Close the demonstrated onboarding drift with a non-mutating connectivity guide while preserving Runner MCP's loopback-first network boundary.

Acceptance:
- reconcile `security/CONNECTIVITY.md`, README and Quickstart so current private-tunnel availability and the meaning of setup `public` mode are consistent;
- explicitly state that public setup records HTTPS identity only and does not bind publicly, install TLS, edit DNS/firewalls or configure a reverse proxy/tunnel;
- extend the existing `runner-mcp guide` with a generic connectivity category/next-step section derived from configured resource URL shape only;
- guide output may report only bounded categories such as loopback or external HTTPS; it must not print configured hostname/resource URL/auth issuer/token/tunnel ID/private path;
- private-tunnel guidance remains outbound-only where supported and points to canonical vendor documentation rather than embedding credentials or vendor-specific provisioning state;
- reverse-proxy guidance keeps TLS outside Runner MCP and does not enable proxy-header trust or public bind;
- `serve`, autostart, firewall, TLS, DNS, dependencies and network exposure remain unchanged;
- tests inject sensitive public hostname/resource URL/auth/token/path literals and prove guide output cannot leak them.

Required validation:
focused guide/privacy tests plus full Ruff/pytest/whitespace, built artifact and clean demo.


---

### Task 30 — automated retention pruning boundary review — CHAT REVIEW

Status: `UNCLAIMED`.

Preferred executor: Claude Chat or ChatGPT review; no code changes.

Source:
Phase 5 and Phase 6 in `roadmap/ROADMAP.md`: automated backup retention pruning and release pruning remain deferred.

Goal:
Define a fail-closed retention-pruning contract that cannot delete protected backups/releases or widen remote deletion authority.

Deliverable:
- inventory current retention-policy invariants and safe metadata available for backups/releases;
- distinguish preview/eligibility calculation from actual deletion;
- define minimum count/age, migration-boundary and active-release protections;
- define what may be automated locally versus what requires explicit operator approval;
- identify symlink/path/TOCTOU and concurrent deployment/migration hazards;
- propose a separate implementation slice only if the review demonstrates a bounded safe path.

Do not delete backups/releases, change retention settings, add mailbox deletion actions or modify deployment/database state.


## Queue refill rule

When fewer than three prerequisite-safe `UNCLAIMED` tasks remain, the integrator should review the roadmap, current findings and open PRs and add new bounded tasks before the queue drains completely. New work must be dependency-safe and must not be invented merely to keep agents busy.

When a CHAT REVIEW demonstrates a real defect, add a separate CODE task with explicit files, acceptance criteria and ownership rather than silently expanding the review.
