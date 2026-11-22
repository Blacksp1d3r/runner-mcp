# Dekkingscontrole compacte AGENTS.md — runner-mcp (2026-11-15)

- Origineel: `docs/agents/AGENTS_FULL_2026-11-15.md`, byte-identiek aan `AGENTS.md` op main vóór activering, SHA-256 `0d35aa6b52522397bb1a5d676099d461b15ab597d710c918c4dbb91114521e33` (bewaakt via `frozen_files` in `tools/doc_memory/budget.json`).
- Omvang: 27,545 → 18,904 tekens.
- Letterlijk overgenomen: alle sections die als *hard rule* of *non-negotiable* zijn gemarkeerd (zie tabel).
- Mechanische controle: elke normatieve zin uit het origineel (must/never/only/nooit/geen/verplicht/...) is letterlijk overgenomen of zijn kernbegrippen (backtick-termen, issuenummers, statuscodes) staan in de compacte tekst. Wat overblijft zijn nadrukwoorden of detailverwijzingen (bv. `FIELD_LINEAGE.md`), die in de naslag staan en via §7 met een leestrigger bereikbaar zijn.

## Bewuste wijzigingen (eigenaarsbesluit 2026-11-15)

1. Checkpoints worden niet meer telkens toegevoegd: `CURRENT_STATE` wordt bijgewerkt, `SESSION_HANDOFF` bevat alleen de recentste overdracht (§5). Dit vervangt de oudere bootstrap-/handoffregel.
2. Library-protocol: actueel is v1.7 (31 oktober 2026); oudere vermeldingen in de naslag zijn historisch.
3. Bij schijnbare tegenstrijdigheid tussen compacte tekst en naslag geldt de strengere regel.

## Tegenstrijdigheden gevonden en opgelost

- Runner-MCP noemde v1.7, v1.6 én v1.2 als actueel → overal v1.7.
- Oude regel "newest-first checkpoint toevoegen" botst met het nieuwe geheugenbeleid → expliciet vervangen (§5).

## Waar staat elke oorspronkelijke sectie

| Oorspronkelijke sectie | Plaats in compacte AGENTS.md |
|---|---|
| Algemene eigenaarsregel — leesbare code en veilige serveropschoning (2026-11-01) | §3 (2026-11-01) + §2 Serveropschoning |
| Eigenaarsregel — directe operatoruitvoering bij technische toolblokkade (2026-10-31) | §2 Toolblokkade |
| Alle projectchats — onmiddellijk origineel toolblokkadebewijs vastleggen (2026-10-31) | §2 Toolblokkade (TOOL_BLOCK_V1-velden, IN_CHAT_ONLY, #1935); v1.6 → v1.7 |
| Verplichte uitvoeringsvolgorde — bewijs → tooltest → uitvoeren (27 oktober 2026) | §3 (2026-10-27), samengevoegd |
| Evidence-first diagnostics: session startup and reuse | §3 (2026-10-27), samengevoegd |
| Mandatory physical topology + exact serving-runtime preflight (owner decision 2026-10-22) | §2 Exacte doelserver |
| Owner-confirmed MCP scope in integrated cockpit (2026-10-20) | §3 (2026-10-20) |
| Operator control route — 2026-10-17 | §2 Bedieningsroute |
| Owner decision — test-first development; review later (2026-10-14) | §2 + §3 (2026-10-14) |
| Mission | §7 naslag |
| Canonical cross-project standards | §2 (Library verleent geen bevoegdheden) + §5 (children, TASK/STATE) + §7; v1.2 → v1.7 |
| Non-negotiable security rules | §1 letterlijk |
| First-party control path — hard rule | §2a letterlijk |
| Zero incremental software-cost rule | §2 |
| External discovery and independence — hard rule | §2b letterlijk |
| Public examples | §1a letterlijk |
| Epic decomposition and bounded-child rule | §5 + §7 |
| Git workflow | §5 |
| CI safety | §1a letterlijk |
| Mandatory session bootstrap and handoff | §4 + §5 |
| Diagnostic topology — mandatory troubleshooting rule | §5 Troubleshooting + Agents en claims + §7 |
| Multi-agent availability and task takeover | §5 Agents en claims + §7 |
| AI source-control identity — hard rule | §2c letterlijk |
