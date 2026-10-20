# 06-qualification-bootstrap — Worker qualification, disposable target en bootstrap — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0002 | KNOWN | qualification/private binding | Qualification agent can restart successfully while A6/qualification capability remains unavailable | required private qualification bindings or peer tool registration can be absent/stale independently of agent process health | sanitized state/binding preflight + peer interface preflight before qualification; fail closed on partial binding state | Fleet A6 historical #509 |
| RMCP-F-0044 | SOURCE_FIXED_NOT_INSTALLED / OWNER_SETUP_WAIT | Agent Bus first-host status/private-base admission | Partial private base caused generic RuntimeError, escaped original OnboardingError wrapper; original #737 CI was red despite 3324 passed | bounded ConfigManagerError for malformed/partial files, only truly absent 0700 owner-root reports NOT_INITIALIZED | fixed #737 head c620db7, full CI #39061856248/Ubuntu #39061856254/attribution #39061856279 SUCCESS, main d2dce33; physical Black ACK still WAIT | #735 / #737 / Fabric #1563 |

Project-specific qualification failures should additionally link their project issue, artifact hash/revision evidence and cleanup result without copying sensitive paths.
