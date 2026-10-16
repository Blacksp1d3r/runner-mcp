# #669 offline evidence chain — source state

- Status: CHATGPT_IN_PROGRESS / WAITING_CI
- Branch chatgpt/669-offline-evidence-chain-v0114 from verified source main c1407cc59be940451d4024b680ffa2c257ed1518.
- Source-only candidate 0.1.14; no release/activation or active provenance claimed.
- Tests cover positive untrusted offline consistency and negative changes.
- Next: exact-head CI, correct any errors, source merge only if permitted by real repository gates.
- Last observed original client Runner-MCP 0.1.9 with null active source/digest; A6/A7 authority unavailable.

- 2026-10-16: actual disconnected package vulnerability corrected (RMCP-F-0032); module directory must be a nonsymlink path under the matching generation. CI for latest source head after this fix remains pending, so source not yet merge-qualified.
