#!/usr/bin/env bash
# Disposable GitHub-hosted runner ONLY. Never execute on serving hosts.
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != "true" || "${RUNNER_ENVIRONMENT:-}" != "github-hosted" ]]; then
  echo "STOP: requires a disposable GitHub-hosted Actions runner" >&2
  exit 1
fi
if [[ "$(id -u)" == 0 || "$(ps -p 1 -o comm=)" != "systemd" ]]; then
  echo "STOP: requires non-root user with systemd PID1" >&2
  exit 1
fi
uid="$(id -u)"
export XDG_RUNTIME_DIR="/run/user/$uid"
unit="runner-mcp-866-disposable-lifecycle.service"
unit_dir="$HOME/.config/systemd/user"
target="$unit_dir/$unit"
if [[ -e "$target" || -L "$target" ]]; then
  echo "STOP: test-owned unit already exists" >&2
  exit 1
fi
sudo systemctl start "user@${uid}.service"
for _ in {1..20}; do
  if systemctl --user show-environment >/dev/null 2>&1; then break; fi
  sleep 1
done
systemctl --user show-environment >/dev/null
mkdir -p "$unit_dir"
test_crontab_owned=false
cleanup() {
  if [[ "$test_crontab_owned" == true ]]; then crontab -r >/dev/null 2>&1 || true; fi
  systemctl --user disable --now "$unit" >/dev/null 2>&1 || true
  rm -f -- "$target"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
}
trap cleanup EXIT
cat >"$target" <<'UNIT'
[Unit]
Description=Runner-MCP isolated M2 lifecycle proof
[Service]
Type=simple
ExecStart=/usr/bin/sleep 300
Restart=on-failure
RestartSec=1
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now "$unit"
for _ in {1..15}; do
  [[ "$(systemctl --user is-active "$unit")" == "active" ]] && break
  sleep 1
done
[[ "$(systemctl --user is-active "$unit")" == "active" ]]
oldpid="$(systemctl --user show "$unit" --property=MainPID --value)"
[[ "$oldpid" =~ ^[1-9][0-9]*$ ]]
# Kill ONLY the test-owned service process. Automatic Restart=on-failure should recover.
kill -KILL "$oldpid"
restarted=false
for _ in {1..25}; do
  newpid="$(systemctl --user show "$unit" --property=MainPID --value)"
  if [[ "$newpid" =~ ^[1-9][0-9]*$ && "$newpid" != "$oldpid" && "$(systemctl --user is-active "$unit")" == "active" ]]; then
    restarted=true
    break
  fi
  sleep 1
done
[[ "$restarted" == true ]]
# Verify that the recovered test unit has an enabled boot target link. This is
# an offline persistence guard; it does not prove a full physical host reboot.
link="$unit_dir/default.target.wants/$unit"
[[ -L "$link" ]]
[[ "$(readlink "$link")" == "$target" ]]
[[ "$(systemctl --user is-enabled "$unit")" == "enabled" ]]
# Recycle only the disposable GitHub-hosted runner's user manager, never PID1.
# The enabled test unit must recover under a NEW manager and process generation.
manager_pid_before="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
[[ "$manager_pid_before" =~ ^[1-9][0-9]*$ ]]
oldpid="$(systemctl --user show "$unit" --property=MainPID --value)"
sudo systemctl restart "user@${uid}.service"
manager_recovered=false
for _ in {1..30}; do
  if systemctl --user show-environment >/dev/null 2>&1; then
    manager_pid_after="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
    current_pid="$(systemctl --user show "$unit" --property=MainPID --value)"
    if [[ "$manager_pid_after" =~ ^[1-9][0-9]*$ && "$manager_pid_after" != "$manager_pid_before" && "$current_pid" =~ ^[1-9][0-9]*$ && "$current_pid" != "$oldpid" && "$(systemctl --user is-active "$unit")" == "active" ]]; then
      manager_recovered=true
      break
    fi
  fi
  sleep 1
