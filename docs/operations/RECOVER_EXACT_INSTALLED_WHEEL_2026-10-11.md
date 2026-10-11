# Exact installed-source recovery wheel — operator plan (2026-10-11)

Status: SOURCE_PROVENANCE_CONFIRMED / WHEEL_NOT_BUILT / RESTORE_NOT_TESTED. Scope: Runner-MCP issue #341, not Fabric A7 unattended auto-rollback or an authorization to deploy. This public document deliberately includes NO real host/address/private path/SSH user/credentials.

## Critical provenance trap (verified GitHub objects)

| Object | Immutable commit | Meaning |
|---|---|---|
| Official GitHub release tag v0.1.3 | `0aa013c279128e22fbd53be32c35bced3ae26834` | Published wheel corresponds to this older release lineage |
| Actual MCP server's product state | `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a` | Operator-console-verified installed source commit |
| Repository main at checkpoint | `2d025ce72443853795aa87b4ec96b83a25064634` | Potential future target, NOT installed |

Verified `compare_commits(v0.1.3 tag commit, installed-state commit)` = `ahead_by=280`, `behind_by=0`, `files changed=130`. Although pyproject labels BOTH code generations version 0.1.3, the official downloadable `aifordable_runner_mcp-0.1.3-py3-none-any.whl` is NOT a verified exact-runtime recovery baseline. **DO NOT substitute release version equality for exact commit/artifact equality.**

An Actions **push** run on the exact historical installed commit exists: GitHub `Runner MCP validation` run `37668416668` completed SUCCESS 2026-10-07, `Commit attribution policy` run `37668416657` completed SUCCESS. Both workflows returned zero retained downloadable artifacts on 2026-10-11. Historical source CI success is NOT a preserved old wheel or recoverable standalone binary.

## Proposed recovery artifact construction — not executed

1. Qualify a truly disposable isolated build worker running the same supported Python/ABI and build backend as the actual installed host; prohibit access to host secrets, user application files, network tokens, protected disks and unknown shared volumes. Capture independent executor identity and approval.
2. From first-party verified GitHub source, fetch exactly commit `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`, verify clean tree, exact SHA, tree provenance and build inputs. NEVER fetch the symbolic `v0.1.3` tag or a branch in place of the immutable installed source SHA.
3. Build an offline wheel with fixed locally available build dependencies into a NEW isolated staging directory, e.g. after reviewing build scripts run `python3.12 -m pip wheel --no-deps --no-build-isolation --no-index --wheel-dir <isolated_stage> .` inside the disposable checkout. **This command is a plan, not an executed step.** Source build may execute backend code; qualify builder first.
4. Capture wheel file SHA-256, size, filename, Python ABI, exact source commit/tree, tooling versions, immutable receipt, and signer/approval provenance. Verify archive content/wheel metadata does not falsely imply it was the already-installed binary. Never put private key, actual host IP/path or customer data into GitHub.
5. Independently attest installed server process Python executable, package import path, actual installed distribution files/module hashes, and source checkout revision, using a trusted host-local read-only collector, so the reconstructed wheel may be compared against **what is actually running** (a state JSON is not byte-for-byte attestation). Version label, PID ownership or a successful live `build_identity` alone are insufficient.
6. Move the verified artifact to independently approved immutable off-target storage; do NOT reuse the shared Bewind archives or assume a planned 8 TB disk is authorized. Verify receipt from a second independent reader and preserve old artifact before touching a server.
7. Practice INSTALL+RESTORE of that exact wheel in a separate disposable environment and test original runtime/protocol/old client surface without mutating production. A synthetic wheel test is not by itself a crash/reboot/total-network-loss recovery test.
8. Only after a separately approved live-host attended update/recovery plan, scoped stop/abort window, independent console access and authenticated original-client response/ACK, consider one-node deployment. Unattended fleet A7 requires additional independent actuator and offline failback proof. Unknown effect -> STOP/RECONCILE, never auto-retry.

## Negative acceptance cases

- A wheel exists under release v0.1.3 but its source SHA is the v0.1.3 tag, not the running code -> FAIL.
- Correct source commit but missing artifact digest or unverified build environment -> WAIT.
- Active process module hashes unqualified or differ from rebuilt wheel -> WAIT/REVIEW; do not call it byte-identical.
- CI green but no externally retained binary/restore test -> WAIT.
- Staging directory has zero wheels and install transaction is clear -> NOT RECOVERY_READY.
- Known SSH port but not proven independent authenticated out-of-band recovery -> WAIT.
- A7 lab source/synthetic tests green -> does NOT authorize live unattended service update.

## Related durable records

- `handover/checkpoints/2026-10-11-341-live-runtime.md` and `roadmap/children/341-live-runtime-recovery/{TASK,STATE}.md`
- Failure Museum RMCP-F-0032 (no verified recovery escrow) and RMCP-F-0034 (v0.1.3 version collision).
- #341 owner for attended update, #590 client return path, AIfordable #428 runtime host attestation, Fabric #943 A7 lab, PR #659 docs-only.

NO host update/restart, package build/installation or physical-media copy was performed by this documentation step.
