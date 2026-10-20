# #669 — deterministic Runner-MCP source release reservation / collision CI gate

**Status:** DESIGN / NOT IMPLEMENTED; reserved future source child, independent of live production update and worker workspace source PR owners. The existing release gate proves version monotonicity against one Git base, not cross-PR uniqueness or strict next-patch reservations.

**Problem:** main version 0.1.41 merged from #751 while concurrent #743 also records 0.1.41, stacked #745 is 0.1.42 and independent draft #750 is 0.1.43. Human comments alone will not prevent recurrence.

**Owner:** one Runner-MCP release steward, not Fabric nor AIfordable. **Prerequisite:** reconcile in-flight release lanes and reserve a unique version for this source-code gate, since editing `scripts/check_release_version.py` itself changes shipped code and triggers a version bump.

**Acceptance contract:**
- Cross-check latest main SHA/version, open shipping PR base/head/version and explicit declared dependency/stack order using independently authorized read-only GitHub API; no two merge-eligible PRs own the same release value.
- CAS/lease or GitHub-enforced serialization stops race between check and merge; test same-version/branch changed after check, unrelated merge, missing API, stale base, forced version jump, intentional major/minor override policy.
- Normal patch release must be the next eligible patch in dependency order; four version files and changelog equal; old exact-head CI invalidated on source changes.
- Must run on candidate's actual head and be made required in protected GitHub branch policy to enforce; otherwise mark advisory, not a guaranteed gate.
- Runnable offline unit tests for deterministic core, bounded API error classification; fail closed/WAIT when coverage incomplete. No added generic shell, credential, CI billing or host mutation.
- Record tests, Failure Museum defect and handover; no merging on historical green checks.

**Source precedence:** [Runner-MCP local contract](../../../docs/coordination/CONTROL_PLANE_SINGLE_FLOW.md), [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924), Runner-MCP #669.
