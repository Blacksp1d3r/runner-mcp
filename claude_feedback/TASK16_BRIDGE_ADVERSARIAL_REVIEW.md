# Task 16 — adversarial bridge/protocol regression review

Status: review complete; no production code changed in this task.

## Conclusion

The protocol-v1 request parser and mailbox boundary are strongly fail-closed for the reviewed capability-expansion classes. I did not find a demonstrated route from malformed JSON, unknown fields, case/abbreviation variants, duplicate keys, identifier mismatch or extra action arguments to an unintended executor capability.

One concrete regression-test gap remains: several of those invariants are implemented but not pinned together in an explicit adversarial matrix. This review recommends tests, not a runtime redesign.

## Adversarial matrix

- Unknown actions: BridgeAction enum plus strict Pydantic model; covered.
- Case/abbreviation variants such as uppercase, hyphenated or prefixes: exact StrEnum values and no normalization; add explicit parameterized rejection.
- Unknown arguments such as command/cwd/env: extra=forbid; command is covered, add representative cwd/env.
- Duplicate action/request ID: strict duplicate-key JSON hook; duplicate action covered, add duplicate request_id.
- Non-standard request JSON constants: parse_constant rejects them; result side is covered, add request-side proof.
- Request ID / mailbox filename mismatch: validated and compared; covered.
- Action/argument mismatch and argument smuggling: per-action field ownership rejects non-owned fields; representative coverage exists, add exhaustive cross-product.
- Self-update uppercase commit: generic commit accepts hex case but self_update additionally requires lowercase; add explicit regression proof.
- Result leakage, oversized/deep results, compare-path smuggling and replay mutation are already bounded and covered.

## Demonstrated implementation properties

BridgeRequest.action is typed as BridgeAction. JSON action values must equal an enum value exactly. There is no lowercase conversion, prefix matching, alias lookup or fuzzy dispatch. bridge_tool_call() switches on that enum and returns only fixed tool names.

BridgeRequest uses ConfigDict(extra="forbid", frozen=True). A globally valid protocol field that is not owned by the selected action is also rejected by the action validator instead of being ignored. This is the critical defense against argument smuggling.

_decode_json_payload() installs _reject_duplicate_keys as object_pairs_hook, so first-wins/last-wins parser differentials for action, request_id or arguments are rejected before model validation.

The mailbox validates the filename request ID and fetch_request() compares the parsed payload request_id with it. Replay processing separately refuses changed content under an already-claimed request ID.

Protocol and transport failures use bounded descriptions rather than raw validation/response bodies. Executor failures are converted to bounded codes/summaries.

## Test gap worth fixing

A bounded CODE test task should:

1. for every BridgeAction, construct one known-valid minimal payload;
2. enumerate every optional protocol field not owned by that action;
3. inject a syntactically valid value and assert strict rejection;
4. assert action case/prefix/hyphen variants are rejected;
5. assert duplicate request_id is rejected;
6. assert uppercase self_update commit is rejected;
7. assert request-side NaN/Infinity constants are rejected;
8. keep executor invocation counters at zero for every rejected payload.

This is test hardening only. No demonstrated runtime defect justifies changing protocol code from this review.

## Smallest boundary

Add the adversarial matrix to tests/unit/test_bridge_protocol.py, with at most one mailbox identity-binding regression in tests/unit/test_github_mailbox.py if needed for coverage clarity.

Do not alter the action enum, add aliases, normalize action strings, broaden identifier regexes, change replay state, or add new bridge capabilities in this task.
