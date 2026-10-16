# #669 offline evidence chain — source state

- Status: COMPLETE_SOURCE_ONLY (no trusted build origin or loaded-process proof)
- Branch chatgpt/669-offline-evidence-chain-v0114 from verified source main c1407cc59be940451d4024b680ffa2c257ed1518.
- Source-only candidate 0.1.14; no release/activation or active provenance claimed.
- Tests cover positive untrusted offline consistency and negative changes.
- Next: exact-head CI, correct any errors, source merge only if permitted by real repository gates.
- Last observed original client Runner-MCP 0.1.9 with null active source/digest; A6/A7 authority unavailable.

- 2026-10-16: actual disconnected package vulnerability corrected (RMCP-F-0032); module directory must be a nonsymlink path under the matching generation. CI for latest source head after this fix remains pending, so source not yet merge-qualified.

- 2026-10-16 hardening: RMCP-F-0032 disconnected installed-package/generation relation fixed with symlink ancestry denial; RMCP-F-0033 group-writable artifact/module rejection added with tests. Earlier CI runs on prior commit do NOT validate this HEAD. Recheck terminal exact-head CI before merge.

- 2026-10-16: PR #692 merged `a7e3bb30d008d655ae5b8c5fdc15813303f84935` from exact source head `8e77d9796744a19c7ebcd6a2dfa759ed7248a3f5`. GitHub validation 38864199810, Ubuntu 38864199752, attribution 38864199758 all SUCCESS. RMCP-F-0032 and RMCP-F-0033 source fixes tested; no production activation.
