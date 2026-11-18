# A6 state-root symlink safety — current-main restack

Owner issue: Runner-MCP #509. Historic unmerged source: PR #655. Fleet A6 qualification: Runner-Fabric #942.

Problem: `Path.exists()` returns false for a dangling symlink; the prior `a6_state_requested` could misclassify a prepared but unsafe A6 root as an absent/no-op state. Symlink loops in the state-root ancestry could also raise an uncategorized runtime exception. This breaks fail-closed policy before A6 admission.

Solution: reuse the already implemented #655 bounded patch, verified byte-for-byte to differ from current main only in the intended 14 lines: reject symlinked fixed journal/evidence roots before existence testing; reject the input A6 parent symlink; sanitize `resolve()` errors; use one protected state-root normalizer across inspection and repair. Negative tests assert missing/dangling/symlink-cycle refusals and no private environment file mutation. Keep existing A6 repair behavior and exact private credential bounds unchanged.

Scope: `src/runner_mcp/fabric_a6_binding_repair.py`, existing A6 unit tests, official version metadata 0.1.27, TASK/STATE. No new updater, worker launch, keys, host process, route, local shell, data conversion or production activation. Historical #655 must not be merged in addition to this current-main restack.

Acceptance: exact-head GitHub validation, clean Ubuntu and attribution success, then source merge under repository rules. Real independent host/version attestation, A6 journal binding and A7 recovery stay unqualified separately. Recorded Failure Museum issue RMCP-F-0026; no fabricated physical exploit.