done
[[ "$manager_recovered" == true ]]
[[ -L "$link" ]]
[[ "$(readlink "$link")" == "$target" ]]
[[ "$(systemctl --user is-enabled "$unit")" == "enabled" ]]
# Simulate rollback of an inactive unit candidate by restoring its original bytes.
baseline_restart="$(systemctl --user show "$unit" --property=RestartUSec --value)"
[[ -n "$baseline_restart" ]]
cp "$target" "$target.previous"
sed -i 's/RestartSec=1/RestartSec=2/' "$target"
systemctl --user daemon-reload
candidate_restart="$(systemctl --user show "$unit" --property=RestartUSec --value)"
[[ "$candidate_restart" != "$baseline_restart" ]]
cmp -s "$target" "$target.previous" && exit 1
mv "$target.previous" "$target"
systemctl --user daemon-reload
grep -Fx 'RestartSec=1' "$target" >/dev/null
restored_restart="$(systemctl --user show "$unit" --property=RestartUSec --value)"
[[ "$restored_restart" == "$baseline_restart" ]]
systemctl --user disable --now "$unit"
[[ "$(systemctl --user is-enabled "$unit" 2>/dev/null || :)" != "enabled" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
# Test ONLY the disposable GitHub-hosted runner scheduler with harmless /usr/bin/true.
# There must be no pre-existing owner crontab; never replace third-party cron entries.
command -v crontab >/dev/null
if cron_output="$(LC_ALL=C crontab -l 2>&1)"; then
  echo "STOP: disposable CI user already has a crontab" >&2
  exit 1
else
  cron_rc=$?
  if [[ "$cron_rc" != 1 || "$cron_output" != "no crontab for $(id -un)" ]]; then
    echo "STOP: disposable CI cron state is ambiguous" >&2
    exit 1
  fi
fi
cron_line="17 * * * * /usr/bin/true"
printf '%s\n' "$cron_line" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$cron_line" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
# Stop cron before starting the test-owned unit: never overlap supervisors.
crontab -r
if crontab -l >/dev/null 2>&1; then
  echo "STOP: cron remains during systemd activation" >&2
  exit 1
fi
systemctl --user enable --now "$unit"
[[ "$(systemctl --user is-active "$unit")" == "active" ]]
if crontab -l >/dev/null 2>&1; then
  echo "STOP: cron and systemd overlap" >&2
  exit 1
fi
# Rollback: stop the test-owned user unit before restoring the original cron.
systemctl --user disable --now "$unit"
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
printf '%s\n' "$cron_line" | crontab -
[[ "$(crontab -l)" == "$cron_line" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
crontab -r
test_crontab_owned=false

# Een echte maar VOLLEDIG DISPOSABLE test van een zesrollen-crontab: laat
# vijf onschuldige rollen en een niet-beheerde externe cronregel ongemoeid
# terwijl alleen github-watcher naar de BESTAANDE test-eigen systemd-unit gaat.
# Dit bewijst scheduler/rollback-bytes, niet de productie-executables of ACK.
original_six_cron="$(cat <<'SIX_CRON'
17 * * * * /usr/bin/true # test-foreign-job
# BEGIN RUNNER MCP AUTOSTART v1
MAILTO=""
* * * * * /usr/bin/true # testrole:server
* * * * * /usr/bin/true # testrole:topology-heartbeat
* * * * * /usr/bin/true # testrole:github-watcher
* * * * * /usr/bin/true # testrole:completion-watcher
* * * * * /usr/bin/true # testrole:agent-bus-worker
* * * * * /usr/bin/true # testrole:fabric-agent-qualification
# END RUNNER MCP AUTOSTART v1
SIX_CRON
)"
selected_test_role='* * * * * /usr/bin/true # testrole:github-watcher'
[[ "$(printf '%s\n' "$original_six_cron" | grep -Fxc "$selected_test_role")" == 1 ]]
candidate_five_cron="$(printf '%s\n' "$original_six_cron" | grep -Fvx "$selected_test_role")"
[[ "$candidate_five_cron" != "$original_six_cron" ]]
[[ "$(printf '%s\n' "$candidate_five_cron" | grep -c '# testrole:')" == 5 ]]
[[ "$(printf '%s\n' "$candidate_five_cron" | grep -Fxc '17 * * * * /usr/bin/true # test-foreign-job')" == 1 ]]
[[ "$(printf '%s\n' "$candidate_five_cron" | grep -Fxc '# BEGIN RUNNER MCP AUTOSTART v1')" == 1 ]]
[[ "$(printf '%s\n' "$candidate_five_cron" | grep -Fxc '# END RUNNER MCP AUTOSTART v1')" == 1 ]]

# De echte Linux-crontab blijft het exact bewaarde herstelobject. Geen
# upload, config, Agent Bus of original-host-pad wordt hier geraakt.
printf '%s\n' "$original_six_cron" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
printf '%s\n' "$candidate_five_cron" | crontab -
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ "$(systemctl --user is-enabled "$unit" 2>/dev/null || :)" != "enabled" ]]

# Precies één, reeds bestaande disposable systemd-nevenunit starten. De
# vijf ongeroerde cronrollen blijven exact aanwezig. Unit wordt NIET
# enabled, zodat de nieuwe dienst geen niet-gekwalificeerde bootclaim krijgt.
systemctl --user start "$unit"
[[ "$(systemctl --user is-active "$unit")" == "active" ]]
migrated_pid="$(systemctl --user show "$unit" --property=MainPID --value)"
[[ "$migrated_pid" =~ ^[1-9][0-9]*$ ]]
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ "$(systemctl --user is-enabled "$unit" 2>/dev/null || :)" != "enabled" ]]

# Simuleer mislukte functionele toelating: stop EERST alleen de test-unit,
# controleer werkelijk einde, herstel DAARNA alle originele cronbytes.
systemctl --user stop "$unit"
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
[[ "$(systemctl --user show "$unit" --property=MainPID --value)" == 0 ]]
printf '%s\n' "$original_six_cron" | crontab -
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 6 ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
crontab -r
test_crontab_owned=false
echo "M2_DISPOSABLE_ONE_OF_SIX_CRON_TO_SYSTEMD_AND_FULL_ROLLBACK=PASS"
echo "M2_DISPOSABLE_CRON_TO_SYSTEMD_TO_CRON_ROUNDTRIP=PASS"
echo "M2_DISPOSABLE_ACTUAL_SYSTEMD_RESTART_AND_UNIT_ROLLBACK=PASS"
