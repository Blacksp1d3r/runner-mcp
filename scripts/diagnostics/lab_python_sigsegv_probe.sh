#!/usr/bin/env bash
set -uo pipefail

# Local-only bounded diagnostic for issue #194.
# Does not install packages, change services, or modify Runner MCP state.

PY="${RUNNER_MCP_PYTHON:-/home/aifordable-runner/.local/share/runner-mcp/venv/bin/python}"
ITERATIONS="${ITERATIONS:-200}"
PER_CPU_ITERATIONS="${PER_CPU_ITERATIONS:-10}"

if [[ ! -x "$PY" ]]; then
  echo "FAIL: Python executable not found or not executable: $PY" >&2
  exit 2
fi

echo "=== LAB PYTHON SIGSEGV PROBE ==="
date --iso-8601=seconds || true
echo "python=$PY"

echo
echo "=== HOST / VIRTUALIZATION ==="
uname -a || true
cat /etc/os-release || true
systemd-detect-virt || true
free -h || true
df -h / || true
lscpu | sed -n '1,35p' || true

echo
echo "=== PYTHON RUNTIME ==="
"$PY" - <<'PY'
import importlib.metadata as md
import platform
import sys

print("executable", sys.executable)
print("version", sys.version.replace("\n", " "))
print("platform", platform.platform())
for package in (
    "mcp",
    "mcp-types",
    "pydantic",
    "pydantic-core",
    "starlette",
    "httpx2",
    "cryptography",
    "cffi",
    "rpds-py",
):
    try:
        print(package, md.version(package))
    except md.PackageNotFoundError:
        print(package, "<missing>")
PY

echo
echo "=== PYTHON MODULE ORIGINS / SHADOWING ==="
"$PY" - <<'PY'
import importlib.util
import os
import sys

print("cwd", os.getcwd())
print("PYTHONPATH", os.environ.get("PYTHONPATH", "<unset>"))
for index, entry in enumerate(sys.path):
    print(f"sys.path[{index}]={entry!r}")

for name in (
    "datetime",
    "typing",
    "types",
    "enum",
    "json",
    "inspect",
    "pathlib",
    "uuid",
    "asyncio",
    "ssl",
    "socket",
    "logging",
    "email",
    "http",
):
    spec = importlib.util.find_spec(name)
    if spec is None:
        print(f"ORIGIN {name}: <not found>")
        continue
    print(
        f"ORIGIN {name}: origin={spec.origin!r} "
        f"locations={list(spec.submodule_search_locations or [])!r}"
    )
PY

echo "--- suspicious stdlib-name files near current working directory ---"
find . -maxdepth 3 \( -type f -o -type d \) \
  \( -name 'datetime.py' -o -name 'datetime' \
     -o -name 'typing.py' -o -name 'typing' \
     -o -name 'types.py' -o -name 'types' \
     -o -name 'enum.py' -o -name 'enum' \
     -o -name 'json.py' -o -name 'json' \
     -o -name 'inspect.py' -o -name 'inspect' \
     -o -name 'pathlib.py' -o -name 'pathlib' \
     -o -name 'uuid.py' -o -name 'uuid' \) \
  -print 2>/dev/null | head -n 100 || true

readlink -f "$PY" || true
ldd "$(readlink -f "$PY")" || true
"$PY" -m pip check || true

echo
echo "=== UBUNTU PYTHON PACKAGE INTEGRITY ==="
dpkg-query -W -f='${Package} ${Version}\n'   python3.12 python3.12-minimal libpython3.12-minimal libpython3.12-stdlib 2>&1 || true
dpkg -V python3.12 python3.12-minimal libpython3.12-minimal libpython3.12-stdlib 2>&1 || true

echo
echo "=== RECENT KERNEL FAULT EVIDENCE ==="
journalctl -k --no-pager --since="-6 hours" 2>/dev/null   | grep -Eai 'segfault|general protection|mce|machine check|hardware error|edac|memory failure|i/o error|blk_update_request|nvme.*(error|fail)|ext4.*(error|corrupt)|xfs.*(error|corrupt)'   | tail -n 200 || true

run_import_stress() {
  local module="$1"
  local count="$2"
  local prefix="$3"
  local i rc

  echo "=== TEST: $prefix$module ($count fresh processes) ==="
  for i in $(seq 1 "$count"); do
    "$PY" -X faulthandler -c "import importlib; importlib.import_module('$module')"       >"/tmp/runner-mcp-probe.out" 2>"/tmp/runner-mcp-probe.err"
    rc=$?
    if [[ "$rc" -ne 0 ]]; then
      echo "FAIL: $prefix$module iteration=$i rc=$rc"
      cat /tmp/runner-mcp-probe.out || true
      cat /tmp/runner-mcp-probe.err || true
      return "$rc"
    fi
  done
  echo "PASS: $prefix$module $count/$count"
}

echo
echo "=== CONTROL IMPORT STRESS ==="
CONTROL_FAILED=0
for module in json hashlib ssl sqlite3; do
  run_import_stress "$module" "$ITERATIONS" "" || CONTROL_FAILED=$?
done

echo
echo "=== MCP CRASH-BOUNDARY STRESS ==="
MCP_FAILED=0
for module in   mcp.server   mcp.server.mcpserver.utilities.func_metadata
do
  run_import_stress "$module" "$ITERATIONS" "" || MCP_FAILED=$?
done

echo
echo "=== PER-VCPU MCP STRESS ==="
CPU_FAILURES=0
if command -v taskset >/dev/null 2>&1; then
  CPU_COUNT="$(nproc)"
  for cpu in $(seq 0 $((CPU_COUNT - 1))); do
    for module in       mcp.server       mcp.server.mcpserver.utilities.func_metadata
    do
      echo "--- cpu=$cpu module=$module ---"
      for i in $(seq 1 "$PER_CPU_ITERATIONS"); do
        taskset -c "$cpu" "$PY" -X faulthandler -c           "import importlib; importlib.import_module('$module')"           >"/tmp/runner-mcp-probe.out" 2>"/tmp/runner-mcp-probe.err"
        rc=$?
        if [[ "$rc" -ne 0 ]]; then
          echo "FAIL: cpu=$cpu module=$module iteration=$i rc=$rc"
          cat /tmp/runner-mcp-probe.err || true
          CPU_FAILURES=$((CPU_FAILURES + 1))
          break
        fi
      done
    done
  done
else
  echo "SKIP: taskset not available"
fi

echo
echo "=== POST-STRESS KERNEL FAULT EVIDENCE ==="
journalctl -k --no-pager --since="-30 minutes" 2>/dev/null   | grep -Eai 'segfault|general protection|mce|machine check|hardware error|edac|memory failure|i/o error|blk_update_request|nvme.*(error|fail)|ext4.*(error|corrupt)|xfs.*(error|corrupt)'   | tail -n 200 || true

echo
echo "=== SUMMARY ==="
echo "control_failed_rc=$CONTROL_FAILED"
echo "mcp_failed_rc=$MCP_FAILED"
echo "per_cpu_failures=$CPU_FAILURES"

if [[ "$CONTROL_FAILED" -ne 0 || "$MCP_FAILED" -ne 0 || "$CPU_FAILURES" -ne 0 ]]; then
  exit 1
fi

echo "PASS: no failures observed in bounded probe"
