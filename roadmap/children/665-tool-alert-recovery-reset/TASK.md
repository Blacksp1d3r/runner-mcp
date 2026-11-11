# #665 — reset a mismatch-alert cooldown after a recovery transition

Existing source-only `summarize_tool_mismatch_alerts` groups bounded mismatch events by opaque trusted scope digest, stable tool ID and typed reason. When an independently authenticated observer later reports READY, the old mismatch episode must end. A renewed mismatch immediately afterward is a **new** episode and must not be silently suppressed by a previous cooldown.

Bounded changes: on syntactically valid READY, clear only matching scope+tool cooldown slots, across all previous reasons. Preserve unrelated scope/tool cooldowns, nondecreasing timestamps, input bound, typed result, sanitization and existing function/API. READY itself never generates an alarm and does NOT authorize dispatch or establish independent authentication.

Acceptance: synthetic A→READY→A emits twice; two mismatch categories reset; other scope/tool suppressed independently; standalone READY no alarm; baseline regressions remain. No live notification service or worker, no network, no host change; Fabric #1471 remains owner of durable alerts/ACK, Runner-MCP #669 independent serving identity and #664 compatibility gates still separate.
