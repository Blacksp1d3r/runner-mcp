# Runner-MCP diagnostic architecture

Runner-MCP follows the AIfordable cross-project diagnostic-topology standard in `Blacksp1d3r/AIfordable#485`.

The purpose is to diagnose a bounded tool or operational symptom without relying on chat memory and without exposing private deployment details.

## Hierarchy

```text
Runner-MCP
  -> component
     -> ROADMAP.md
     -> SOURCES.md
     -> DATA_LINEAGE.md
     -> FAILURES.md
  -> FIELD_LINEAGE.md
  -> IMPLEMENTATION_MAP.md
  -> TEST_EVIDENCE_MAP.md
  -> FAILURE_INDEX.md
  -> topology/
     -> SYSTEM_TOPOLOGY.md
     -> DATA_STORE_MAP.md
     -> TRACEABILITY_RULES.md
     -> FAILURE_TAXONOMY.md
```

## Diagnostic order

1. identify the public/bounded tool or visible operational symptom;
2. resolve the owning component/subcomponent;
3. trace semantic inputs to trusted local/private state;
4. verify policy/authorization and revision binding;
5. verify an external/peer edge only when the lineage crosses it;
6. verify physical persistence only after the logical state is proven;
7. identify the earliest expected/observed divergence;
8. register a reusable failure with regression evidence.

This public repository never records real hostnames, private paths, ports, tokens, credentials or customer payloads. Infrastructure and credential identity remain owned by the canonical AIfordable/Runner-Fabric authorities.

Existing `.github/ISSUE_TEMPLATE/failure-record.md` remains the detailed incident/failure template. Existing `docs/SAFE_DIAGNOSTICS.md` remains the runtime-safe diagnostic output contract.

## Connector failure guidance

When tools are visible but every read-only call returns an unstructured internal error, use `CONNECTOR_READONLY_TRIAGE.md` and canonical RMCP-MCP-0005/#590. Do not infer runtime health or execute ad-hoc shell commands. The read-only triage must distinguish client schema, invocation transport, server dispatch and application response before any operational recovery.
