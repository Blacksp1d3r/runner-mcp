# Runner MCP — Resume Prompt

Use this prompt when starting a new chat:

> Continue work on `Blacksp1d3r/runner-mcp`. Before material work, reconcile the latest GitHub state and read in this exact order: `AGENTS.md` -> `roadmap/ROADMAP.md` -> `roadmap/DEPENDENCIES.md` -> `handover/CURRENT_STATE.md` -> `handover/SESSION_HANDOFF.md` -> `handover/AGENT_EXCHANGE.md` -> `decisions/DECISIONS.md` -> then inspect current GitHub PRs/issues/CI. GitHub current state wins over stale handoff text. Continue from the current assignment and next safe steps; do not repeat already completed work. Feature/code work remains branch -> PR -> review/tests. Before ending the chat, update the handoff files when state materially changed and leave an explicit checkpoint.
