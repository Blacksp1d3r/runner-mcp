# 01-runtime-self-update — Runtime en self-update — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| none-migrated | — | — | No additional component-specific reusable failure migrated yet | — | use global taxonomy/template | #569 |

Use the existing repository failure-record template for detailed incidents. Add stable IDs here only for reusable root causes.

## 2026-10-19 — RMCP-F-0045 (source-only, not a live incident)

At the active-revision provider boundary, missing mapping entries or object
attributes could raise `KeyError`, `IndexError` or `AttributeError`, bypassing
the previous bounded exception list and surfacing a generic internal tool error.
PR #742 contains a narrow `LookupError`/`AttributeError` containment fix and
regressions requiring unknown revision, false activation/readiness, a denied
update and no private exception text. No evidence of this path occurring on a
live host; exact-head CI must pass before source acceptance. The separately
missing serving-generation attestation is still UNKNOWN and is not repaired
by this exception-containment change.

Design: [SERVING_GENERATION_ATTESTATION.md](SERVING_GENERATION_ATTESTATION.md).

## 2026-10-19 — RMCP-F-0046 (synthetic source boundary, no live incident)

Source checkout baseline evaluation previously expected a valid `clean_head` dict and coerced unknown commit values to string. A malformed provider result could escape status/Doctor or produce a noncanonical source revision. The #742 source fix strictly checks dict, `clean is True`, and lowercase 40-character commit, or returns `(None, False)` without exposing private exception detail. Tests cover ten malformed forms plus a provider error and assert no updater job is queued. This does NOT reconcile the real manual installation or alter historical state. Exact-head CI pending.
