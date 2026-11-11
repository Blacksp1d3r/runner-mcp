# Failure Museum — F30 unsigned lab / signed custody destination alias (2026-10-21)

## Trigger
Post-merge source inspection of Runner-MCP #789 (v0.1.70) showed the new optional keyless Q7 disposable lab importer reused the exact same private `bundle` destination as the original signer-controlled importer. Its result was labeled unsigned and had no installation authority, but identical final storage names could cause an unsigned test bundle to be mistaken for or block later signing-qualified release custody.

## Scope / impact
Detected in source only. No physical Black zipapp import, installation, process change, Agent Bus execution or six-role cutover was made. The previous signed private-custody function and source tests were otherwise passing. Trust is not created by download SHA-256 values from the same Release API.

## Root cause
Reusing the entire stage callback conflated two different trust classes at the fixed final filesystem leaf. Message-level taint is insufficient when a later consumer reads bytes from a shared path.

## Fix
Source follow-up v0.1.71 provides fixed `lab-unsigned-bundle` and `.q7-lab-unsigned-inflight` names and a separate lab wrapper reusing the same nofollow, owner-only, lock, fsync, digest, wheelhouse and no-overwrite code. Normal signed custody retains `bundle`, `.q7-bundle-inflight`, and the original public receipt schema. No arbitrary destination capability or production install permission is added.

## Regression acceptance
1. Keyless lab import succeeds only into unsigned lab leaf, never signed `bundle`.
2. Signed and lab stores coexist, no cross-overwrite; both replay attempts fail closed.
3. Interrupted lab writes preserve the prior signed bundle and the partial in-flight evidence.
4. The original signed path, exact-head lint/pytest/build/Ubuntu/demo/attribution tests remain green.

## Operational status
Fix is SOURCE ONLY; the physical Black 33/33 import and original-client ACK remain WAIT. A6 physically independent journal/readback and A7 offline six-role recovery remain separate unproven gates.
