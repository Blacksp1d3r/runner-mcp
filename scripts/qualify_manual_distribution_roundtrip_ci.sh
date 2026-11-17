#!/usr/bin/env bash
# Echte handmatige distributie-upgrade/rollback, uitsluitend in disposable CI.
#
# Herkomst: HEAD^1 (0.1.174) of vastgepinde historische broncommit
# 0.1.88; HEAD is 0.1.175. Het gebouwde bronwheel is GEEN serving-A7-attest. Daarna gebruikt één
# private Python 3.12-venv exact die wheels voor vier echte pip-transities.
# Na ELKE transitie wordt de bestaande echte CLI als lokale HTTP-server
# gestart en weer gestopt; de kernel-PID en geladen-versieheader tellen mee.
# Deze proef wijzigt nooit een server, een actieve dienst, een SQL-relay of A7.
set -euo pipefail
umask 077

if [ "$(id -u)" = 0 ] || [ "$(printenv GITHUB_ACTIONS || true)" != true ]; then
  echo "STOP: uitsluitend niet-root op disposable GitHub Actions." >&2
  exit 2
fi
if [ "$(python3.12 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.12" ]; then
  echo "STOP: CPython 3.12 is verplicht." >&2
  exit 2
fi
if [ "$(git rev-parse --is-shallow-repository)" != false ]; then
  echo "STOP: baseline en PR moeten allebei beschikbaar zijn." >&2
  exit 2
fi

if [[ "$#" -gt 1 ]]; then
  echo "STOP: alleen de twee vooraf beoordeelde historische CI-baselines" >&2
  exit 2
fi
case "${1:-}" in
  "")
    baseline="$(git rev-parse HEAD^1)"
    expected_baseline="0.1.174"
    ;;
  --historical-088)
    # Vaste oorspronkelijke Git-bron, GEEN originele server-wheelbron.
    baseline="ce327e5db688fe6bae835a4c181824320f01f762"
    expected_baseline="0.1.88"
    ;;
  *)
    echo "STOP: onbekende CI-bronbaseline" >&2
    exit 2
    ;;
esac
candidate="$(git rev-parse HEAD)"
if ! git cat-file -e "${baseline}^{commit}" ||
   ! git merge-base --is-ancestor "$baseline" "$candidate"; then
  echo "STOP: vaste historische broncommit is niet beschikbaar" >&2
  exit 2
fi
baseline_version="$(git show "$baseline:pyproject.toml" | python3.12 -c 'import sys,tomllib;print(tomllib.loads(sys.stdin.read())["project"]["version"])')"
candidate_version="$(python3.12 -c 'import tomllib;print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])')"
if [ "$baseline_version" != "$expected_baseline" ] ||
   [ "$candidate_version" != 0.1.175 ]; then
  echo "STOP: de historische baseline of kandidaat komt niet overeen" >&2
  exit 2
fi

run_temp="$(printenv RUNNER_TEMP || true)"
if [ -z "$run_temp" ] || [ ! -d "$run_temp" ]; then
  echo "STOP: disposable runner-werkmap ontbreekt." >&2
  exit 2
fi
work="$(mktemp -d -p "$run_temp" rmcp-manual-roundtrip-XXXXXXXX)"
unit="runner-mcp-669-disposable-manual.service"
unit_dir="$HOME/.config/systemd/user"
unit_target="$unit_dir/$unit"
unit_owned=false

