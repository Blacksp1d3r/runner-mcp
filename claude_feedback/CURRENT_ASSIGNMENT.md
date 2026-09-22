# Current assignment for Claude

Work from the latest `main` branch. Task 1 has been reviewed and merged through PR #42 as `3653e22f9618f0e00374ee3d008c5c435c94acdc`.

Read:
1. `AGENTS.md`
2. `claude_feedback/README.md`
3. `claude_feedback/NEXT_TASKS.md`
4. `roadmap/ROADMAP.md`
5. `handover/CURRENT_STATE.md`

Then execute **Task 2 — installer/operator robustness** from `claude_feedback/NEXT_TASKS.md`.

Primary scope:
- detect missing `sudo` before `install-operator.sh` attempts cross-account delegation;
- add regression coverage for that failure path without depending on the host actually lacking sudo;
- review reinstall/overwrite messaging and improve it only where behavior remains non-destructive and explicit;
- preserve service-user validation, wrapper ownership recognition, symlink refusal and private-config separation exactly;
- do not add automatic sudo setup, privilege escalation, uninstall or destructive cleanup.

Coordination constraints:
- create a fresh branch from current `main`;
- do not touch `self_update.py`, restart/activation handling or the self-update bridge contract;
- no private paths, credentials, service names or host-specific values in tests/docs;
- run Ruff, full pytest, clean demo and built-artifact validation through normal PR CI;
- update handover only for real behavior changes/defect fixes;
- open a focused PR.

When Task 2 is complete, take **Task 3 — secure I/O inventory and migration plan** next only as a design/inventory slice. Do not mass-refactor secure writes in the same PR.

If a security defect appears, keep the fix minimal and fail-closed, and document the newly proven regression.
