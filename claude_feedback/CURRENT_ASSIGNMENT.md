# Current assignment for Claude

Work from the latest `main` branch.

Read:
1. `AGENTS.md`
2. `claude_feedback/README.md`
3. `claude_feedback/NEXT_TASKS.md`
4. `roadmap/ROADMAP.md`
5. `handover/CURRENT_STATE.md`

Then execute **Task 1 — direct configuration and adapter regression coverage** from `claude_feedback/NEXT_TASKS.md`.

Constraints:
- create a fresh branch from current `main`;
- focus on direct unit/regression coverage for `Settings.from_mapping()` and adapter registry/capability fail-closed behavior;
- production-code changes should be zero unless a new test demonstrates a real defect;
- do not touch self-update/restart/activation implementation;
- do not weaken or expose private path/environment/credential information;
- run Ruff and the full pytest suite;
- open a PR with a concise summary of the newly direct-covered contracts;
- update `handover/CURRENT_STATE.md` only if behavior changed or a real defect was fixed;
- do not create a second roadmap status table.

If you find a real security defect, stop broadening the task, add the smallest failing regression test and apply the smallest fail-closed fix.

When this task is complete, leave the next recommended task from `NEXT_TASKS.md` clearly identified in the PR or handover so another agent can continue without re-analysis.
