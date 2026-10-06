# Fabric worker qualification provisioning

Tracking: #445. Fabric authority: Blacksp1d3r/Runner-Fabric#1130.

Runner Fabric owns the enrollment/provisioning decision. Runner-MCP only performs
one fixed local provisioning action on the worker.

## Public MCP command

`fabric_worker_qualification_provision` accepts only:

- semantic worker ID;
- fixed capability profile;
- worker generation;
- enrollment plan SHA-256;
- policy expiry timestamp;
- exact managed Runner Fabric revision;
- request fingerprint.

The tool accepts no path, hostname, IP, endpoint, service, executable, argv,
environment map, Incus object name, token, password or key.

## Private worker authority

The worker operator supplies the host-owned environment value
`RUNNER_MCP_WORKER_QUALIFICATION_TEMPLATE_JSON`.

Its schema is:

```json
{
  "schemaVersion": "runner-mcp/worker-qualification-private/v1",
  "worker_id": "worker-example",
  "capability_profile": "bewind-ocr-qualification-v1",
  "generation": 1,
  "disposable_target": {
    "...": "the existing private Runner Fabric disposable-target qualification fields"
  }
}
```

Real private topology and Incus names remain local and must never be committed.

## Fencing

Before mutation Runner-MCP proves:

1. request fingerprint matches the Fabric request material;
2. policy expiry is still in the future;
3. worker ID/capability/generation match local private authority;
4. the managed `runner-fabric` launcher resolves into the exact requested
   control-plane update slot.

Only then is the existing disposable-target qualification configuration written
to the fixed private Runner-MCP configuration namespace and bound into the
private runtime environment.

The resulting state remains qualification-only:
`normalActivationEnabled=false`.

## Follow-up

After provisioning succeeds, Fabric may call the existing
`fabric_disposable_target_qualify` operation. That operation still performs the
real create/isolation/destroy/recreate/final-destroy proof and cleans the
disposable guest afterward.

This feature does not run Bewind OCR and does not start or stop the active
Bewind v3 backfill.
