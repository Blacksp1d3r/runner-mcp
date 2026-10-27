# #341 — provisional baseline retention checkpoint

2026-10-27: **SOURCE_CANDIDATE / CI_PENDING / LIVE_OPT_IN_FALSE / A7_NOT_QUALIFIED**.

Branch `chat-a/341-provisional-baseline-retention-20261027` restacked on main v0.1.95 commit `cdb9a910c7598c0c77c1fadc66c2ca0db40b3ea4` (workstream B PR #848 preserved); proposed v0.1.96. Existing self-update success disposal occurs before original-client reconnect: no physical bad-update test or real A7 acceptance. Candidate changes only existing `SelfUpdateManager` source and regression tests, no host mutation, service/cron/credential/tunnel update or additional backup.

One read-only connected `build_identity` tooltest still reports 0.1.88 with null source/digest. Earlier correct-host original PID/six-role alias evidence, AF-SB-0002 historic 0.1.38 escrow and Black/LAB consumed read-only SQL ACKs are reusable, not to be repeated. Future authorized deployment needs independent signed true loaded-process/wheel identity #669, Fabric A6 off-target #942, A7 physically installed boot-persistent six-role rollback #943 and same-campaign original-requester ACK. Opt-in remains OFF unless Fabric has qualified and deployed the existing local control path; no external commit/confirmation is implemented by this child.
