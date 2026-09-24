# Task 40 — retention pruning execute-boundary review

Date: 2026-09-24

Status: **COMPLETE — review only. No deletion performed.**

## Scope

This review starts from Task 30's fail-closed pruning analysis and Task 34's implemented local read-only retention preview.

No release, backup, metadata file or retention setting is deleted or rewritten. No pruning approval, MCP action, mailbox action or unattended scheduler is added.

## Executive conclusion

A first **local manual release-pruning** slice is now bounded enough to specify, but only for the narrowest class already proven by Task 34:

- staging projects only;
- local CLI only;
- emergency stop must be inactive;
- exactly one release per confirmed execution;
- candidate must be `potentially_eligible` under a freshly recomputed strict preview;
- candidate must not be current, direct rollback target, in the retained `previous_release` closure, retention-count/age protected, or a migration-recovery boundary;
- the release must first be atomically quarantined under the private release root and only then recursively removed with a symlink-safe fd-relative deletion primitive;
- no backup is deleted in this first code slice.

Automatic pruning remains deferred.

Backup pruning also remains deferred because the current flat `.dump` + `.json` pair needs its own crash-recovery transaction contract.

## Evidence from Task 34

Task 34 materially improves the boundary over the Task 30 state.

The strict preview now:

- validates private 0700 release/backup directories;
- validates release metadata shape, identity, timestamp, commit, environment and migration reference;
- validates backup metadata shape, identity, timestamp, kind, engine and size;
- rejects symlink metadata and dump files;
- verifies 0600 private-file permissions;
- rejects incomplete backup dump/metadata pairs;
- verifies dump size against metadata;
- validates the current release pointer;
- detects missing release references and cycles;
- applies minimum-count and minimum-age policy only as protection inputs;
- protects the current release and direct rollback target;
- computes retained release-reference closure;
- protects every release carrying a migration recovery reference;
- protects pre-migration backups referenced by retained releases;
- keeps manual backups categorically non-eligible;
- marks production/non-staging state read-only;
- exposes no filesystem paths or credentials.

This is sufficient to define a conservative mutation plan, provided execution recomputes the same state while holding the correct mutation lock.

## Manual-backup policy

No automatic/manual deletion policy exists for `manual` backups.

The safe resolution for the first pruning implementation is therefore:

**manual backups have indefinite retention and are never pruning candidates.**

Do not add a hidden default age. Do not infer `pitr_retention_days`. Do not repurpose `pre_migration_backup_days`.

A future manual-backup retention setting must be an explicit separately reviewed policy change.

## Release-chain boundary

Task 34's retained-reference closure gives a conservative and useful first rule:

**the first executable pruning slice must not create a rollback-chain boundary.**

Any release reachable from a retained release through `previous_release` remains protected. Because the current release is retained, the historical chain behind the current release remains intact.

This means the first release-pruning implementation can remove only releases that are outside the retained chain, such as old orphan/non-activated release artifacts, and only when count/age policy also permits.

This deliberately sacrifices aggressive disk reclamation in exchange for preserving the existing one-step rollback contract exactly.

A later product decision may define an intentional historical boundary, but that is not required for the first safe slice.

## Migration boundary

Task 34 currently protects any release with `pre_migration_backup_id` as a migration-recovery boundary, even if it is otherwise orphaned.

Keep that rule for the first pruning execution.

Therefore the first release-pruning implementation must not:

- delete a release carrying a migration backup reference;
- delete a pre-migration backup as a side effect of release deletion;
- cascade release and backup deletion in one operation.

This keeps code-release deletion independent from database recovery data.

## Locking and revalidation

Preview output is advisory and may be stale.

Actual release pruning must use the **same per-project deployment lock** used by deploy/rollback and must recompute all release state after that lock is acquired.

For any future operation touching both releases and backups, lock ordering remains:

1. deployment lock;
2. database lock.

Never acquire the database lock first and then the deployment lock.