cleanup() {
  # Stop de eigen unit vóór verwijderen van wheels en private config.
  if [[ "$unit_owned" == true ]]; then
    if [[ -f "$unit_target" && ! -L "$unit_target" ]] &&
       grep -Fxq 'Description=Runner-MCP 669 disposable manual upgrade proof' "$unit_target"; then
      systemctl --user stop "$unit" >/dev/null 2>&1 || true
      rm -f -- "$unit_target"
      systemctl --user daemon-reload >/dev/null 2>&1 || true
    fi
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT

if [[ "${RUNNER_ENVIRONMENT:-}" != github-hosted ]] ||
   [[ "$(ps -p 1 -o comm=)" != systemd ]]; then
  echo "STOP: niet een disposable systemd-user omgeving" >&2
  exit 2
fi
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
sudo systemctl start "user@$(id -u).service"
for _ in {1..20}; do
  if systemctl --user show-environment >/dev/null 2>&1; then break; fi
  sleep 1
done
systemctl --user show-environment >/dev/null
mkdir -p -- "$unit_dir"
if [[ -e "$unit_target" || -L "$unit_target" ]]; then
  echo "STOP: de testunit bestaat al" >&2
  exit 2
fi
unit_owned=true
mkdir -p "$work/source/baseline" "$work/source/175" "$work/wheels/baseline" "$work/wheels/175"

git archive "$baseline" | tar -xf - -C "$work/source/baseline"
git archive "$candidate" | tar -xf - -C "$work/source/175"
python3.12 -m pip wheel --disable-pip-version-check --no-deps \
  --wheel-dir "$work/wheels/baseline" "$work/source/baseline" >/dev/null
python3.12 -m pip wheel --disable-pip-version-check --no-deps \
  --wheel-dir "$work/wheels/175" "$work/source/175" >/dev/null

wheel_baseline="$(find "$work/wheels/baseline" -maxdepth 1 -type f -name "aifordable_runner_mcp-${baseline_version}-*.whl" -print -quit)"
wheel175="$(find "$work/wheels/175" -maxdepth 1 -type f -name 'aifordable_runner_mcp-0.1.175-*.whl' -print -quit)"
if [[ ! -f "$wheel_baseline" || ! -f "$wheel175" ]]; then
  echo "STOP: één van de exact vaste twee bronwheels ontbreekt" >&2
  exit 2
fi
if [[ "$(find "$work/wheels/baseline" -maxdepth 1 -type f | wc -l)" -ne 1 ]] ||
   [[ "$(find "$work/wheels/175" -maxdepth 1 -type f | wc -l)" -ne 1 ]]; then
  echo "STOP: de wheels zijn niet exact één per broncommit" >&2
  exit 2
fi
python3.12 -m venv "$work/runtime"
python="$work/runtime/bin/python"
cli="$work/runtime/bin/runner-mcp"

# Alleen de eerste baseline-installatie haalt dependencies op. De daaropvolgende
# drie transacties krijgen --no-index en --no-deps: uitsluitend reeds gebouwde
# wheels, zonder verborgen downloads of een tweede updater.
"$python" -m pip install --disable-pip-version-check --no-input "$wheel_baseline" >/dev/null

verify() {
  expected="$1"
  "$python" - "$expected" <<'PY'
import importlib
import importlib.metadata
import pathlib
import site
import sys

expected = sys.argv[1]
actual = importlib.metadata.version("aifordable-runner-mcp")
if actual != expected:
    raise SystemExit(f"installed distribution mismatch: {actual} != {expected}")
module = importlib.import_module("runner_mcp")
if module.__file__ is None or not pathlib.Path(module.__file__).is_file():
    raise SystemExit("installed package module missing")
matches = [
    entry for root in site.getsitepackages()
    for entry in pathlib.Path(root).glob("aifordable_runner_mcp-*.dist-info")
]
if len(matches) != 1 or expected not in matches[0].name:
    raise SystemExit("stale or ambiguous installed dist-info")
print("DISPOSABLE_MANUAL_DIST_VERSION=" + actual)
PY
  "$python" -m pip check >/dev/null
  "$cli" --help >/dev/null
  "$python" scripts/qualify_manual_serving_roundtrip_ci.py "$expected" "$work"
  "$python" scripts/qualify_manual_systemd_service_ci.py "$expected" "$work" "$unit_target"
}

verify "$baseline_version"
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel175" >/dev/null
verify 0.1.175
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel_baseline" >/dev/null
verify "$baseline_version"
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel175" >/dev/null
verify 0.1.175

if [[ "$baseline_version" == "0.1.174" ]]; then
  echo "MCP_DISPOSABLE_PY312_MANUAL_174_175_ROLLBACK_REUPGRADE=PASS"
else
  echo "MCP_DISPOSABLE_PY312_HISTORICAL_SOURCE_088_175_ROLLBACK_REUPGRADE=PASS"
  echo "MCP_DISPOSABLE_HISTORICAL_WHEEL_EQUALS_ORIGINAL_SERVER=NOT_ATTESTED"
fi
echo "MCP_DISPOSABLE_REAL_SERVING_RESTART_ROLLBACK=PASS"
echo "MCP_DISPOSABLE_SYSTEMD_USER_MANAGED_ROUNDTRIP=PASS"
echo "MCP_PRODUCTION_OR_A7_UPDATE_AUTHORIZED=FALSE"
