# Staging deployment safety

Runner MCP Phase 6 deploys configured staging projects only.

Production deployment remains prohibited.

## Source of truth

A deployment uses the clean Git `HEAD` of the configured project working tree.

The MCP client cannot supply a branch, tag, commit, archive path or shell command.

Preflight requires:

- a Git working tree;
- no tracked modifications;
- no untracked files;
- a full HEAD commit hash;
- a staging project environment;
- a configured restartable service alias with a health check;
- every required test profile to exist;
- database backup + migration configuration when deploy migrations are enabled.

Git preflight/archive calls use fixed argument arrays with `shell=False`. System/global Git configuration is constrained and Git hooks/fsmonitor are disabled for these operations.

## Release creation

Runner MCP creates a new release directory from `git archive` of the verified commit.

Repository symlinks are rejected from release archives in the current implementation.

Release directories are never reused or overwritten by Runner MCP. This is logical release immutability; it is not a filesystem-level immutable-bit guarantee against the Linux account that owns the files.

Private deployment storage uses mode 0700 for the release root, release collection and runtime HOME.

The active release is selected by a `current` symlink inside the configured release root. Activation replaces this symlink atomically.

## Required tests

Configured required test profiles run before release creation.

After the tests complete, Runner MCP checks the Git working tree and HEAD again. A test or external process that modifies the source tree causes deployment to fail before a release is activated.

## Database migrations

When deploy migrations are enabled:

1. source state is rechecked;
2. the Phase 5 migration workflow creates a pre-migration database backup;
3. the operator-stop state is rechecked;
4. the predefined migration command runs;
5. only a successful migration can proceed to release activation.

A failed migration never activates the new release.

## Activation and health

After activation Runner MCP restarts only the configured service alias and waits for both:

- service active state;
- configured health result `healthy`.

A service without a health check cannot be used for automated staging deployment.

## Automatic code rollback

If activation/health fails and no database migration was applied, Runner MCP may automatically reactivate exactly one previous release and restart the service.

This follows the global one-step rollback rule.

If database migrations were applied, automatic code rollback is not performed. The result is `failed_manual_recovery_required`, because old code may be incompatible with the new database schema.

Runner MCP never automatically restores the database.

If the operator emergency stop is active, Runner MCP does not continue with mutating rollback actions.

## Asynchronous deployment jobs

`deploy_staging` creates a private background job and returns immediately.

`deployment_status` returns persisted safe metadata and the final safe deployment result.

Deployment job files use restrictive permissions. A job that was queued/running when Runner MCP restarts is marked `interrupted`; it is never silently resumed.

The emergency stop is the external operator control for an in-progress deploy. Long operations finish or stop at their defined safe checkpoints.

## Current limitations

Phase 6 does not yet provide:

- generic build hooks or arbitrary build shell commands;
- production deployment;
- release retention pruning;
- manual historical rollback selection (Phase 7);
- filesystem immutability against the runtime Linux account;
- deployment adapters for every framework/runtime.

Project-specific preparation should remain explicit and trusted. Future adapters must preserve the same deny-by-default model.
