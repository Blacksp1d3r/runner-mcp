# Runner-MCP release and version integrity (pending v0.1.4 source policy)

## Binding product rule
Every production-capable source change, new MCP tool, schema/interface modification, installer/script change or CI release workflow change MUST increment the numeric release version. The same unique version must appear in `pyproject.toml`, `server.json.version`, each `server.json.packages[].version`, `src/runner_mcp/__init__.py::__version__` and `glama.json.version`. No "we added tools but still report 0.1.3" is acceptable; a new release requires a new version and exact immutable source digest.

A shipping PR with no version increase FAILS CI. Every bump must update all four primary version-bearing files, not only two. A patch fix normally increments PATCH; a backward compatible tool/feature normally increments MINOR; an incompatible interface increments MAJOR. Colliding independently developed PRs must serialize or rebase their proposed version against the latest `main` before merge, run fresh exact-head CI and receive independent review. No force merge on stale green results. The first proposed source candidate following legacy 0.1.3 is 0.1.4, but this is NOT a published GitHub/PyPI release and NOT a runtime update until separately deployed and acknowledged.

Documentation/tests/handover-only changes do not alter the executable or tool catalogue and do not require a new binary version. If a changed file is in `src/runner_mcp/`, `scripts/`, `install.sh`, `pyproject.toml`, `server.json` or `.github/workflows/`, the gate requires strictly increasing metadata. Do not hide new tools outside checked paths; code review checks tree and exposed MCP catalogue.

## Apply as soon as eligible, without sacrificing recovery
After reviewed merge, the first-party CI must build the exact immutable source commit, run comprehensive tests, produce artifact SHA256, record release journal and stage an available update candidate automatically. Once the independent attended A6 journal and A7 rollback/ACK route are qualified, fleet controller should update by safe per-node strategy, retain previous signed recovery artifact independently, confirm server's exact `build_identity`/loaded module/catalogue and receive same original-client result+ACK before promoting another node.

**No production deploy is implied just by changing a version file or merging a PR.** Until A6/A7 are qualified, automatically staging is allowed but activation is WAIT. Never set the ACTIVE installed version or claim an update took effect before runtime/ACK proof. Avoid continuous polling AI: the future controller should schedule/process CI/event-triggered promotion, record state and alert only upon actionable denial.

## Continuous monitoring invariants
1. Source version vs registry versions: equality (build-time CI).
2. Proposed version strictly greater than merge-base when shipping source changes (PR CI).
3. Immutable source SHA, independently hashed wheel digest and proposed version travel together in manifest (build pipeline).
4. Active server version/source/digest, tool catalogue and original-client route are measured from actual serving process (runtime attestation).
5. Actual release is acknowledged only after stable post-deploy health, result+ACK and offline-capable rollback escrow (fleet admission). No invented success for missing ACK.
6. Never reuse a release version for a different wheel or source SHA. If a version exists in published registry from another SHA, choose next available version.
7. If any gate is absent: publish WAIT reason to the appropriate child, do not silently run old code or pretend a new version is installed.

## Ownership
- Runner-MCP release metadata and source CI version guard: this bounded policy PR.
- Runner-MCP #341 attended first-node release, independent wheel.
- Fabric A6 #942/#1039 journal and correlation; Fabric A7 #943 autonomous rollback and authenticated ACK; Runner-MCP #590 same original-client route; AIfordable #428 authenticated host/runtime identity.
- This policy PR does NOT claim ownership of fleet rollout or Claude #381 runtime dispatch and cannot bypass other workers' leases.

## Regression record
Previous state: code and tool capabilities advanced 280+ commits while live and official public binary both displayed version `0.1.3` despite diverging release generations. Observed installed commit `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`, official public `v0.1.3` tag `0aa013c279128e22fbd53be32c35bced3ae26834`. Error mode: version text cannot identify actual code/artifact. Fix: unique numeric source version bump policy plus mandatory immutable SHA/digest and real server/ACK witness. No fleet update in this documentation change.
