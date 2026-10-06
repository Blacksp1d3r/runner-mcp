# Runner MCP — Resume Prompt

Use this prompt when starting a new chat:

> Continue Runner-MCP / Runner Fabric / AIfordable from the 2026-10-06 Claude/Q7 checkpoint. Reconcile GitHub first; current GitHub state wins over stale handoff text. Read Runner-MCP AGENTS/roadmap/CURRENT_STATE/NEXT_ACTION, Runner Fabric CURRENT_STATE/SESSION_HANDOFF plus CHAT_CHECKPOINT_2026-10-06_CLAUDE_Q7.md, and AIfordable AF22_6B_CLAUDE_PRO_WORKER.md/CURRENT_STATE.
>
> Checkpoint heads: Runner-MCP 92b11d8619d96a53939959b787143060e26fdc7d (#437 merged), Runner Fabric 4ba216be24444f1fa34fc2dc0f54d6907181ecd0 (#1060 merged), AIfordable bfc5c3313a2d3fe2552ff95ea19f1415e4c1f5a9 at checkpoint.
>
> Claude/Q7 software chain is complete: AIfordable #400 -> Runner Fabric #1060 -> Runner-MCP #437. New bounded tool: fabric_coding_availability_qualify(case, expected_revision). The prior chat had a stale connector catalog and could not yet see it. First action in a fresh chat: verify the tool is visible; if visible, run the three fixed synthetic Q7 cases with the exact current AIfordable revision and record results in Runner Fabric #972 and AIfordable #333/#262.
>
> Do not redo already-green Claude work: dedicated aifordable-coder identity, Claude Code 2.1.289 subscription baseline, Q2/Q3, edit->proposal->registration proof, AIfordable #287, Fabric #815, AIfordable #400, Fabric #1060, Runner-MCP #437.
>
> Separate live gates: Runner-MCP #381 remains design-only because generic cross-user systemd control would widen authority; AIfordable #370 still needs one host-local start->health->stop->disable service proof. Runner-MCP #417 still blocks Runner-Fabric source/Actions read. Runner-MCP #333 still needs real topology authority/READY/not_unique proof. Fabric A6/#942 remains blocked by stale managed Fabric runtime plus #417/local-custody absence.
>
> Preserve fail-closed authority and the no-new-variable-cost policy. Do not use generic shell/Desktop Commander as a shortcut around blocked first-party paths.
