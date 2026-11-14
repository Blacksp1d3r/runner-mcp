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
peer_unit=""
peer_target=""
peer_old_pid=""
peer_work=""
cleanup() {
  # Ook bij een afgebroken test uitsluitend de zelfgemaakte peer-unit,
  # oude nep-cronworker en wegwerpbestanden opruimen.
  if [[ -n "$peer_unit" ]]; then
    systemctl --user disable --now "$peer_unit" >/dev/null 2>&1 || true
  fi
  if [[ -n "$peer_old_pid" ]]; then
    kill "$peer_old_pid" >/dev/null 2>&1 || true
    wait "$peer_old_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$peer_target" ]]; then rm -f -- "$peer_target"; fi
  if [[ -n "$peer_work" && "$peer_work" == "${RUNNER_TEMP:?}"/runner-mcp-866-peer.* ]]; then
    rm -rf -- "$peer_work"
  fi
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

# M3 bronproef op dezelfde disposable host. Deze keer is de unit GEEN
# algemene sleep-dienst: hij is exact met de echte Runner-MCP-bronrenderer
# gegenereerd en gebruikt de bestaande cron_autostart.run_cron_component.
# De tijdelijke neprol mag geen netwerk, credentials of productiecode draaien.
peer_work="$(mktemp -d "${RUNNER_TEMP:?}/runner-mcp-866-peer.XXXXXX")"
peer_private="$peer_work/private"
peer_exe="$peer_work/fake-runner-mcp"
peer_log="$peer_work/starts.log"
peer_venv="$peer_work/venv"
mkdir -m 0700 "$peer_private"
python3 -m venv "$peer_venv"
PIP_DISABLE_PIP_VERSION_CHECK=1 "$peer_venv/bin/python" -m pip install -q -e .

# Een test-only binair met dezelfde vaste Runner-MCP argumenten; de lock,
# fstat-controle, flock en execv zijn WEL de echte geïnstalleerde broncode.
printf '#!%s\n' "$peer_venv/bin/python" > "$peer_exe"
cat >> "$peer_exe" <<'FAKE_RUNNER_MCP'
from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from runner_mcp.cron_autostart import run_cron_component

if len(sys.argv) not in (5, 6) or sys.argv[1] != "--config-dir":
    raise SystemExit(21)
config = Path(sys.argv[2])
args = sys.argv[3:]
if args == ["autostart", "cron-run", "github-watcher"]:
    run_cron_component(
        config_dir=config,
        executable=Path(__file__),
        component="github-watcher",
    )
elif args == ["github-watcher", "run"]:
    # Simulatie van een langlopende watcher, geen netwerk of mailbox.
    os.umask(0o077)
    with (Path(__file__).resolve().parent / "starts.log").open("a") as evidence:
        evidence.write(f"{os.getpid()}\n")
        evidence.flush()
        os.fsync(evidence.fileno())
    time.sleep(45)
else:
    raise SystemExit(22)
FAKE_RUNNER_MCP
chmod 0700 "$peer_exe"

# Geen bestaande, mogelijk vreemde unit overnemen of verwijderen. De
# dynamisch gegenereerde service blijft static en uitsluitend test-owned.
candidate_target="$unit_dir/runner-mcp-github-watcher.service"
if [[ -e "$candidate_target" || -L "$candidate_target" ]]; then
  echo "STOP: disposable peer target already belongs to another owner" >&2
  exit 1
fi
peer_unit="runner-mcp-github-watcher.service"
peer_target="$candidate_target"
"$peer_venv/bin/python" - "$peer_exe" "$peer_private" "$peer_target" <<'PY_GENERATE'
from pathlib import Path
import sys
from runner_mcp import autostart

