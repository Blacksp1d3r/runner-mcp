# Runner-MCP fixed A6 local storage read bridge

Status: SOURCE_CANDIDATE_IN_CI / LIVE_FIXED_ROOTS_WAIT.
Branch: `feat/f30-a6-readonly-bridge-0.1.52`; candidate 0.1.54 source based on main 0.1.53.
Paired Fabric source `a6_storage_preflight()` merged #1618/#1626; does not mean serving original Fabric agent exposes it.
No new relay, credential, updater, storage manager, filesystem or host operation. Source implements only bounded zero-argument safe WAIT/local-hash claim, all physical independence/target-loss/write/dispatch flags false.
Tests/release reservation then guard merge. Separately coordinated original-client physical admission remains OFF.
