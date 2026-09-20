# Controlled release rollback

Runner MCP Phase 7 supports safe release inspection and one-step code rollback for staging only.

Database restore is not part of release rollback.

## Release history

`list_releases` returns safe metadata only:

- release ID;
- Git commit;
- creation time;
- direct previous release;
- whether the release is current;
- whether that release applied database migrations;
- optional pre-migration backup ID;
- whether retention policy currently protects it;
- whether the current release is eligible for code rollback.

No release filesystem path is returned.

Release metadata files must exist, match their directory identity, contain a valid commit/timestamp/environment, and use restrictive permissions. Invalid or tampered metadata fails closed.

## Retention policy

Retention protection uses both minimum count and minimum age.

With the default policy, a release is protected when it is within the newest 20 releases OR is younger than 90 days. It becomes eligible for future cleanup only after both protection thresholds are exceeded.

Phase 7 does not delete releases automatically. The `retention_protected` flag is informational groundwork for a future pruning operation.

This means a project with only a handful of releases over a year does not lose history merely because a numeric retention limit exists.

## One-step rollback

The client cannot choose an arbitrary target release.

`rollback_plan(project)` resolves the direct previous release from trusted release metadata.

`rollback_release(project)` starts exactly that rollback as an asynchronous job.

Unknown MCP tool arguments are globally rejected, so a client cannot smuggle a `target_release`, branch or other ignored control field into the call.

After a successful rollback, a later separate rollback action may move one additional step back, after a fresh plan and health assessment.

Runner MCP never cascades automatically through multiple historical releases.

## Database migration boundary

If the currently active release recorded `migrations_applied=true`, Runner MCP blocks code rollback.

This prevents old application code from being automatically paired with a newer database schema whose backward compatibility is unknown.

The pre-migration backup reference remains visible as metadata, but Runner MCP does not automatically restore it.

## Health behavior

Rollback performs:

1. operator-safety check;
2. direct previous-release resolution;
3. atomic current-symlink switch;
4. configured service restart;
5. service/health verification.

If the rollback target fails health and the emergency stop is not active, Runner MCP reactivates the original current release and restarts it.

This is recovery from a failed rollback, not a second historical rollback step.

If the emergency stop is active, Runner MCP does not continue mutating recovery actions.

## Asynchronous jobs

Rollback uses the same private persisted job model as staging deployment.

A project cannot have a deploy and rollback job active at the same time.

Jobs that were queued/running when Runner MCP restarts are marked `interrupted` and are never silently resumed.

## What is still excluded

Phase 7 does not provide:

- database restore;
- arbitrary target selection;
- multi-step automatic rollback;
- production rollback;
- automatic retention pruning.
