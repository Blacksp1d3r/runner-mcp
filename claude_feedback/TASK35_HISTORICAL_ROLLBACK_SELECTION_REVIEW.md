# Task 35 — manual historical rollback selection boundary review

Date: 2026-09-24

Status: **COMPLETE — review only; arbitrary historical target selection remains deferred.**

## Scope

This task reviews whether Runner MCP should ever let an operator select an older historical release directly.

No rollback/runtime code, approval authority, deployment job behavior, release metadata, database recovery behavior or production policy is changed here.

## Executive conclusion

Runner MCP already has the safer primitive needed to move backward through release history: **one explicit direct-previous rollback at a time**.

A successful rollback makes the previous release current. A later rollback can then be planned from that new current release, but only after a fresh plan, a fresh short-lived human approval, another execution and another health check.

That is materially safer than accepting an arbitrary historical target because each step re-evaluates:

- the current release;
- the direct previous release from trusted metadata;
- the database-migration boundary;
- operator safety/emergency-stop state;
- the approval binding;
- deployment/rollback concurrency;
- service restart and health.

There is no demonstrated alpha need to bypass those checkpoints. Arbitrary historical target selection therefore remains deferred, and this review does not queue a code implementation for it.

## Current release-chain invariants

The implemented deployment/rollback model establishes these invariants:

1. Release activation is represented by the private `current` symlink.
2. The current pointer must resolve to exactly one release directory inside the configured release store.
3. Each release metadata record contains its own release ID and at most one `previous_release`.
4. `rollback_plan(project)` derives the target exclusively from the **current release's** trusted `previous_release` value.
5. The client cannot supply a target release to `rollback_plan` or `rollback_release`.
6. Unknown MCP arguments are rejected globally, so a hidden target cannot be smuggled through an ignored field.
7. A rollback action is constrained to one step by the safety guard.
8. The asynchronous job stores the expected current and expected direct target.
9. The deployment manager re-resolves the plan under its per-project mutation lock and rejects a changed current or target.
10. A project cannot have a deployment and rollback job active at the same time.
11. Interrupted queued/running jobs are marked interrupted after restart rather than resumed silently.
12. Production mutations remain unavailable.

These constraints mean the release chain is not merely presentation metadata; it is part of the mutation authority boundary.

## Visibility is not activation authority

`list_releases(project)` already exposes bounded release history:

- release ID;
- commit;
- creation time;
- direct previous release;
- current state;
- migration flag;
- pre-migration backup reference;
- retention state;
- direct rollback eligibility.

That is useful operator visibility. It does **not** imply that every listed release is a valid activation target.

A future UI/CLI may improve how older history is visualized, but it must not convert a release list row, release ID or commit into direct mutation authority.

In particular, a generic operation such as:

```text
rollback --target RELEASE_ID
```

would weaken the current design because it would collapse several independently revalidated one-step decisions into one request.

## Migration boundaries

The current direct rollback rule blocks rollback whenever the active release records `migrations_applied=true`.

That boundary must remain step-local and fail closed.

Example:

```text
R4 (current, no migration) -> R3 (no migration) -> R2 (migration) -> R1
```

A first approved rollback may move R4 -> R3 if all checks pass. A later separately approved rollback may move R3 -> R2 if all checks pass. Once R2 is current, a further code rollback is blocked because R2 crossed a database migration boundary.

An operator-selected request for R1 must never skip over R2 merely because R1 exists and is retained.

Crossing that boundary requires a separately designed database recovery decision. Code rollback must not infer, trigger or bundle a database restore.

## Missing, malformed or pruned release metadata

Historical traversal must follow a complete trusted direct-previous chain. It must never reconstruct a missing link from:

- directory ordering;
- timestamps;
- Git commit ancestry;
- release names;
- operator-supplied guesses.

If the current release points to a missing or invalid previous release, rollback fails closed.

For any future historical-path preview, a missing, malformed, unsafe or pruned metadata link must terminate the path with a bounded blocked state. It must not search for the “next best” older release.

This is also why future pruning policy must define chain-boundary semantics before release deletion becomes authoritative.

