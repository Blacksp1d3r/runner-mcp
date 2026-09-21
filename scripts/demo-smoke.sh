#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_ROOT="$(mktemp -d)"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$REPO_ROOT/.venv"
  rm -rf "$DEMO_ROOT"
}
trap cleanup EXIT

export HOME="$DEMO_ROOT/home"
export RUNNER_MCP_INSTALL_ROOT="$HOME/.local/share/runner-mcp"
export RUNNER_MCP_BIN_DIR="$HOME/.local/bin"
export PATH="$RUNNER_MCP_BIN_DIR:$PATH"
mkdir -p "$HOME"

cd "$REPO_ROOT"
./install.sh

python3 -m venv --copies .venv
.venv/bin/python -m pip install --disable-pip-version-check -e '.[dev]'

printf '\n%s\n%s\n%s\n%s\n\n\n\n\n\n\nYES\n' \
  "demo" \
  "Runner MCP demo" \
  "Blacksp1d3r/runner-mcp" \
  "$REPO_ROOT" \
  | runner-mcp setup

runner-mcp doctor
runner-mcp status
runner-mcp guide

runner-mcp test-profile add demo unit --preset pytest
runner-mcp test-profile list demo
runner-mcp doctor

runner-mcp emergency-stop on
runner-mcp emergency-stop status
printf 'UNLOCK\n' | runner-mcp emergency-stop off
runner-mcp emergency-stop status

runner-mcp serve --host 127.0.0.1 --port 8000 >"$DEMO_ROOT/server.log" 2>&1 &
SERVER_PID="$!"

python3 - <<'PY'
import json
import time
import urllib.request

deadline = time.monotonic() + 20
while True:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=2) as response:
            payload = json.loads(response.read())
        if payload.get("status") != "ok":
            raise SystemExit("unexpected health payload")
        break
    except Exception:
        if time.monotonic() >= deadline:
            raise
        time.sleep(0.25)
PY

kill "$SERVER_PID"
wait "$SERVER_PID" || true
SERVER_PID=""

echo "Runner MCP clean demo smoke test passed."
