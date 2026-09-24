# Task 30 — automated retention pruning boundary review

Date: 2026-09-24

## Scope

Review only. No backup, release, metadata file or retention setting is deleted or changed. No new MCP/mailbox deletion authority is added.

Goal: define a fail-closed retention-pruning boundary for PostgreSQL backups and staging releases using the current retention policy without allowing an age/count calculation to become destructive authority by accident.

## Executive conclusion

**Automatic deletion is not ready for implementation.**

The current code has useful retention primitives, but deletion still has unresolved reference, policy and concurrency semantics.

The smallest safe next slice is a **read-only retention preview**. It should calculate what is protected, potentially eligible and blocked, without unlinking/rmtree, rewriting metadata or changing any retention setting.

Actual pruning must remain a later, separately reviewed mutation.

## Current retention policy

`RetentionPolicy` currently enforces:

- minimum releases to keep: default 20, range 2–1000;
- minimum release age: default 90 days, range 1–3650;
- PITR retention days: default 30 days;
- pre-migration backup retention: default 180 days;
- maximum automatic code rollback: exactly one release;
- explicit database-restore approval required;
- automatic production database restore prohibited.

### Release eligibility primitive

`release_is_deletable()` returns true only when both conditions hold:

1. the release rank from newest is outside the protected minimum count;
2. the release age meets/exceeds the minimum age.

This is a useful **policy eligibility predicate**, not a complete deletion authorization.

### Pre-migration backup eligibility primitive

`pre_migration_backup_is_deletable()` uses age only.

It does not know whether a backup is still referenced by a release or still required for recovery.

### Manual backups

There is currently **no retention/deletion policy for manual logical backups**.

Therefore manual backups must never be automatically selected for deletion by a future pruning implementation until a separate explicit policy exists.

### PITR setting

`pitr_retention_days` must not be applied to logical `.dump` backups. WAL/PITR storage/orchestration is not implemented yet.

## Current release metadata and protections

Each release metadata record contains:

- release ID;
- commit;
- creation timestamp;
- previous release ID;
- staging environment;
- whether migrations were applied;
- optional pre-migration backup ID.

`list_releases()` already reports:

- current;
- rollback eligibility;
- retention protection;
- previous release;
- migration state;
- pre-migration backup reference.

Metadata is validated fail-closed for identity, commit, timezone, environment and permissions.

### Important limitation

`retention_protected` currently means only “protected by minimum count/age”.

It does **not** mean “safe to delete if false”.

A release may still require protection because it is:

- the current active release;
- the direct rollback target of the current release;
- referenced as `previous_release` by a retained release;
- part of a migration/recovery boundary whose pre-migration backup remains operationally relevant;
- being created/activated/rolled back by an in-flight deployment operation.

Any future UI/API must avoid renaming `retention_protected=false` to `deletable=true`.

## Current backup metadata and protections

Logical backup metadata exposes safely:

- backup ID;
- project;
- kind: `manual` or `pre_migration`;
- created_at;
- size_bytes;
- PostgreSQL engine;
- availability.

The underlying storage uses private per-project directories and 0600 dump/metadata files.

### Important limitations for deletion

The current `list_backups()` is a safe listing surface, not a destructive-validation surface.

It intentionally skips malformed metadata, and its availability check does not currently prove all facts required before deletion, such as:

- metadata file mode itself;
- exact dump-size match to recorded `size_bytes`;
- strict metadata shape/no unknown fields;
- duplicate-key rejection;
- whether a pre-migration backup is referenced by retained release metadata;
- whether the database operation lock is currently held.

Deletion must not be implemented by taking the existing list output and unlinking those IDs.

## Reference integrity

### Current release

The active `current` symlink target is always protected, regardless of count/age.

### Direct rollback target

The release referenced by the active release's `previous_release` is the only current one-step rollback target.

It must not be deleted while that reference is live.

### Older release chain

Retained release metadata may point to older releases through `previous_release`.

Pruning creates a product-policy question:

- either retain enough of the chain that subsequent separately approved one-step rollbacks continue to work;
- or permit an intentional chain boundary where an old `previous_release` becomes unavailable.

The current product contract does not define that boundary. A deletion implementation must not guess.

A preview may safely report reference relationships and a `blocked_by_release_reference` category.

### Migration backup references

A release with migrations applied may record `pre_migration_backup_id`.

Any pre-migration backup referenced by a release that remains retained must be protected from deletion even if it is older than `pre_migration_backup_days`.

The current age-only retention helper is therefore insufficient as a destructive authorization.

## Concurrency boundary

### Database operations

`DatabaseManager` already uses a per-project non-blocking lock around:

- manual backup;
- migration apply, including creation of the pre-migration backup.

A future backup-pruning mutation must use the **same per-project database-operation lock** so it cannot race backup creation or migration.

A read-only preview may inspect without mutation, but must clearly be treated as advisory. Actual deletion must re-evaluate under the lock.

### Deploy/rollback operations

`DeploymentManager` already uses a per-project lock around deploy and rollback.

