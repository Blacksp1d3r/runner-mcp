# Runner-MCP #662 — concurrent source release admission

Status: **SOURCE MERGED** into main v0.1.45 by PR #753 squash `8dbbd1263f32c868df259ad2c77b7306faf683c1`. Final ready-head release admission + all CI PASS in workflow #39316596943, Ubuntu #39316597003 and attribution #39316597250. Required branch protection, automatic promotion and live host deployment remain UNVERIFIED.

The new CI job uses existing read-only GitHub API permissions and an exact PR synthetic merge. It checks current main SHA/version, expected PR base and head, open merge-eligible PR version metadata, duplicate reservations, strictly the next patch release, and postchecks main freshness. Documentation-only PRs skip reservation. Unknown API/metadata/page overflow or stale source evidence cause WAIT/FAIL. It never updates another PR branch, generates credentials, publishes artifacts or activates a host.

A passing CI result is still **not** an atomic version lock. Enforce branch protection making Release reservation admission required, require the PR be current with main OR a merge queue that recomputes the check per final merge, and serialize main merges under one release steward. Without independently verified GitHub policy configuration, treat this as an advisory preflight rather than guaranteed conflict prevention. PRs #743/#745/#750 have now merged in order as source 0.1.42/0.1.43/0.1.44. PR #753 was marked READY and the real release-admission job passed against current main 0.1.44; this is not GitHub branch-rule enforcement or permission to deploy. No one may skip source release sequencing, and every later change requires a fresh exact-head full CI check.

Dependencies: release conveyor #662, canonical cross-project coordination Runner-Fabric #924, AIfordable #609, provenance #669 and PRs #743/#745/#750. GitHub source merge never certifies the installed Runner-MCP or Agent Bus. Preserve historical self-update state and actual current 0.1.38 diagnostic failures.

## Same-version coordination and freshness

Two READY PRs that propose the same next patch do not have to deadlock each other. The lower numbered PR has deterministic first priority; the other stays WAIT/rebases. An explicit release steward can change priority by moving the earlier PR back to draft, closing it or changing its candidate source and rerunning checks. Before and after inventory the checker independently re-reads the current candidate PR open/draft/base/head from GitHub, so an event from an obsolete head does not grant even provisional admission. Incomplete inventory and duplicate PR IDs fail closed. This priority rule is not an atomic queue and does not replace required checks + merge serialization.

## Required GitHub configuration and queue compatibility (still unverified)

As of 2026-10-19, GitHub's main branch-protection API returns HTTP 403 to this integration; the branch rules cannot be inspected or changed here. This check is therefore **not yet enforced** on merges, even though the source exists and test jobs pass. Ask a repository administrator to verify and require the exact job name `Release reservation admission` on main, together with current-main/up-to-date branch checks and one release steward who serializes source merges. The installed central Runner-MCP version is not affected.

**Do not enable GitHub merge queue for this new job yet.** The current Runner-MCP validation workflow listens to `pull_request` and `push` but does not implement `merge_group` admission. Before activating merge queue, implement a separate source child that reruns the complete source-version admission and mandatory CI on each merge-group synthetic SHA, including stacked/multi-PR ordering, then qualify it under protected branch rules. A skipped check on merge_group is not admission.

## Intermediate inventory race and bearer transport

The read-only admission guard now collects the competing READY PR-version inventory **twice**, before and after the proposed-release check; any contender becoming READY, closing, retargeting or changing version during that window fails closed rather than admitting against stale data. It also rereads the candidate PR identity and main SHA. This is an early race detector, **not** a post-CI atomic merge lock; a required fresh status/serialized merge remains essential. All scoped GitHub API requests explicitly use `ProxyHandler({})` and no redirects, preventing inherited proxy environment settings from forwarding the bearer credential. No credentials or raw API response bodies appear in diagnostic output.