## Repeated one-step approvals are the correct historical model

Historical rollback should remain a sequence of independent one-step actions, not one approval for an arbitrary number of steps.

For every step:

1. inspect current state;
2. generate the direct rollback plan;
3. request a new approval;
4. approve locally;
5. consume that single-use approval;
6. enqueue exactly one rollback;
7. revalidate current/target under mutation locking;
8. activate the direct previous release;
9. restart and health-check;
10. stop and reassess before another step.

A user may ultimately reach an older release after several successful steps, but Runner MCP should not treat the final desired release as authorization to traverse all intermediate states automatically.

This preserves human agency and keeps health/database compatibility evidence between mutations.

## Approval binding and TOCTOU

The existing rollback approval path already has multiple useful race defenses:

- approval creation binds the current `rollback_plan`;
- the approval manager stores only a fingerprint of that binding privately;
- approval is short-lived and single-use;
- on consumption, Runner MCP recomputes the rollback material and rejects a changed binding;
- job creation carries the approved expected current and expected target;
- `DeploymentJobRunner.start_rollback()` recomputes the plan before enqueueing;
- `DeploymentManager.rollback_one()` acquires the per-project mutation lock, recomputes the plan again and rejects a changed current/target before activation.

A future historical-selection feature must not weaken this into “approve release X once, then derive a path later.” Any path that changes while approvals are pending must invalidate the pending decision.

If a read-only historical-path preview is ever introduced, it is advisory only. Execution must still recompute one direct step after acquiring the mutation boundary.

## Concurrency boundary

The current design has two complementary controls:

- persisted deployment/rollback jobs prevent two active deploy/rollback jobs for one project;
- the deployment manager's per-project lock serializes the actual mutation.

Future history visualization does not need either mutation lock.

Future historical execution must use the existing job/manager path rather than add a second activation route. A direct local helper that writes `current` or calls the service backend outside these locks would create a competing authority and is not acceptable.

## Health behavior must remain step-local

A rollback is accepted only after the target service is restarted and checked.

When a rollback target is unhealthy, Runner MCP may reactivate the original release when safe. That recovery is not permission to continue further backward.

A multi-step historical command would create ambiguous behavior if an intermediate release is unhealthy: skip it, revert, or continue. All three weaken the existing safety model.

Stopping after each step avoids that ambiguity.

## Production boundary

Historical visibility may remain read-only where a production project is represented, but Runner MCP must not gain production rollback authority.

No amount of historical retention or operator selection changes the existing policy that production mutations are outside the current Runner MCP mutation scope.

## Potential future usability improvement

A **read-only historical path preview** could be defensible if operators later demonstrate that the current release list is hard to reason about.

Such a preview could show, using bounded safe metadata only:

- current release ID;
- ordered direct-previous release IDs reachable from current;
- per-hop migration-boundary state;
- missing/unsafe-link blocked state;
- whether each hop would require a separate fresh approval.

It must not:

- accept an execution target;
- create or approve an action;
- enqueue multiple jobs;
- cross a migration boundary;
- activate releases;
- infer around missing metadata;
- expose paths, service units or private configuration.

However, `list_releases` already provides enough information for alpha operation, and Task 34 is separately adding retention-focused read-only visibility. There is no demonstrated need for another history-specific API now.

## Decision

Keep the implemented mutation model unchanged:

**direct previous release only, one approval, one job, one health check, then reassess.**

Do not add arbitrary target selection or automatic multi-step traversal.

No bounded CODE follow-up is queued by Task 35. If real operator feedback later shows that historical chain visibility is inadequate, review a read-only path-preview slice first; mutation semantics remain one-step regardless.

## Explicit non-goals preserved

This review does not authorize:

- `target_release` as a caller-selected mutation argument;
- arbitrary commit/ref activation;
- automatic multi-step rollback;
- approval of an entire future rollback path;
- skipping intermediate releases;
- crossing database migration boundaries;
- automatic or bundled database restore;
- production rollback;
- bypassing the existing deployment job/lock path;
- remote approval or typed-confirmation bypass.
