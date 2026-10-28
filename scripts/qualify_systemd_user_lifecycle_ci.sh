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
cleanup() {
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
# Simulate rollback of an inactive unit candidate by restoring its original bytes.
cp "$target" "$target.previous"
sed -i 's/RestartSec=1/RestartSec=2/' "$target"
systemctl --user daemon-reload
cmp -s "$target" "$target.previous" && exit 1
mv "$target.previous" "$target"
systemctl --user daemon-reload
grep -Fx 'RestartSec=1' "$target" >/dev/null
systemctl --user disable --now "$unit"
[[ "$(systemctl --user is-enabled "$unit" 2>/dev/null || :)" != "enabled" ]]
[[ "$(systemctl --user is-active "$unit" 2>/dev/null || :)" != "active" ]]
echo "M2_DISPOSABLE_ACTUAL_SYSTEMD_RESTART_AND_UNIT_ROLLBACK=PASS"
