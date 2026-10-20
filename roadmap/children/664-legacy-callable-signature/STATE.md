# #664 legacy callable signature regression — STATE

- COMPLETE_TEST_GUARD_ONLY (historical customer wheel schema not qualified)
- Branch chatgpt/664-legacy-signature-regression-v0124, base main 53a002df136d010ebe460643a37ddcf86af58c6e.
- Test and pinned fixture only, no version bump or runtime change; source remains 0.1.23.
- Pending exact-head PR CI; if failing, fix and register real issue in Failure Museum, then mark COMPLETE_TEST_GUARD_ONLY.
- Parent #664 stays open for customer compatibility qualification on actual released wheels and operator-defined support policy.

- 2026-10-16: PR #702 source test-only merged squash `aa1a80656a04c3b1d278228e20ea129988e622d0` from exact CI-qualified head `92d0e9ce8a423f87b61fb579d4545429c1288f59`. Runner validation `38902202349` rerun final attempt: Ruff/pytest, build and clean demo SUCCESS; attribution `38902202402` SUCCESS. Test mutation targeting RMCP-F-0040 fixed. A separate pre-existing timing-dependent round-robin scheduling assertion failed once during first run, rerun passed without source scheduler changes; do not assert root cause or production defect proven. No Ubuntu installer run was observed for tests-only PR.
