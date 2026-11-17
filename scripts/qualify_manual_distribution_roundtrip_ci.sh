#!/usr/bin/env bash
# Echte handmatige distributie-upgrade/rollback, uitsluitend in disposable CI.
#
# Herkomst: HEAD^1 is de GitHub-baseline 0.1.174; HEAD is de PR-kandidaat
# 0.1.175. Beide worden in afzonderlijke wheels gebouwd. Daarna gebruikt één
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

baseline="$(git rev-parse HEAD^1)"
candidate="$(git rev-parse HEAD)"
baseline_version="$(git show "$baseline:pyproject.toml" | python3.12 -c 'import sys,tomllib;print(tomllib.loads(sys.stdin.read())["project"]["version"])')"
candidate_version="$(python3.12 -c 'import tomllib;print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])')"
if [ "$baseline_version" != 0.1.174 ] || [ "$candidate_version" != 0.1.175 ]; then
  echo "STOP: uitsluitend bestaande 0.1.174 naar 0.1.175 PR-bron." >&2
  exit 2
fi

run_temp="$(printenv RUNNER_TEMP || true)"
if [ -z "$run_temp" ] || [ ! -d "$run_temp" ]; then
  echo "STOP: disposable runner-werkmap ontbreekt." >&2
  exit 2
fi
work="$(mktemp -d -p "$run_temp" rmcp-manual-roundtrip-XXXXXXXX)"
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/source/174" "$work/source/175" "$work/wheels/174" "$work/wheels/175"

git archive "$baseline" | tar -xf - -C "$work/source/174"
git archive "$candidate" | tar -xf - -C "$work/source/175"
python3.12 -m pip wheel --disable-pip-version-check --no-deps \
  --wheel-dir "$work/wheels/174" "$work/source/174" >/dev/null
python3.12 -m pip wheel --disable-pip-version-check --no-deps \
  --wheel-dir "$work/wheels/175" "$work/source/175" >/dev/null

wheel174="$(find "$work/wheels/174" -maxdepth 1 -type f -name 'aifordable_runner_mcp-0.1.174-*.whl' -print -quit)"
wheel175="$(find "$work/wheels/175" -maxdepth 1 -type f -name 'aifordable_runner_mcp-0.1.175-*.whl' -print -quit)"
if [ ! -f "$wheel174" ] || [ ! -f "$wheel175" ]; then
  echo "STOP: één van de echte releasewheels ontbreekt." >&2
  exit 2
fi
if [ "$(find "$work/wheels/174" -maxdepth 1 -type f | wc -l)" -ne 1 ] ||
   [ "$(find "$work/wheels/175" -maxdepth 1 -type f | wc -l)" -ne 1 ]; then
  echo "STOP: niet-exacte wheelset." >&2
  exit 2
fi

python3.12 -m venv "$work/runtime"
python="$work/runtime/bin/python"
cli="$work/runtime/bin/runner-mcp"

# Alleen de eerste baseline-installatie haalt dependencies op. De daaropvolgende
# drie transacties krijgen --no-index en --no-deps: uitsluitend reeds gebouwde
# wheels, zonder verborgen downloads of een tweede updater.
"$python" -m pip install --disable-pip-version-check --no-input "$wheel174" >/dev/null

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
}

verify 0.1.174
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel175" >/dev/null
verify 0.1.175
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel174" >/dev/null
verify 0.1.174
"$python" -m pip install --disable-pip-version-check --no-index --no-deps \
  --force-reinstall "$wheel175" >/dev/null
verify 0.1.175

echo "MCP_DISPOSABLE_PY312_MANUAL_174_175_ROLLBACK_REUPGRADE=PASS"
echo "MCP_DISPOSABLE_REAL_SERVING_RESTART_ROLLBACK=PASS"
echo "MCP_PRODUCTION_OR_A7_UPDATE_AUTHORIZED=FALSE"
