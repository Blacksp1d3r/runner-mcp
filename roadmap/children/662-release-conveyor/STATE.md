# #662 autonomous release conveyor — STATE, 2026-10-11

- Status: `VERSION_GATE_READY_REVIEW / AUTO_CANDIDATE_STAGED_IN_SOURCE / LIVE_AUTOPROMOTION_WAIT_A6_A7`.
- PR #661 current source candidate `40f25a271d399dedd45fd798c410d5e3ef4db1c5`, 9-file version metadata/CI/tests change; all exact-head checks SUCCESS; READY REVIEW, NOT merged, NOT published. Candidate source version 0.1.4 is NOT installed anywhere by this action.
- Runtime observed by operator/connected client remains legacy stored a0fd964c... / version 0.1.3, no confirmed external artifact digest. Source main last observed 2d025ce..., but always refresh GitHub.
- New source-only after-main-merge CI artifact builder in PR #661; no automatic host update or PyPI publish. Future trusted version allocator, independent release signer, off-target custody and A6/A7 admission required.
- PR #660 isolated exact old-source wheel on Python 3.12.15 verified and private Library archived; two bytewise wheel SHA differ despite same 91 unpacked member bytes. Not actual server loaded-module binary attestation.
- A7 Blacky synthetic local Ed25519 matrix 6/6 PASSED; real updated server/tunnel-loss original-client ACK not proven. A6 #942 not yet qualified. Runner-MCP tool catalog drift Q7 preflight explained by installed old source not containing newer registration (#590/#381).
- Failure Museum: RMCP-F-0034 release tag/version collision; RMCP-F-0035 non-identical archive hash across same-source builds; RMCP-F-0036 missing Q7 tool from old installed server source. New chat read issue #662, PR #661, these files, upstream AGENTS/roadmap/handover and GitHub live CI before editing.
- No production host, service, tunnel, source repo main, protected disk, provider, customer data or Claude dispatch was changed by this roadmap note.

Next: independent review/merge of #661, then trusted version allocator child on its own branch (respect other workers) and actual post-merge main candidate artifact receipt; do not convert staged code into live permission.

## 2026-10-12 release-integrity continuation

- PR #661 originally had two drift-prone lists: Python `needs_bump()` included operator installer and discovery metadata after patches, but post-main candidate-upload regex initially omitted them. New source head `57ef72f6e9654470c843645af790c2bd340022d4` now derives GitHub release outputs using the *same* `check_release_version.py` source rule, with added negative tests; exact-head CI pending as recorded. Failure Museum RMCP-F-0037.
- PR #663 stacked on #661 implemented `--expected-main` guard required for `--apply`: compare cached origin/main SHA to expected pinned SHA, refuse version <= latest locally observed main, preserve dry-run path, added tests for stale main and version collision. Current head `1c42c894d41aea91bc8ac6098e2729a6f3084bd9`, all three prior exact-head workflows SUCCESS, but PR base #661 has moved and needs current-base qualification before merging. A local cached ref **is not** a global distributed version lease; protected-branch current-head CI and unique published-artifact policy remain necessary.
- Neither #661 nor #663 is merged or deployed. Main and live installed source still old as last verified; no service/host/Wheel/backup-drive writes. Do not mistake staging for deployment.
