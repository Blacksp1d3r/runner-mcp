# ADR-2026-10-12 — Universal Runner-MCP toolset, configurable activation

**Status:** ACCEPTED by operator, 2026-10-12  
**Scope:** Runner-MCP installed package and tool registry on every managed host; Runner Fabric capability admission remains separate  
**Related:** Runner-MCP #662 (versioned release conveyor), #590 (original-client catalogue), #341 (first-node recovery), PR #661 (95-tool source baseline), Fabric A6 #942 / A7 #943

## Decision

All managed Runner-MCP hosts install the **same canonical, reviewed Runner-MCP release artifact**, with the **same package version, immutable source revision, artifact checksum and COMPLETE compiled tool set**. The canonical repository remains `Blacksp1d3r/runner-mcp`. Project- or server-specific variants that delete tools, omit modules, edit tool definitions, repack the wheel or reuse one version for different package bytes are prohibited.

A tool's installation and source-defined registration are universal; its **effective enabled/exposed status and its actual execution authority** may vary through a separately authorized configuration/policy applied to a particular host, role, tenant or client. A capability should not be disabled merely because it is unused for one day, but may be disabled when unnecessary or unsafe for that deployment. It remains in the package and can be restored through a controlled policy change rather than rebuilding/releasing another binary.

Where practical, provide the complete bounded tool interface to qualified servers. The operator's preference for tool availability does **not** mean blanket privileges or consent to protected mutations. The existing deny-by-default execution rules remain authoritative:
- **Presence:** tool implementation shipped in the identical release wheel.
- **Registration:** source-defined tools included in the canonical versioned manifest.
- **Enablement/exposure:** deterministic per-host/client/role policy; disabled tools cannot be called or must refuse before side effects. Any policy-driven catalogue difference is explicitly reported, not mistaken for an old binary.
- **Authorization:** each actual operation still requires fixed allowlist, correct host, caller/tenant context, scope, required approvals/leases/fencing, provenance and safety checks. Updating a service, executing code, modifying a database, removing data or granting access is never authorized by having the tool installed or enabled.
- **Outcome:** operations return observable receipts; unavailable/denied states give a bounded reason and do not silently fall back to generic shell, privileged API, or another project.

Runner Fabric is the **sole control plane** for qualified capability/host/worker registration, admission, leases, scheduling and recovery. Runner-MCP is the host-local bounded execution and communication interface. There is no duplicate per-project MCP fork and no new unrestricted shell.

## Version and deployment invariants

1. Every source/tool/interface/security fix producing a different approved executable advances a unique numeric release version. Never call two different wheels the same released version.
2. Before rollout, publish the canonical **complete** tool inventory from both declaration forms (`@mcp.tool()` and `mcp.tool()(function)`) and check that exact immutable wheel content contains it. Current 0.1.4 source candidate has **95** static registrations; the historically serving a0fd... source has **87**; counts are evidence about SOURCE, not yet verified runtime behaviour.
3. Every host reports both `packageVersion/sourceCommit/artifactSha256` and `completeToolsetDigest`; report `effectiveEnabledSet/disabledSet` and bounded denial reasons **separately**, without leaking host secrets. Runtime/catalogue receipt comes from an authenticated serving process and original client, not just GitHub/manifest metadata.
4. Changes to enablement policy do **not** change the wheel or version. A policy change must carry its own policy version/digest and audit/approval when appropriate. Do not let an unauthenticated client or prompt change it.
5. One-node qualified update, independent prior artifact restore, A6 off-target journal, A7 real rollback and original-client result/ACK precede additional host rollout. No mass updater merely because source CI passes.
6. Servers without the dependency or hardware required for a tool retain its implementation and report `UNAVAILABLE/NOT_CONFIGURED` or disable the tool, without counterfeit success or new host-specific package.
7. Tool registration present in wheel, tool advertised by the connected client, tool actually enabled and tool callable under authorization are **four distinct measurements**. Never claim all tools operational from the static wheel count.

## Enforcement tasks and negative tests

- Build-time CI: one package/version and identical full source tool manifest for all targets; deny altered/partial wheels. Preserve artifact digests in off-target custody.
- Runtime: capability inventory endpoint or equivalent bounded projection emits canonical expected tool names/count, disabled/denied set and their policy version, and the actual serving build identity; no broad filesystem/process details.
- Security regression: disabled tool cannot produce side effects, including via alternate worker, adapter, queue or alias. Enabled tool without matching authorization is refused. Wrong host/tenant/role/caller or stale policy receipt fails closed.
- Fleet regression: two hosts on the same release have identical package/toolset digests even when their enabled subsets differ. Switching enablement does not rebuild/redeploy source.
- Drift regression: an old serving revision with stale tool catalogue cannot masquerade as the new release; original client ACK and advertised tool reconciliation are required.

**Implementation state:** ARCHITECTURAL DECISION ONLY. It does not claim feature flags, host policy enforcement or automatic fleet cutover are implemented today. Source PR #661 remains unmerged/unapproved until reviewed. Existing production remains unchanged. Child implementation belongs under a bounded tracked issue after source and lease reconciliation.
