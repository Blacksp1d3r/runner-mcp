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
# Reversible scheduler switch using only this fresh disposable runner's crontab.
# No original fleet jobs are touched; abort if this CI user already has any cron.
command -v crontab >/dev/null
cron_error="$(mktemp)"
if crontab -l >/dev/null 2>"$cron_error"; then
  echo "STOP: disposable user already has cron entries" >&2
  rm -f -- "$cron_error"
  exit 1
else
  cron_status=$?
  if [[ "$cron_status" != 1 ]] || ! grep -Eq '^no crontab for [A-Za-z0-9_.-]+
 "$cron_error"; then
    echo "STOP: disposable cron state is ambiguous" >&2
    rm -f -- "$cron_error"
    exit 1
  fi
fi
rm -f -- "$cron_error"
cron_line="17 * * * * /usr/bin/true"
printf '%s\\n' "$cron_line" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$cron_line" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
# Switch: remove cron FIRST, then enable systemd, verify no double-active.
crontab -r
if crontab -l >/dev/null 2>&1; then
  echo "STOP: cron remained present during systemd activation" >&2
  exit 1
fi
systemctl --user enable --now "$unit"
[[ "$(systemctl --user is-active "$unit")" == "active" ]]
if crontab -l >/dev/null 2>&1; then
  echo "STOP: overlapping cron and systemd" >&2
  exit 1
fi
# Rollback: disable systemd FIRST, then restore exact cron line.
systemctl --user disable --now "$unit"
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
printf '%s\\n' "$cron_line" | crontab -
[[ "$(crontab -l)" == "$cron_line" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
crontab -r
test_crontab_owned=false
echo "M2_DISPOSABLE_CRON_TO_SYSTEMD_TO_CRON_ROUNDTRIP=PASS"
echo "M2_DISPOSABLE_ACTUAL_SYSTEMD_RESTART_AND_UNIT_ROLLBACK=PASS"