A future release-pruning mutation must use the **same deployment lock** and recompute current/reference/retention state after acquiring it.

It must not rely on a preview created before an in-flight deploy/rollback.

### Cross-manager dependency

Deployments may invoke database migrations while holding the deployment lock, and migration uses the database lock.

Any future operation that needs both release and backup state must use a documented lock ordering compatible with the existing deploy -> database sequence.

A pruning implementation must not acquire database then deployment in the opposite order, because that creates a lock-order/deadlock hazard.

Recommended order when both are required:

1. deployment lock;
2. database lock.

A read-only preview should avoid holding both for long periods.

## Symlink/path/TOCTOU boundary

A destructive pruning implementation must not:

- accept a caller-supplied path;
- accept a caller-supplied release directory;
- accept a caller-supplied backup dump path;
- follow symlinks;
- delete a directory/file based only on earlier `Path.stat()` data.

Before deletion it must derive the target only from a validated project + validated ID under the configured private root and revalidate containment/type/identity while holding the relevant operation lock.

For release directories, recursive deletion is higher risk than metadata reads. A future implementation needs a dedicated no-symlink tree-deletion contract rather than directly calling `shutil.rmtree()` on a previewed path.

For backup pairs, dump + metadata deletion must define ordering and crash recovery. Removing one and crashing before the other must not leave a record that can be mistaken for a valid recovery point.

## Emergency-stop and approval semantics

Pruning is destructive even though it is housekeeping.

Recommended policy:

- **preview:** read-only, available while emergency stop is active;
- **actual pruning:** staging/local mutation only, blocked by emergency stop;
- initial actual pruning should require explicit local typed confirmation bound to a fresh plan;
- do not add pruning to the GitHub mailbox/MCP mutation allow-list in the first implementation;
- do not reuse deploy/migration approval actions because pruning has different binding/retention semantics.

Unattended automatic pruning should remain a later decision after local plan/execute semantics are proven.

## What can be automated safely today

Only **read-only calculation**.

A safe preview can derive bounded categories such as:

### Releases

- `current`
- `rollback_target`
- `retention_count_or_age`
- `referenced_by_retained_release`
- `migration_recovery_reference`
- `potentially_eligible`

### Backups

- `manual_policy_missing`
- `pre_migration_age_protected`
- `referenced_by_retained_release`
- `unavailable_or_invalid`
- `potentially_eligible`

“Potentially eligible” must explicitly mean **not authorization to delete**.

## Smallest recommended CODE follow-up

Create a local/read-only retention preview task only.

Suggested scope:

1. add strict private scanners/planners for release and backup retention state;
2. reuse current count/age policy predicates but layer reference/current/rollback protections on top;
3. never treat manual backups as deletion candidates;
4. expose safe categories through local CLI such as:
   - `runner-mcp retention preview PROJECT`;
5. return IDs/timestamps/kinds only if they are already considered safe by existing public metadata contracts;
6. do not return filesystem paths;
7. do not delete or rewrite anything;
8. do not add approvals, MCP tools or mailbox actions;
9. work while emergency stop is active because it is read-only;
10. include a deterministic/private plan fingerprint internally only if useful for a later execute design.

## Required regression matrix for preview

### Release preview

- current release always protected even if count/age would allow deletion;
- direct current rollback target always protected;
- minimum-count protection;
- minimum-age protection;
- count and age must both permit before potential eligibility;
- retained-release references produce a blocked category;
- migration metadata/reference remains visible only as safe categorical state;
- unsafe release metadata fails closed;
- symlink release directory/metadata fails closed;
- production project is read-only/ineligible for mutation planning;
- no path/unit/health URL leaks.

### Backup preview

- manual backup never becomes automatically eligible;
- young pre-migration backup protected;
- old pre-migration backup still protected while referenced by a retained release;
- old unreferenced pre-migration backup may be marked potentially eligible;
- unavailable/malformed/symlink/broad-permission/size-mismatch metadata cannot become eligible;
- no dump path/DSN/hash/content leak;
- no database subprocess or connection is used.

### Cross-boundary

- preview performs zero deletion calls;
- preview remains available during emergency stop;
- no MCP/mailbox action is added;
- no retention setting is changed.

## Requirements before actual deletion can be designed

A later pruning-execute review must resolve:

1. policy for manual backups;
2. exact rollback-chain boundary after old release deletion;
3. crash-safe paired backup dump/metadata deletion;
4. no-symlink recursive release-tree deletion;
5. lock ordering and revalidation;
6. whether pre-migration backups referenced by pruned releases may be deleted in the same transaction;
7. typed local confirmation/plan binding;
8. audit record shape without private paths;
9. interruption recovery after partial pruning.

Until those are defined and tested, automatic deletion remains deferred.

## Recommendation

Do **not** add automatic pruning yet.

Add one bounded read-only retention-preview implementation next. It gives operators visibility into what the current policy would protect or potentially permit, surfaces the missing policy/reference semantics, and creates testable evidence for a later mutation review without risking data loss.
