# #333 opt-in tunnel doctor — STATE

- COMPLETE_SOURCE_ONLY (live tunnel evidence collector/operator wiring not yet qualified); branch `chatgpt/333-explicit-tunnel-doctor-evidence-v0124`.
- Base main `1a3157397be97567a37156ab00afa0c76776cb88`, source v0.1.23. Current candidate 0.1.24.
- Pure evidence projector + actual doctor opt-in injection + synthetic negatives implemented. New args default unchanged for old clients.
- No private tunnel state accessed, process restart/host/tunnel/secret/config mutation or live rollout.
- Next: PR exact-head CI, failure museum if needed, merge and GitHub handover.

- 2026-10-16: [PR #703](https://github.com/Blacksp1d3r/runner-mcp/pull/703) merged `d3929bbcdcf0d7fd547740ed80a2e4195b89dd36` from exact tested source head `dbb1143f7f9eff82bf676b9eaa94929f1ff2766c`. CI validation `38903795857` Ruff/pytest, built release and clean demo, Ubuntu `38903796065`, attribution `38903795921` all SUCCESS. Runtime remains 0.1.9; no private tunnel sensor or reboot manager enrolled.
