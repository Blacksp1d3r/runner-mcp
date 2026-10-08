# 06-qualification-bootstrap — Worker qualification, disposable target en bootstrap — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0002 | KNOWN | qualification/private binding | Qualification agent can restart successfully while A6/qualification capability remains unavailable | required private qualification bindings or peer tool registration can be absent/stale independently of agent process health | sanitized state/binding preflight + peer interface preflight before qualification; fail closed on partial binding state | Fleet A6 historical #509 |

Project-specific qualification failures should additionally link their project issue, artifact hash/revision evidence and cleanup result without copying sensitive paths.