The first recommended CODE slice touches releases only, so it should acquire only the deployment lock.

Execution must fail rather than wait indefinitely when another deployment/rollback operation owns the lock, matching the existing non-overlap model.

## Plan binding and typed local confirmation

Do not execute directly from `retention preview` output.

The first executable pruning path should use a short-lived private plan stored under Runner MCP private state.

The plan should bind at least:

- project code;
- environment;
- candidate release ID;
- current release ID;
- candidate release metadata digest;
- retention-policy fingerprint;
- planned operation version;
- creation/expiry time;
- random single-use plan ID.

The operator-facing plan may show only safe values already allowed by the preview contract: project, release ID, timestamp and bounded reason/category.

Recommended local confirmation phrase:

`PRUNE RELEASE <project> <release-id>`

Immediately before quarantine, while holding the deployment lock, Runner MCP must recompute preview state and the private binding.

Any change in current release, metadata, candidate eligibility, retention policy or plan expiry invalidates the plan.

Plans are single-use. A failed or stale plan requires a fresh plan.

Do not reuse the migration/deploy/rollback remote approval machinery for this first local housekeeping action.

## Emergency-stop and environment semantics

Release pruning is destructive.

Required execution boundary:

- project environment must be exactly `staging`;
- retention policy must be confirmed;
- operator-stop mechanism must be configured;
- emergency stop must be inactive;
- planning/preview remains available while the stop is active;
- production remains read-only and cannot produce an executable prune plan.

Do not create a recovery-mode exception for pruning.

## Release quarantine before deletion

Deleting a release tree directly in place makes crash recovery and path races harder.

The first implementation should use an atomic quarantine step under the same private release root.

Recommended private structure:

- existing active releases: `<release_root>/releases/<release_id>`;
- private quarantine: `<release_root>/.prune-quarantine/`;
- private transaction records: `<release_root>/.prune-transactions/`.

Both private directories must be non-symlink directories with mode 0700.

Execution sequence:

1. acquire deployment lock;
2. recompute strict retention state;
3. revalidate plan binding;
4. create and fsync a 0600 transaction record;
5. atomically rename the exact candidate release directory from `releases/` into `.prune-quarantine/` on the same filesystem;
6. fsync the active releases directory and quarantine directory;
7. mark the transaction `quarantined` durably;
8. recursively remove the quarantined tree using a symlink-safe fd-relative deletion primitive;
9. fsync quarantine directory;
10. mark/delete the transaction record durably;
11. release the deployment lock.

Once the atomic rename succeeds, the release is no longer part of active release inventory. A crash after that point leaves an explicit private quarantine/transaction state rather than a half-deleted active release.

Do not expose quarantine paths or transaction filenames publicly.

## No-symlink recursive deletion contract

Do not call path-based `shutil.rmtree()` without proving its symlink-attack resistance.

The implementation may use Python's fd-based `shutil.rmtree(..., dir_fd=...)` only when `shutil.rmtree.avoids_symlink_attacks` is true on the running platform, with the quarantine parent opened safely and the child addressed relative to that descriptor.

Otherwise pruning must fail closed.

Before quarantine, the candidate itself must be the exact validated non-symlink release directory under the configured releases directory.

Do not follow repository-created symlinks or special filesystem nodes during destructive traversal.

## Crash/interruption recovery for release pruning

Recovery should be local-only and must not run as a generic server startup mutation.

A local `retention prune-recover` or equivalent later helper may inspect private transaction records and quarantine entries.

Safe recovery actions are limited to:

- finish deleting a release already atomically quarantined by a valid transaction; or
- report an inconsistent transaction as `manual_attention_required`.

Recovery must never move a quarantined release back into active history automatically and must never choose a different release to prune.

The emergency-stop policy for finishing an already-authorized quarantine should be reviewed in the implementation task. The conservative first choice is to require stop inactive for all prune mutations, including cleanup.

## Backup pair deletion

Do not include backup deletion in the first CODE slice.