executable, config, target = map(Path, sys.argv[1:])
autostart.configured_autostart_components = lambda _path: (
    "server", "github-watcher",
)
name, candidate = autostart.render_inactive_cron_server_peer_unit(
    config_dir=config, executable=executable, component="github-watcher",
)
assert name == target.name
assert '"autostart" "cron-run" "github-watcher"' in candidate
assert "Requires=runner-mcp.service" not in candidate
assert "[Install]" not in candidate
assert candidate.count("ExecStart=") == 1
target.write_text(candidate, encoding="utf-8")
PY_GENERATE
# Houd exact de gegenereerde kandidaatbytes uitsluitend op de testhost vast.
# Na de positieve herstelproef gebruiken we ze voor een tweede negatieve
# omschakeling, zonder een nieuw unittemplate of productiemanager te maken.
cp -- "$peer_target" "$peer_work/peer-unit.template"
systemctl --user daemon-reload
[[ "$(systemctl --user is-enabled "$peer_unit")" == "static" ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]

# Zet nu OOK de zes onschuldige cronregels werkelijk terug: de integratieproef
# combineert exact crontab-behoud met de werkelijk gegenereerde lockende peer.
# Geen van deze zes testrollen voert software of netwerkverzoeken uit.
printf '%s\n' "$original_six_cron" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$original_six_cron" ]]

# Oude cron-wrapper simuleren met dezelfde echte flock/execv-broncode.
"$peer_exe" --config-dir "$peer_private" autostart cron-run github-watcher &
peer_old_pid=$!
for _ in {1..60}; do
  [[ -f "$peer_log" ]] && break
  kill -0 "$peer_old_pid"
  sleep 0.1
done
[[ -f "$peer_log" ]]
[[ "$(grep -c '^' "$peer_log")" == 1 ]]
"$peer_venv/bin/python" - "$peer_private" <<'PY_LOCKED'
from pathlib import Path
import sys
from runner_mcp.cron_autostart import component_active
assert component_active(Path(sys.argv[1]), "github-watcher")
PY_LOCKED

# De daadwerkelijke kandidaat kan met bezette oude lock GEEN tweede worker
# aanmaken. Een status 'inactive' is GEEN geslaagde cutover.
systemctl --user start "$peer_unit"
for _ in {1..60}; do
  [[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]] && break
  sleep 0.1
done
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
[[ "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]
[[ "$(grep -c '^' "$peer_log")" == 1 ]]
kill -0 "$peer_old_pid"
[[ "$(crontab -l)" == "$original_six_cron" ]]

# Na bewezen einde van de oorspronkelijke process/lock-generatie mag de
# exacte statische test-unit wel één nieuwe rol starten.
systemctl --user stop "$peer_unit"
# Exact één cronregel wordt verwijderd; alle andere vijf en de vreemde
# cronregel blijven bestaan, voordat de oude worker wordt vrijgegeven.
printf '%s\n' "$candidate_five_cron" | crontab -
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 5 ]]
kill "$peer_old_pid"
wait "$peer_old_pid" >/dev/null 2>&1 || true
peer_old_pid=""
"$peer_venv/bin/python" - "$peer_private" <<'PY_UNLOCKED'
from pathlib import Path
import sys
from runner_mcp.cron_autostart import component_active
assert not component_active(Path(sys.argv[1]), "github-watcher")
PY_UNLOCKED
systemctl --user start "$peer_unit"
for _ in {1..60}; do
  if [[ -f "$peer_log" && "$(grep -c '^' "$peer_log")" == 2 ]]; then break; fi
  sleep 0.1
done
[[ "$(grep -c '^' "$peer_log")" == 2 ]]
[[ "$(systemctl --user is-active "$peer_unit")" == "active" ]]
peer_new_pid="$(systemctl --user show "$peer_unit" --property=MainPID --value)"
[[ "$peer_new_pid" =~ ^[1-9][0-9]*$ ]]
[[ "$peer_new_pid" == "$(tail -n 1 "$peer_log")" ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == "static" ]]

# Stop en controleer het werkelijk vrijgeven van de oude, hergebruikte lock;
# laat de bestaande originele zes-cronregelsproef en output onaangeroerd.
systemctl --user stop "$peer_unit"
[[ "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]
"$peer_venv/bin/python" - "$peer_private" <<'PY_FINAL'
from pathlib import Path
import sys
from runner_mcp.cron_autostart import component_active
assert not component_active(Path(sys.argv[1]), "github-watcher")
PY_FINAL
[[ "$(grep -c '^' "$peer_log")" == 2 ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == "static" ]]
[[ "$(crontab -l)" == "$candidate_five_cron" ]]

# Bij afwijzing van de functionele canary: eerst de rol stoppen, dan het
# test-owned unitbestand en de managercache verwijderen, dan exact het oude
# crontab herstellen. Zo kan een managed-marker de cron-reconciler niet hinderen.
rm -- "$peer_target"
systemctl --user daemon-reload
[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
printf '%s\n' "$original_six_cron" | crontab -
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 6 ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -Fxc '17 * * * * /usr/bin/true # test-foreign-job')" == 1 ]]
crontab -r
test_crontab_owned=false
[[ "$(crontab -l 2>/dev/null || :)" == "" ]]

# NEGATIEVE M3-bronproef: na de eenrols-cronuitsluiting faalt de werkelijk
# gerenderde systemd-kandidaat omdat uitsluitend de TEST-launcher niet meer
# uitvoerbaar is. We mogen dan geen lopende nieuwe rol of fictieve ACK zien.
# De rollback verwijdert eerst de test-unit en herstelt daarna de volledige
# oorspronkelijke crontab, inclusief de vreemde regel. Geen live hostactie.
[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
install -m 0600 -- "$peer_work/peer-unit.template" "$peer_target"
cmp -s "$peer_work/peer-unit.template" "$peer_target"
systemctl --user daemon-reload
[[ "$(systemctl --user is-enabled "$peer_unit")" == "static" ]]
printf '%s\n' "$original_six_cron" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$original_six_cron" ]]
printf '%s\n' "$candidate_five_cron" | crontab -
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 5 ]]
chmod 000 "$peer_exe"
systemctl --user start "$peer_unit" >/dev/null 2>&1 || true
for _ in {1..60}; do
  if [[ "$(systemctl --user show "$peer_unit" --property=Result --value)" == "exit-code" ]]; then break; fi
  sleep 0.1
done
[[ "$(systemctl --user show "$peer_unit" --property=Result --value)" == "exit-code" ]]
[[ "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
[[ "$(grep -c '^' "$peer_log")" == 2 ]]
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
systemctl --user stop "$peer_unit"
[[ "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]
rm -- "$peer_target"
systemctl --user daemon-reload
[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
chmod 0700 "$peer_exe"
printf '%s\n' "$original_six_cron" | crontab -
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 6 ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -Fxc '17 * * * * /usr/bin/true # test-foreign-job')" == 1 ]]
[[ "$(grep -c '^' "$peer_log")" == 2 ]]
crontab -r
test_crontab_owned=false
[[ "$(crontab -l 2>/dev/null || :)" == "" ]]
# M3 opstartbestendigheid, ook met precies één overgezette rol:
# de bronrenderer is DEZELFDE cron-geflockte eenrolsunit, nu alleen met de
# enablebare installhaak. Op de disposable host wordt na exclusieve
# cronuitsluiting één service gestart, de user-manager echt herstart, en
# pas daarna de originele crontab exact hersteld. Geen fysieke hostreboot.
"$peer_venv/bin/python" - "$peer_exe" "$peer_private" "$peer_target" <<'PY_BOOT'
from pathlib import Path
import sys
from runner_mcp import autostart

executable, config, target = map(Path, sys.argv[1:])
autostart.configured_autostart_components = lambda _path: (
    "server", "github-watcher",
)
static_name, static = autostart.render_inactive_cron_server_peer_unit(
    config_dir=config, executable=executable, component="github-watcher",
)
boot_name, candidate = autostart.render_boot_candidate_cron_peer_unit(
    config_dir=config, executable=executable, component="github-watcher",
)
assert boot_name == static_name == target.name
assert candidate == static + "\n[Install]\nWantedBy=default.target\n"
assert ' "autostart" "cron-run" "github-watcher"' in candidate
assert "Requires=runner-mcp.service" not in candidate
target.write_text(candidate, encoding="utf-8")
PY_BOOT
systemctl --user daemon-reload
[[ "$(systemctl --user is-enabled "$peer_unit")" == "disabled" ]]
printf '%s\n' "$original_six_cron" | crontab -
test_crontab_owned=true
[[ "$(crontab -l)" == "$original_six_cron" ]]
printf '%s\n' "$candidate_five_cron" | crontab -
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 5 ]]
systemctl --user enable --now "$peer_unit"
[[ "$(systemctl --user is-enabled "$peer_unit")" == "enabled" ]]
boot_link="$unit_dir/default.target.wants/$peer_unit"
[[ -L "$boot_link" ]]
[[ "$(readlink "$boot_link")" == "$peer_target" ]]
for _ in {1..60}; do
  if [[ -f "$peer_log" && "$(grep -c '^' "$peer_log")" == 3 ]]; then break; fi
  sleep 0.1
done
[[ "$(grep -c '^' "$peer_log")" == 3 ]]
[[ "$(systemctl --user is-active "$peer_unit")" == "active" ]]
boot_pid_before="$(systemctl --user show "$peer_unit" --property=MainPID --value)"
[[ "$boot_pid_before" == "$(tail -n 1 "$peer_log")" ]]
manager_before="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
[[ "$manager_before" =~ ^[1-9][0-9]*$ ]]
# De testhost herstart alleen haar EIGEN user-manager, nooit PID1 of de
# originele github-runner. De enable-link moet opnieuw een werkende rol starten.
sudo systemctl restart "user@${uid}.service"
boot_recovered=false
for _ in {1..30}; do
  if systemctl --user show-environment >/dev/null 2>&1; then
    manager_after="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
    boot_pid_after="$(systemctl --user show "$peer_unit" --property=MainPID --value)"
    if [[ "$manager_after" =~ ^[1-9][0-9]*$ && "$manager_after" != "$manager_before" && "$boot_pid_after" =~ ^[1-9][0-9]*$ && "$boot_pid_after" != "$boot_pid_before" && "$(systemctl --user is-active "$peer_unit")" == "active" && -f "$peer_log" && "$(grep -c '^' "$peer_log")" == 4 ]]; then
      boot_recovered=true
      break
    fi
  fi
  sleep 1
done
[[ "$boot_recovered" == true ]]
[[ "$(tail -n 1 "$peer_log")" == "$boot_pid_after" ]]
[[ -L "$boot_link" && "$(readlink "$boot_link")" == "$peer_target" ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == "enabled" ]]
[[ "$(crontab -l)" == "$candidate_five_cron" ]]

# M3 NEGATIEF: na de BEWEZEN managerherstart gaat juist de enabled
# testrol stuk. Maak uitsluitend de tijdelijke nep-CLI onuitvoerbaar en
# dood enkel de exact uit systemd afgeleide test-MainPID. De echte unit
# probeert dan de bestaande Restart=on-failure-route, maar mag nooit
# een tweede taakrecord produceren of cron ongemerkt veranderen.
chmod 000 "$peer_exe"
kill -KILL "$boot_pid_after"
boot_restart_failed=false
for _ in {1..120}; do
  if [[ "$(systemctl --user show "$peer_unit" --property=Result --value)" == "exit-code" && "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]; then
    boot_restart_failed=true
    break
  fi
  sleep 0.1
done
[[ "$boot_restart_failed" == true ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
[[ "$(grep -c '^' "$peer_log")" == 4 ]]
[[ "$(crontab -l)" == "$candidate_five_cron" ]]
[[ -L "$boot_link" && "$(readlink "$boot_link")" == "$peer_target" ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == "enabled" ]]

# In omgekeerde richting eerst de enable-link en actieve nieuwe rol
# verwijderen; pas als de oude cronlock vrij is, de zes regels terugzetten.
systemctl --user disable --now "$peer_unit"
# Ook bij een voortdurend mislukte auto-restart mag geen unit herstarten.
chmod 0700 "$peer_exe"
[[ "$(systemctl --user show "$peer_unit" --property=MainPID --value)" == 0 ]]
[[ "$(systemctl --user is-enabled "$peer_unit" 2>/dev/null || :)" != "enabled" ]]
[[ ! -L "$boot_link" ]]
"$peer_venv/bin/python" - "$peer_private" <<'PY_BOOT_UNLOCKED'
from pathlib import Path
import sys
from runner_mcp.cron_autostart import component_active
assert not component_active(Path(sys.argv[1]), "github-watcher")
PY_BOOT_UNLOCKED
rm -- "$peer_target"
systemctl --user daemon-reload
[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
printf '%s\n' "$original_six_cron" | crontab -
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 6 ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -Fxc '17 * * * * /usr/bin/true # test-foreign-job')" == 1 ]]
[[ "$(grep -c '^' "$peer_log")" == 4 ]]

# Rollback moet ook EEN TWEEDE user-manager-herstart overleven. Na stop,
# disable, lockvrijgave, delete en exact cronherstel is een later start-
# signaal van de oude enabled-unit verboden. Alleen op de disposable host.
rollback_manager_before="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
[[ "$rollback_manager_before" =~ ^[1-9][0-9]*$ ]]
sudo systemctl restart "user@${uid}.service"
rollback_manager_recovered=false
for _ in {1..30}; do
  if systemctl --user show-environment >/dev/null 2>&1; then
    rollback_manager_after="$(systemctl show "user@${uid}.service" --property=MainPID --value)"
    if [[ "$rollback_manager_after" =~ ^[1-9][0-9]*$ && "$rollback_manager_after" != "$rollback_manager_before" ]]; then
      rollback_manager_recovered=true
      break
    fi
  fi
  sleep 1
done
[[ "$rollback_manager_recovered" == true ]]
[[ ! -e "$peer_target" && ! -L "$peer_target" && ! -L "$boot_link" ]]
[[ "$(systemctl --user is-active "$peer_unit" 2>/dev/null || :)" != "active" ]]
[[ "$(systemctl --user is-enabled "$peer_unit" 2>/dev/null || :)" != "enabled" ]]
[[ "$(crontab -l)" == "$original_six_cron" ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -c '# testrole:')" == 6 ]]
[[ "$(printf '%s\n' "$(crontab -l)" | grep -Fxc '17 * * * * /usr/bin/true # test-foreign-job')" == 1 ]]
[[ "$(grep -c '^' "$peer_log")" == 4 ]]
crontab -r
test_crontab_owned=false
[[ "$(crontab -l 2>/dev/null || :)" == "" ]]
# M3 brongekoppelde proef: beoordeel voor het eerst de ECHTE door de
# Runner-MCP-renderers geproduceerde ZES cronregels (niet de eerdere inert
# gelabelde fixtures), de bootbare unit én ALLE fase-checkpoints tegen de
# werkelijke disposable crontab/systemd-manager. Ook bij mislukking ruimt de
# bestaande EXIT-trap uitsluitend zelfgemaakte testassets op.
# Dit is geen fysieke origineel-hostactuatie en geen echte Fabric-ACK.
phase_script="$peer_work/phase-checkpoint-disposable.py"
cat >"$phase_script" <<'PY_PHASE_CHECKPOINT'
"""Exact source-bound M3 phase checks on this guarded disposable CI user."""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from pathlib import Path

from runner_mcp import autostart
from runner_mcp.cron_autostart import (
    component_active,
    read_crontab,
    render_cron_block,
    cron_status,
)

mode = sys.argv[1]
scratch, executable, config, unit = map(Path, sys.argv[2:6])
role = "github-watcher"
roles = (
    "server", "topology-heartbeat", "github-watcher",
    "completion-watcher", "agent-bus-worker",
    "fabric-agent-qualification",
)
autostart.configured_autostart_components = lambda _path: roles
original_file = scratch / "source-original.cron"
candidate_file = scratch / "source-candidate.cron"
boot_file = scratch / "source-boot-unit.txt"
if mode == "prepare":
    original = "17 * * * * /usr/bin/true # test-foreign-job\n\n" + "\n".join(
        render_cron_block(
            executable=executable, config_dir=config,
            components=roles, port=8000,
        )
    ) + "\n"
    original_file.write_text(original, encoding="utf-8")
else:
    original = original_file.read_text(encoding="utf-8")
preflight = autostart.AutostartMigrationPlan(
    component=role, state="PLAN_ONLY",
    reason_code="original_host_and_rollback_not_attested",
    cron_installed=True, systemd_manager_reachable=True,
    systemd_units_absent=True,
)
if mode in ("peer_failed_idle", "recover_failed_peer"):
    # De test-executable is met opzet stuk. Herstel mag nooit opnieuw
    # afhankelijk zijn van het kunnen uitvoeren van die kapotte kandidaat.
    # Gebruik uitsluitend de eerder door de bronrenderer vastgelegde
    # rollback-, kandidaat- en unitbytes uit deze disposable testfixture.
    pinned_boot = boot_file.read_text(encoding="utf-8")
    suffix = "\n[Install]\nWantedBy=default.target\n"
    assert pinned_boot.endswith(suffix)
    plan = autostart.SinglePeerSystemdMigrationPreview(
        component=role, original_crontab=original,
        candidate_crontab=candidate_file.read_text(encoding="utf-8"),
        rollback_crontab_sha256=hashlib.sha256(original.encode("utf-8")).hexdigest(),
        inactive_unit_name=unit.name,
        inactive_unit_contents=pinned_boot.removesuffix(suffix),
        boot_unit_contents=pinned_boot,
    )
else:
    plan = autostart.plan_single_peer_systemd_migration(
        preflight=preflight, original_crontab=original,
        executable=executable, config_dir=config,
        components=roles, component=role,
    )
assert plan.cutover_authorized is False
assert plan.inactive_unit_name == unit.name
if mode == "prepare":
    assert not unit.exists() and not unit.is_symlink()
    candidate_file.write_text(plan.candidate_crontab, encoding="utf-8")
    boot_file.write_text(plan.boot_unit_contents, encoding="utf-8")
    assert plan.original_crontab.count("autostart cron-run") == 6
    assert plan.candidate_crontab.count("autostart cron-run") == 5
    raise SystemExit(0)

assert plan.candidate_crontab == candidate_file.read_text(encoding="utf-8")
assert plan.boot_unit_contents == boot_file.read_text(encoding="utf-8")
observed_unit = unit.read_text(encoding="utf-8") if unit.is_file() else None
if observed_unit is None:
    enabled = active = False
    pid = 0
else:
    def show(*args: str) -> str:
        return subprocess.run(
            ["systemctl", "--user", *args],
            capture_output=True, text=True, timeout=10, check=False,
        ).stdout.strip()
    enabled = show("is-enabled", unit.name) == "enabled"
    active = show("is-active", unit.name) == "active"
    raw_pid = show("show", unit.name, "--property=MainPID", "--value")
    assert raw_pid.isdecimal()
    pid = int(raw_pid)
lock_active = component_active(config, role)
log = executable.parent / "starts.log"
records = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
new_ack = False
if mode == "new_worker_ack":
    # Synthetic durable job receipt, NOT a real Fabric app ACK.
    assert len(records) == 5 and pid == int(records[-1])
    new_ack = True
# Echte, begrensde herstelacties blijven test-only binnen de bestaande
# GitHub-hosted disposable CI-gate. Geen nieuw productiemechanisme/CLI.
if mode == "recover_failed_peer":
    root = os.environ.get("RUNNER_TEMP")
    expected_unit = Path.home() / ".config/systemd/user/runner-mcp-github-watcher.service"
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
        or os.geteuid() == 0
        or not root
        or not scratch.resolve().is_relative_to(Path(root).resolve())
        or unit != expected_unit
        or unit.parent.is_symlink()
        or unit.is_symlink()
        or not unit.is_file()
    ):
        raise RuntimeError("STOP: original-host or unit identity not disposable")
    identity = unit.stat()
    if (
        identity.st_uid != os.getuid()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
        or identity.st_nlink != 1
    ):
        raise RuntimeError("STOP: unit inode or owner is not qualified")
    assert unit.read_text(encoding="utf-8") == plan.boot_unit_contents
    assert read_crontab() == plan.candidate_crontab
    assert enabled and not active and pid == 0 and not lock_active
    assert len(records) == 5
    before = autostart.propose_single_peer_reconciliation(
        preview=plan, phase="peer_failed_idle",
        observed_crontab=read_crontab(),
        observed_unit_contents=observed_unit,
        unit_enabled=enabled, unit_active=active, main_pid=pid,
        role_lock_active=lock_active, new_function_ack=False,
        cron_rows=tuple(cron_status(
            config_dir=config, components=roles, executable=executable,
        )),
        systemd_rows=tuple(autostart.user_service_status(unit_dir=unit.parent)),
    )
    if (
        not before.consistent
        or before.proposed_step != "DISABLE_FAILED_PEER_THEN_RECHECK"
        or before.action_authorized
    ):
        raise RuntimeError("STOP: mixed-mode failure checkpoint unqualified")

    def required_command(*argv: str, input_text: str | None = None) -> None:
        completed = subprocess.run(
            list(argv), input=input_text, text=True,
            capture_output=True, timeout=30, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("STOP: disposable recovery command failed")

    # Testuitvoerder handelt alléén na expliciete test-only identiteit,
    # geverifieerde volle cronbytes en afwezige PID/lock/ACK. De planner
    # blijft in het echte product NIET-geautoriseerd.
    required_command("systemctl", "--user", "disable", "--now", unit.name)
    assert show("is-enabled", unit.name) == "disabled"
    assert show("is-active", unit.name) != "active"
    assert show("show", unit.name, "--property=MainPID", "--value") == "0"
    assert read_crontab() == plan.candidate_crontab
    assert not component_active(config, role)
    assert unit.read_text(encoding="utf-8") == plan.boot_unit_contents
    assert unit.stat().st_ino == identity.st_ino
    unit.unlink()
    required_command("systemctl", "--user", "daemon-reload")
    assert not unit.exists() and not unit.is_symlink()
    assert read_crontab() == plan.candidate_crontab
    assert show("is-active", unit.name) != "active"
    assert not component_active(config, role)
    ready = autostart.propose_single_peer_reconciliation(
        preview=plan, phase="rollback_ready",
        observed_crontab=read_crontab(),
        observed_unit_contents=None, unit_enabled=False,
        unit_active=False, main_pid=0, role_lock_active=False,
        new_function_ack=False,
        cron_rows=tuple(cron_status(
            config_dir=config, components=roles, executable=executable,
        )),
        systemd_rows=tuple(autostart.user_service_status(unit_dir=unit.parent)),
    )
    if (
        not ready.consistent
        or ready.proposed_step != "RESTORE_EXACT_ORIGINAL_CRONTAB_THEN_RECHECK"
        or ready.action_authorized
    ):
        raise RuntimeError("STOP: one-role cron restore is unqualified")
    required_command("crontab", "-", input_text=plan.original_crontab)
    assert read_crontab() == plan.original_crontab
    assert not component_active(config, role)
    complete = autostart.propose_single_peer_reconciliation(
        preview=plan, phase="rollback_confirmed",
        observed_crontab=read_crontab(),
        observed_unit_contents=None, unit_enabled=False,
        unit_active=False, main_pid=0, role_lock_active=False,
        new_function_ack=False,
        cron_rows=tuple(cron_status(
            config_dir=config, components=roles, executable=executable,
        )),
        systemd_rows=tuple(autostart.user_service_status(unit_dir=unit.parent)),
    )
    assert complete.consistent and complete.proposed_step == "NO_ACTION_ALREADY_RESTORED"
    assert not complete.action_authorized
    assert plan.original_crontab.count("autostart cron-run") == 6
    assert read_crontab().count("17 * * * * /usr/bin/true # test-foreign-job") == 1
    assert len(records) == 5
    print("M3_DISPOSABLE_BOUNDED_SINGLE_ROLE_EXECUTOR_EXACT_ROLLBACK=PASS")
    raise SystemExit(0)

result = autostart.assess_single_peer_migration_checkpoint(
    preview=plan, phase=mode, observed_crontab=read_crontab(),
    observed_unit_contents=observed_unit,
    unit_enabled=enabled, unit_active=active, main_pid=pid,
    role_lock_active=lock_active, new_function_ack=new_ack,
)
assert result.consistent is True, result.reason_code
assert result.next_action_authorized is False

# Dezelfde ECHTE disposable crontab- en systemd-status zijn invoer van het
# nieuwe rolgebonden herstelvoorstel. De functie mag niets uitvoeren.
if mode in ("staged_inactive", "new_worker_ack", "peer_failed_idle",
            "rollback_ready", "rollback_confirmed"):
    cron_rows = tuple(cron_status(
        config_dir=config, components=roles, executable=executable,
    ))
    systemd_rows = tuple(autostart.user_service_status(unit_dir=unit.parent))
    advice = autostart.propose_single_peer_reconciliation(
        preview=plan, phase=mode, observed_crontab=read_crontab(),
        observed_unit_contents=observed_unit, unit_enabled=enabled,
        unit_active=active, main_pid=pid, role_lock_active=lock_active,
        new_function_ack=new_ack,
        cron_rows=cron_rows, systemd_rows=systemd_rows,
    )
    expected_step = {
        "staged_inactive": "REMOVE_EXACT_INACTIVE_PEER_THEN_RECHECK",
        "new_worker_ack": "KEEP_PEER_NO_GENERIC_RECONCILE",
        "peer_failed_idle": "DISABLE_FAILED_PEER_THEN_RECHECK",
        "rollback_ready": "RESTORE_EXACT_ORIGINAL_CRONTAB_THEN_RECHECK",
        "rollback_confirmed": "NO_ACTION_ALREADY_RESTORED",
    }[mode]
    assert advice.consistent is True, advice.reason_code
    assert advice.proposed_step == expected_step
    assert advice.action_authorized is False
    assert advice.rollback_sha256 == plan.rollback_crontab_sha256
    if mode == "new_worker_ack":
        # Een actief unitproces zonder actueel functioneel ACK is geen PASS.
        rejected = autostart.propose_single_peer_reconciliation(
            preview=plan, phase=mode, observed_crontab=read_crontab(),
            observed_unit_contents=observed_unit, unit_enabled=enabled,
            unit_active=active, main_pid=pid, role_lock_active=lock_active,
            new_function_ack=False,
            cron_rows=cron_rows, systemd_rows=systemd_rows,
        )
        assert rejected.consistent is False
        assert rejected.proposed_step == "STOP_UNQUALIFIED"
PY_PHASE_CHECKPOINT

[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
[[ "$(crontab -l 2>/dev/null || :)" == "" ]]
"$peer_venv/bin/python" "$phase_script" prepare "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
crontab "$peer_work/source-original.cron"
test_crontab_owned=true
"$peer_venv/bin/python" "$phase_script" before_exclusion "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
crontab "$peer_work/source-candidate.cron"
"$peer_venv/bin/python" "$phase_script" ready_to_stage "$peer_work" "$peer_exe" "$peer_private" "$peer_target"

# Stage alleen exact de berekende testunit NA de brongecontroleerde
# cronuitsluiting. De vijf overige echte test-cronregels blijven aanwezig.
[[ ! -e "$peer_target" && ! -L "$peer_target" ]]
install -m 0600 -- "$peer_work/source-boot-unit.txt" "$peer_target"
systemctl --user daemon-reload
"$peer_venv/bin/python" "$phase_script" staged_inactive "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
systemctl --user enable --now "$peer_unit"
for _ in {1..80}; do
  if [[ -f "$peer_log" && "$(grep -c '^' "$peer_log")" == 5 ]]; then break; fi
  sleep 0.1
done
[[ "$(grep -c '^' "$peer_log")" == 5 ]]
"$peer_venv/bin/python" "$phase_script" new_worker_ack "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
# Een gezonde peer mag NOOIT door de test-herstelactuator worden gestopt.
if "$peer_venv/bin/python" "$phase_script" recover_failed_peer "$peer_work" "$peer_exe" "$peer_private" "$peer_target" >/dev/null 2>&1; then
  echo "STOP: healthy peer was incorrectly eligible for rollback" >&2
  exit 1
fi
[[ "$(systemctl --user is-active "$peer_unit")" == "active" ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == enabled ]]
[[ "$(crontab -l)" == "$(cat "$peer_work/source-candidate.cron")" ]]
[[ "$(grep -c '^' "$peer_log")" == 5 ]]

# Foutinjectie ALLEEN op eigen disposable nep-worker: het reeds gemeten
# MainPID is precies de laatste geregistreerde teststart. Na exec-failure
# blijft de unit enabled, maar de worker kan geen werkrecord/ACK toevoegen.
# De nieuwe herstelplanner moet nu stop/disable voorstellen, nooit activeren.
test_failed_old_pid="$(systemctl --user show "$peer_unit" --property=MainPID --value)"
[[ "$test_failed_old_pid" =~ ^[1-9][0-9]*$ ]]
[[ "$test_failed_old_pid" == "$(tail -n 1 "$peer_log")" ]]
chmod 000 -- "$peer_exe"
kill -KILL "$test_failed_old_pid"
failed_peer_observed=false
for _ in {1..120}; do
  test_failed_pid="$(systemctl --user show "$peer_unit" --property=MainPID --value)"
  test_failed_result="$(systemctl --user show "$peer_unit" --property=Result --value)"
  if [[ "$test_failed_result" == exit-code && "$test_failed_pid" == 0 ]]; then
    failed_peer_observed=true
    break
  fi
  sleep 0.1
done
[[ "$failed_peer_observed" == true ]]
[[ "$(systemctl --user is-enabled "$peer_unit")" == enabled ]]
[[ "$(grep -c '^' "$peer_log")" == 5 ]]
"$peer_venv/bin/python" "$phase_script" peer_failed_idle "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
# Hergebruik exact één bron- en hostgekwalificeerde, TEST-ONLY herstelactuator.
# Daarin wordt na elke stap live opnieuw geverifieerd. Geen generieke CLI.
"$peer_venv/bin/python" "$phase_script" recover_failed_peer "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
chmod 0700 -- "$peer_exe"
"$peer_venv/bin/python" "$phase_script" rollback_confirmed "$peer_work" "$peer_exe" "$peer_private" "$peer_target"
[[ "$(crontab -l)" == "$(cat "$peer_work/source-original.cron")" ]]
[[ "$(grep -c '^' "$peer_log")" == 5 ]]
crontab -r
test_crontab_owned=false
[[ "$(crontab -l 2>/dev/null || :)" == "" ]]
echo "M2_DISPOSABLE_SOURCE_RENDERED_SIX_ROLE_PHASE_CHECKPOINT_ROUNDTRIP=PASS"
echo "M3_DISPOSABLE_ROLE_RECONCILE_PROPOSALS_SOURCE_READBACK=PASS"
echo "M3_DISPOSABLE_FAILED_PEER_RECOVERY_PROPOSAL_AND_EXACT_CRON_ROLLBACK=PASS"

echo "M2_DISPOSABLE_BOOT_PEER_CRASH_RESTART_FAIL_AND_PERSISTENT_CRON_ROLLBACK=PASS"
echo "M2_DISPOSABLE_BOOTABLE_LOCKED_PEER_USER_MANAGER_RESTART_AND_ROLLBACK=PASS"
echo "M2_DISPOSABLE_FAILED_EXEC_START_EXACT_CRON_ROLLBACK=PASS"
echo "M2_DISPOSABLE_SIX_ROLE_RENDERED_PEER_EXCLUSIVE_SWITCH_AND_ROLLBACK=PASS"
echo "M2_DISPOSABLE_REAL_RENDERED_PEER_AND_SHARED_CRON_LOCK=PASS"
echo "M2_DISPOSABLE_ONE_OF_SIX_CRON_TO_SYSTEMD_AND_FULL_ROLLBACK=PASS"
echo "M2_DISPOSABLE_CRON_TO_SYSTEMD_TO_CRON_ROUNDTRIP=PASS"
echo "M2_DISPOSABLE_ACTUAL_SYSTEMD_RESTART_AND_UNIT_ROLLBACK=PASS"
