# #739 — fixed Release asset bytes source candidate 0.1.43

User-authorized continuation of dependent #745 now that #743 v0.1.42 is merged to main at `02970477d35b37c38fe67a4a645f2ad5c0ea7a11`. Source-only helper + offline tests; no actual download, credential or physical host operation, no immutable custody/rollback/ACK. Unique candidate 0.1.43; exact-head CI and guarded source merge required. Later draft #750 remains v0.1.44 and draft #753 v0.1.45. Parent importer #739 remains OPEN until approved original-host end-to-end trust and storage proof.

2026-10-19 follow-up: GitHub re-targeted dependent source PR from parent feature branch to main after #743 merged. Commit-attribution re-ran, but exact-head validation and Ubuntu install were not scheduled by base edit alone. This scoped handover update intentionally triggers a fresh synchronize event to qualify the new `main`-based 0.1.43 candidate. Do not infer prior green stacked CI from new base.
