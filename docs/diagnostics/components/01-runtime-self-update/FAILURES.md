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

## 2026-10-20 — RMCP-F-0054 (source-only installed RECORD parser negative admission)

The existing offline installed RECORD comparator accepted *any* pip RECORD entry not present in the source wheel unless its path began `runner_mcp/`. That silently tolerated arbitrary exterior paths and duplicate console entries as if they were normal installer metadata. The source-MERGED v0.1.50 correction admits only known bounded pip console scripts and common installer metadata, validates optional external digest/size shape and refuses duplicates with synthetic negative tests. No evidence of real host exploit, no installed-process proof, no live updater/host action, and no change to A6/A7/ACK gates. Tracking #669.

## 2026-10-20 — RMCP-F-0055 (offline evidence path redirection)

The offline evidence chain previously delegated each input to separate helpers and used lexical `Path.is_relative_to()` for generation membership. Source-only negative review exposed that lexical `..` or linked ancestors can reference a different physical path while looking generation-relative. Source-MERGED v0.1.51 refuses nonabsolute inputs, lexical parent traversal and symlinked ancestors for every path, with parametrized synthetic tests. No proof of a live incident; even successful offline chain remains `active_build_provenance_verified=false`, never independently signed correct-host process trust. Tracking #669.
