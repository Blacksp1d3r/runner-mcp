# Runner-MCP #341 — existing provisional activation rollback custody

## Existing defect and scope
`SelfUpdateManager._run_job` cleared its existing install transaction and deleted the baseline wheel *immediately after installing/verifying the next wheel and writing restart markers*. This occurs before any restarted original client/Fabric result/ACK and leaves no same-manager rollback artifact if that process fails to reappear. Keep the old machinery; no second updater, watchdog, relay or observer.

## Narrow candidate v0.1.96
- Add a **strict, opt-in** `retain_activation_baseline: bool = False` constructor option to the existing manager. Do not automatically enable it on any serving host.
- Refuse opt-in first installs without a recorded baseline before any job is queued.
- On successful target wheel install, preserve the original private transaction, baseline/target wheel files, and restart intent instead of prematurely clearing the recovery state.
- Explicit read-only `provisional_activation_pending` status: a matching completed job + retained transaction while opted-in, not an ACK or a good deployment.
- Future updates remain blocked by existing `install_recovery_pending`. Existing attended emergency-stop `recover_installation` can restore the previous wheel after restart intent resolves.
- No commit/disarm endpoint or remote clearance authority is created. Fabric #943 owns physical on-boot local actuator / commit-confirmation, Fabric #942 off-target journal. No live deployment permitted based on this source feature.

## Acceptance
Exact HEAD release-reservation, Ruff, full pytest including positive and negative successful-install retention/restart/crash-recovery, wheel artifact, clean Ubuntu installation and attribution. Confirm legacy behavior is unchanged when not opted-in; existing packet identities, signed serving witness #669, original A6/A7 and same-campaign ACK remain separate WAIT.
