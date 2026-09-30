#!/usr/bin/env bash
set -uo pipefail

# Disposable clean-room control for issue #194.
# Creates one Incus container, installs the exact known lab Python stack inside
# it, runs bounded fresh-process stress, and deletes the container on exit.

IMAGE="${IMAGE:-images:ubuntu/24.04}"
ITERATIONS="${ITERATIONS:-200}"
KEEP_ON_FAILURE="${KEEP_ON_FAILURE:-0}"
NAME="${NAME:-runner-mcp-diag-$(date +%s)}"
FAILED=0

cleanup() {
  local rc=$?
  if [[ "$rc" -ne 0 ]]; then
    FAILED=1
  fi
  if [[ "$KEEP_ON_FAILURE" == "1" && "$FAILED" == "1" ]]; then
    echo "KEEP_ON_FAILURE=1: preserving $NAME for inspection"
    return
  fi
  incus delete -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== INCUS CLEAN-ROOM QUALIFICATION ==="
echo "container=$NAME"
echo "image=$IMAGE"
echo "iterations=$ITERATIONS"

command -v incus >/dev/null 2>&1 || {
  echo "FAIL: incus command unavailable" >&2
  exit 2
}

echo
echo "=== LAUNCH ==="
incus launch "$IMAGE" "$NAME"

echo
echo "=== WAIT FOR EXEC ==="
ready=0
for i in $(seq 1 60); do
  if incus exec "$NAME" -- true >/dev/null 2>&1; then
    ready=1
    echo "PASS: container ready after $i checks"
    break
  fi
  sleep 1
done
if [[ "$ready" != "1" ]]; then
  echo "FAIL: container did not become ready" >&2
  exit 3
fi

echo
echo "=== CONTAINER BASELINE ==="
incus exec "$NAME" -- bash -lc '
  set -euxo pipefail
  uname -a
  cat /etc/os-release
  nproc
  free -h
  df -h /
'

echo
echo "=== INSTALL DISTRO PYTHON TOOLING ==="
incus exec "$NAME" -- bash -lc '
  set -euxo pipefail
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends python3.12-venv ca-certificates
  /usr/bin/python3.12 --version
  /usr/bin/python3.12 -m venv /opt/mcp-diag
  /opt/mcp-diag/bin/python -m pip install --upgrade pip
'

echo
echo "=== INSTALL EXACT KNOWN LAB STACK ==="
incus exec "$NAME" -- bash -lc '
  set -euxo pipefail
  PY=/opt/mcp-diag/bin/python
  "$PY" -m pip install --only-binary=:all: \
    "mcp==2.2.0" \
    "mcp-types==2.2.0" \
    "pydantic==2.13.5" \
    "pydantic-core==2.46.5" \
    "starlette==0.52.1" \
    "httpx2==2.13.1" \
    "cryptography==50.0.2" \
    "cffi==2.1.1" \
    "rpds-py==2026.6.3"
  "$PY" -m pip check
  "$PY" - <<"PY"
import importlib.metadata as md
import sys
print("python", sys.version.replace("\n", " "))
for package in (
    "mcp", "mcp-types", "pydantic", "pydantic-core", "starlette",
    "httpx2", "cryptography", "cffi", "rpds-py",
):
    print(package, md.version(package))
PY
'

run_module() {
  local module="$1"
  echo
  echo "=== STRESS: $module ==="
  incus exec "$NAME" -- env MODULE="$module" ITERATIONS="$ITERATIONS" bash -lc '
    set -u
    PY=/opt/mcp-diag/bin/python
    for i in $(seq 1 "$ITERATIONS"); do
      "$PY" -X faulthandler -c "import importlib, os; importlib.import_module(os.environ[\"MODULE\"])" \
        >/tmp/mcp-diag.out 2>/tmp/mcp-diag.err
      rc=$?
      if [ "$rc" -ne 0 ]; then
        echo "FAIL: $MODULE iteration=$i rc=$rc"
        cat /tmp/mcp-diag.out || true
        cat /tmp/mcp-diag.err || true
        exit "$rc"
      fi
    done
    echo "PASS: $MODULE $ITERATIONS/$ITERATIONS"
  '
}

run_module mcp.server
run_module mcp.server.mcpserver.utilities.func_metadata
run_module pydantic_core
run_module _cffi_backend
run_module rpds.rpds
run_module cryptography.hazmat.bindings._rust

echo
echo "=== HOST KERNEL FAULTS DURING TEST WINDOW ==="
journalctl -k --no-pager --since="-30 minutes" 2>/dev/null \
  | grep -Eai 'segfault|general protection|mce|machine check|hardware error|edac|memory failure|i/o error|nvme.*(error|fail)|ext4.*(error|corrupt)' \
  | tail -n 200 || true

echo
echo "PASS: disposable Incus clean-room qualification completed"
