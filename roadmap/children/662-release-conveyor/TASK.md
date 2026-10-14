# #662 — Autonomous, versioned Runner-MCP release conveyor (TASK)

Umbrella: https://github.com/Blacksp1d3r/runner-mcp/issues/662 . This is a read-only ownership/roadmap handoff, not new host authority or an unreviewed release.

## Goal
After every approved source/tool improvement, automatically assign/persist a NEW numeric version, build immutable source-matched wheel and release candidate, stage it independently, and once the A6/A7 first-party gates pass, promote one node at a time with original-client ACK or autonomous rollback. No perpetual human/AI 'doe verder' loop.

## Bounded children
1. `VERSION-GATE` — code, tool, script, installer, release workflow must strictly increase SemVer relative to latest main. Synchronize pyproject, server registry top+packages, runtime __version__, and glama metadata. PR #661 (first pending v0.1.4) exact-head validation green, **not merged/published/deployed** at this checkpoint. Independent review before merge.
2. `VERSION-ALLOCATOR` — future trusted event-driven source worker must allocate/claim next semver without races across concurrent PRs, compare against latest main and any existing publication, and update the four metadata carriers atomically on its own branch. Source must fail closed if another branch claims version; never rewrite a published artifact. No generic host shell privilege.
3. `CANDIDATE-BUILDER` — after reviewed code merge to protected main, automatic CI creates wheel/sdist, exact source SHA, version and SHA256SUMS; branch policy #661 adds job. Verify artifact independently; GitHub expiry is short and NOT an independent backup.
4. `INDEPENDENT-ESCROW` — #341 retains one independently signed/hash-verified previous wheel, trusted read-only active process/package provenance, off-target restore rehearsal and operator-owned out-of-band route. Existing historic old-source wheel in private Library is reconstructed candidate only (actual binary equality not shown).
5. `SAFE-A6-A7-PROMOTION` — Fabric A6 #942/#1039 collects off-target verified attempt journal and same-path A3 result; Fabric A7 #943 proves authentic ACK and self-rollback when original client absent, tampered/expired ACK and real tunnel outage. Integrate with actual first-party service and verified current host (#428), never pass source fixtures as live authority.
6. `DEPLOY-FEEDBACK` — for each reviewed version and each enrolled host, issue bounded prepared/active/committed or reverted receipt, original-client ACK and exact runtime tool catalogue; unknown effect enters STOP/RECONCILE and alerts one actionable exception; next node only after previous is confirmed.
7. `PUBLISH` — independently reviewed PyPI/MCP registry/GitHub release tag from exact artifact after required gates; no overwrite or second wheel under existing version. Use existing protected publishing workflow, not new paid services.

## Negative acceptance
- Same version after adding tool, plugin, command, API, source fix or installer step -> CI FAIL.
- pyproject 0.1.4 but server/init/glama still 0.1.3 -> FAIL.
- Document-only handover/Failure Museum change -> no new binary version required.
- Concurrent PRs choose 0.1.5 -> second cannot merge without reallocation, fresh CI and review.
- CI green but old wheel not independently restorable / live host source unknown / no original-client ACK -> stage WAIT, not claim active.
- Ed25519 synthetic A7 lab 6/6 PASS -> does NOT qualify A7 real updater/tunnel cut.
- Historical 0.1.3 tag and installed 0.1.3 source differ by 280 commits; do not select wheel by version string.
- Two builds same old source have identical 91 unpacked file hashes but different overall wheel SHA; preserve exact selected artifact hash, never overwrite under version alone.

Owner boundaries: PR #661 source version gate, #341 first-node recovery, #590 real client route, AIfordable #428 host attestation, Fabric A6 #942/#1039, Fabric A7 #943, Claude #381/Q7 independent. Do not restart shared GitHub runners, touch protected Bewind data/disks, or activate a server update from this task.
