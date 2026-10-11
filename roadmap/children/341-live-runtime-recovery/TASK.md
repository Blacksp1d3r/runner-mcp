# Runner-MCP #341 — live first-node recovery evidence (TASK)
Owner: existing #341 update lane. Separate source/documentation only; do not take over A7, #590, #428, or #653–#657 worker claims.

Goal: map correct active MCP server build/route and verify separately recoverable baseline before an ATTENDED single-node update. A7 autonomous fleet rollback and Claude Q3/Q7 non-RUN are parallel independent work.

Inputs: operator-confirmed active server stored revision a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a; no pending install transaction; ZERO temporary managed wheel files; one real local listener; two separate completion/GitHub watchers; active tunnel. Main at check 2d025ce72443853795aa87b4ec96b83a25064634.

Steps: (1) reconcile GitHub issues/PRs/owners; (2) verify exact correct-host process UID, executable/module digest, configuration generation, source tree, wheel provenance and loopback listener ownership using first-party trusted local collector; (3) bind tunnel and original-client good+failing request and audit/results/ACK; (4) verify IMMUTABLE old baseline wheel and operator-owned off-band recovery, restore rehearsal and safe stop; (5) request host-specific scoped human approval for a one-node attended pinned reviewed-main update only after previous checks; (6) collect post-update original-client result+ACK, revert or reconcile on unknown effect; (7) consider independently qualified second host.

Forbidden: guessing IDs/ports/hosts, releasing main branch PRs without reviews, arbitrary shell/TOFU/password/credential copies, killall/cron edits/tunnel restarts, external disk writes, customer data, backup volume reuse, live updates to make escrow magically exist, paid API calls, Claude dispatch, production effect based on docs.

Failure Museum cases: RMCP-F-0031 final argv after execv; RMCP-F-0032 missing independently verified recovery escrow despite healthy status; RMCP-F-0033 hostname DNS/SSH client false negatives.

Acceptance: exact source/process/artifact, independent restored previous package, operator off-band path and isolated abort proven with explicit signed/fenced context; original-client result+ACK; otherwise WAIT_LIVE_UPDATE while safe source/CI and Q7 non-RUN continue.
