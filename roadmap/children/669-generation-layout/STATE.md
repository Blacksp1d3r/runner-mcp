# #669 generation-layout — current state

- Status COMPLETE_SOURCE_ONLY (not immutable or serving-attested).
- Branch chatgpt/669-immutable-generation-preflight-v0113, based on main 215218cd06786838ca3e7ea86ae770b07eec4a84.
- Candidate source version 0.1.13 in all four metadata files.
- Offline generation layout code/tests present; no root privileges or serving identity.
- Last live MCP version independently observed 0.1.9, active source/digest null.
- Next: open one PR, reconcile exact-head CI and source-merge only after green; no production release.
- Dependency: trusted builder manifest custody, sealing/independent storage attestation, process/venv/loaded modules, A6/A7, original-client ACK.

- 2026-10-16: PR #691 merged into main squash `c1407cc59be940451d4024b680ffa2c257ed1518` from exact head `06437f5b91e2ce00108630a91bdb821e408963ad`, validation/Ubuntu/attribution successful. No live upgrade.
