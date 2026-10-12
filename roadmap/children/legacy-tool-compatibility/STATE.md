# Older customer tool contract compatibility — STATE

2026-10-12: PROPOSED / DOCUMENTED ONLY. No implementation, compatibility tests, client rollout or support SLA approved.
Operator requires newer central services to communicate safely with customers on earlier Runner-MCP versions. Old tool public contracts remain stable; fixes may change implementation under new package version, breaking changes require v2 tool ID. A tool absent in older binary cannot be invoked until upgrade or independently qualified alternative.
Four separate identities: package/source/wheel; protocol epoch; tool contract schema/semantics; host/tenant activation policy. All must be attested/negotiated, not inferred from string version.
Parent universal-toolset ADR in docs PR #659; this proposed ADR at docs/architecture/ADR-2026-10-12-LEGACY-TOOL-CONTRACTS.md.
Next: independent ADR review, contract snapshot inventory, versioned CI comparator and Fabric negotiation tests; customer support calendar to be decided explicitly.
