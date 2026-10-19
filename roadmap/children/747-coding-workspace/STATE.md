# #747 state — 2026-10-19

- SOURCE IMPLEMENTATION: in GitHub PR under `feat/747-bounded-worker-workspace-v0140`; CI pending.
- OPERATOR PHYSICAL ROOTS: Claude and Qwen base directories are present according to user readback. Do not recreate roots or alter VM disk.
- CENTRAL ACTIVE HOST: different node, v0.1.38 last verified; this source candidate is NOT installed. The current original-client Agent Bus relay/mutation remains UNKNOWN/OFF. No cross-host filesystem write has occurred.
- NEXT: exact-head source CI; if green and allowed, guarded source merge. Then privately configure worker-owner local service binding without sudo/broad Incus permissions; confirm caller sees same-host authenticated worker tool, capture original-client request/receipt/ACK through correct per-target Agent Bus when independently admitted. The worker must produce the first actual patch separately.
- FAILURE BEHAVIOR: absent/partial root, group-writable/symlink, wrong UID or guest, stale claim and capacity ceiling all deny with no arbitrary filesystem mutation. Audit caller receipt only; do not publish server paths, private identities or tokens.
