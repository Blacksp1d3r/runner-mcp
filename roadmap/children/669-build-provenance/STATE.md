# #669 — serving-generation provenance

status: SOURCE_OFFLINE_GUARDS_MERGED / CORRECT_HOST_WITNESS_WAIT
owner: Runner-MCP source lane (#669); Fabric authority/activation separately #924
source_main_version: 0.1.51
source_main_merge: 8104f244085adc68b8b705e9f7ec7a38dd69b2be
live_connected_serving_version: 0.1.38
active_loaded_wheel_verified: false
active_source_revision_verified: false
self_update_ready: false
production_changes_performed: false

## Accepted source-only progress (2026-10-20)

- Source 0.1.47 #760 false-green A6 Doctor classification; #761 six-SYNTHETIC-role witness denial tests.
- Source 0.1.48/0.1.49 #763/#764 private A6 parent-path and semantic fixed-key checks.
- Source 0.1.50 #766 installed-RECORD foreign/duplicate path denial (exact-head CI validation 39390108398, Ubuntu 39390108426, attribution 39390108361 PASS).
- Source 0.1.51 #767 offline evidence path canonicality (exact-head CI validation 39390980634, Ubuntu 39390980640, attribution 39390980656 PASS).
- Independent GitHub wheel/RECORD checks to 0.1.49 are OFF-HOST artifact consistency only. No trusted correct-host imported-code observation can yet be concluded.
- All source preflights intentionally keep `active_build_provenance_verified=false`, source revision and artifact digest NULL, even when their own offline signatures/bytes match.

## Not done: physical trust and activation

Original-client central v0.1.38 still reports source/digest unavailable, self_update_ready false, two Doctor failures. Historical `self-update-state.json` is rollback/transaction history, not current wheel identity. A6 private state 0/11, Fabric independent off-target journal #1617/#942 and A7 offline rollback #943 still unqualified. Original requester terminal result/ACK #609 not proved. Correct-host observer must bind actual loaded six process generations and launcher targets to owner-trusted pinned wheel/RECORD/source, a fresh bounded challenge and immutable rollback copy, then return public-safe categorical receipt without leaked host paths or secret material. Only Fabric #924 can later authorize one-node guarded activation after all gates; never bypass with generic shell or blind restart.

## Historical context

The earlier 2026-10-13 child branch proposing source 0.1.7 (review-waiting) is superseded by merges into main. Do not restart or reapply historical PRs or claim that the old branch describes current shipping source.