For a later backup-pruning task, a private deletion transaction must exist before either member of the `.dump` + `.json` pair is removed.

A safe sequence would require:

1. database-operation lock;
2. fresh strict backup/release-reference revalidation;
3. durable 0600 transaction record containing backup ID and private content/metadata binding;
4. delete or quarantine the dump;
5. fsync project directory;
6. delete or quarantine metadata;
7. fsync project directory;
8. clear the transaction.

If interrupted, the strict preview is allowed to fail closed until the local transaction recovery finishes.

No incomplete pair may ever be reported as a valid recovery point.

Because this needs a dedicated recovery contract and a decision on file quarantine versus unlink ordering, it should remain a separate CODE task after release pruning is proven.

## Pre-migration backup candidates

Even later, only `pre_migration` backups may enter retention pruning under the current policy, and only if all of the following are true under the database lock:

- older than `pre_migration_backup_days`;
- strict private metadata/dump validation succeeds;
- not referenced by any retained release;
- not referenced by any active prune/deploy/migration transaction.

Manual backups remain excluded.

## Audit/result contract

A pruning execution audit/result may contain only bounded safe fields such as:

- action = `prune_release`;
- project code;
- plan ID or deterministic non-secret event ID;
- release ID;
- state = `planned`, `quarantined`, `completed`, `failed`, or `manual_attention_required`;
- bounded failure category;
- timestamp.

Never include:

- release-root/quarantine paths;
- repository filesystem paths;
- service units;
- DSN/database details;
- raw exception text;
- file listings or contents.

## First CODE follow-up justified

A bounded first mutation slice is justified now, limited to **one local staging release per execution**.

Recommended Task 43 scope:

- add local `retention prune-plan PROJECT` for the oldest deterministic release that is freshly `potentially_eligible`, or return no candidate;
- add local `retention prune-release PROJECT PLAN_ID` with typed confirmation;
- execute at most one release per plan;
- acquire the deployment lock and recompute strict eligibility before mutation;
- use private durable transaction state plus same-filesystem quarantine;
- use only symlink-safe fd-relative recursive deletion;
- retain full current/rollback/reference closure and every migration-boundary release;
- no backup deletion;
- no manual-backup policy change;
- no automatic/unattended pruning;
- no production mutation;
- no MCP/mailbox/bridge action;
- no generic arbitrary path or release ID supplied by a remote client.

## Required tests for Task 43

At minimum:

- current release can never be planned;
- direct rollback target can never be planned;
- any retained-reference ancestor can never be planned;
- count/age protected release can never be planned;
- migration-boundary release can never be planned;
- production cannot create executable plan;
- emergency stop blocks execute but not preview/plan inspection;
- deterministic candidate selection;
- stale current pointer invalidates a plan;
- changed metadata invalidates a plan;
- changed retention policy invalidates a plan;
- deployment-lock contention fails before mutation;
- candidate symlink fails closed;
- quarantine parent symlink/broad permissions fail closed;
- transaction record is private and durable;
- atomic rename occurs before recursive deletion;
- fd-safe deletion capability absent => fail closed;
- interruption after quarantine leaves recoverable private state;
- repeated execution of same plan is rejected;
- no path/secret/raw exception leakage;
- no backup file is touched;
- no MCP/mailbox action exists.

## Automatic pruning

Still deferred.

Unattended pruning should not be considered until:

- local one-release execution is proven;
- crash recovery is proven;
- backup pair pruning is separately proven;
- retention policy changes have explicit operator UX;
- observability exists for pending prune transactions.

## Conclusion

Task 34 supplies enough strict read-only evidence to move one step beyond preview, but not to general retention automation.

The next safe mutation is a deliberately conservative local one-release prune that can only remove an old non-migration orphan outside the entire retained rollback chain. Quarantine and durable transaction state make interruption recoverable without treating preview eligibility as destructive authority.

Backup pruning, historical chain cutting, manual-backup deletion, unattended pruning and all remote deletion authority remain deferred.
