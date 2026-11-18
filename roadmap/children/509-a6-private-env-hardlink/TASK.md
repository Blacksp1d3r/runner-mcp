# Runner-MCP #509 — fixed A6 private env inode alias guard

Owner: Runner-MCP #509. Source-only defensive child. No new MCP tool, relay, installer or host shell.

Existing `repair_a6_qualification_binding` and `inspect_a6_binding_state` must reject a second hard-link alias to the 0600, owner-private `runner-mcp.env` file before reading or merging the fixed eleven A6 bindings. Reuse the already-approved private file helper and fixed configuration location. Fail with the existing sanitized A6 config-unavailable category. Ensure a refusal does not update process environment or private config.

Acceptance: a normal single-link env retains 0/11 and repaired 11/11 behavior; synthetic double-linked private config fails closed for both inspection and repair; unrelated worker keys and fixed environment persist on normal authorized repair; tests and exact-head CI pass.

This local inode check alone does not eliminate filesystem races, prove A6 journal is physically off target, prove six serving-role wheel/source identity (#669), or authorize the live 0.1.38 upgrade. Fabric #1617/#942/#943/#924 and original-client ACK remain external admission gates.
