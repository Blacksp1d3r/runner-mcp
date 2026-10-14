# #669 — Source-only child STATE (2026-10-13)

child_id: RMCP-669-PROVENANCE-FAIL-CLOSED
status: WAITING_CI_AND_INDEPENDENT_REVIEW
owner: Runner-MCP source lane / bounded
branch_or_worktree: fix/669-no-stale-active-build-v017-20261013
base_revision: 1667b20a2d6d6ed0fa88d1cddebdb5e0647fe420
release_version: 0.1.7 (proposed, neither released nor installed)
source_only: true
production_changes: false

## Verified facts at start
- Parent 661, 668, 670 all OPEN, no official submitted independent reviews.
- Physical operator's v0.1.4 manual wheel was tested 100/100 source-file-equal, but build_identity reported old self-update commit.
- Active tunnel control plane authenticated after attended tunnel cron-PATH workaround; AIfordable topology attestation absent and Fabric synthetic status unqualified.
- Existing Blacky public static triage #661 had 2 advisory RF-PR-007, #668 and #670 had 0 heuristic findings; neither constitute independent GitHub approval.

## This source branch
- Renames old historical transaction reader; current-source marker now explicitly UNVERIFIED.
- In-memory module version versus mutable distribution metadata separate.
- Tests cover false provenance under manual wheel and hot-update simulation.
- Full separate artifact attestation and independent active-runtime digest NOT yet delivered.

## Next step
Check exact-head CI; fix any test failures within this branch, update test evidence and review receipt. Independently review #661, #668, #670 then #669. No merge, self-update, restart, credential change or tool catalog refresh authorized by this source-only child.
