# #333 opt-in tunnel doctor — STATE

- SOURCE_IN_PROGRESS / WAITING_CI; branch `chatgpt/333-explicit-tunnel-doctor-evidence-v0124`.
- Base main `1a3157397be97567a37156ab00afa0c76776cb88`, source v0.1.23. Current candidate 0.1.24.
- Pure evidence projector + actual doctor opt-in injection + synthetic negatives implemented. New args default unchanged for old clients.
- No private tunnel state accessed, process restart/host/tunnel/secret/config mutation or live rollout.
- Next: PR exact-head CI, failure museum if needed, merge and GitHub handover.
