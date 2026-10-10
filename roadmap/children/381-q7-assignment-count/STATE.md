# #381 — Q7 exact assignment count

- state: COMPLETE_SOURCE_ONLY; LIVE_ACCEPTANCE_BLOCKED
- branch: safety/381-q7-exact-assignment-count
- PR: #647 MERGED
- tests: exact head ea6e27bb1b3dcfe256b561ff8955bf31c0cdd768; attribution 38073911858 and 38074186402 SUCCESS; full validation 38073911864 SUCCESS (Ruff, 2772 pytest, artifact and clean demo)
- runtime/live qualification: BLOCKED_EXTERNAL
- Fabric authority: BLOCKED_EXTERNAL #1398/#1400
- actual Q7 worker: BLOCKED_EXTERNAL #972/#370
- Claude dispatch: NO_DISPATCH

- squash_merge: d078781d28f98398359e4db163dd8c248a77264d

## Evidence
Pure exact JSON-type check; numeric equality in Python otherwise conflates boolean with integer. No local/remote system action.
