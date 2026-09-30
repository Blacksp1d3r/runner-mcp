#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${RUNNER_MCP_PYTHON:-python3}"
INSTALL_ROOT="${RUNNER_MCP_INSTALL_ROOT:-$HOME/.local/share/runner-mcp}"
BIN_DIR="${RUNNER_MCP_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="$INSTALL_ROOT/venv"
PIP_INSTALL_TIMEOUT_SECONDS="${RUNNER_MCP_PIP_INSTALL_TIMEOUT_SECONDS:-600}"
RUNTIME_SMOKE_TIMEOUT_SECONDS="${RUNNER_MCP_RUNTIME_SMOKE_TIMEOUT_SECONDS:-30}"

echo "Runner MCP installer"
echo

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: Python 3.12 or newer is required." >&2
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
then
  echo "Error: Python 3.12 or newer is required." >&2
  exit 1
fi

TIMEOUT_BIN="$(command -v timeout || true)"
if [[ -z "$TIMEOUT_BIN" ]]; then
  echo "Error: the 'timeout' utility is required for bounded installation checks." >&2
  echo "Install GNU coreutils (or provide a compatible timeout utility) before retrying." >&2
  exit 1
fi

validate_timeout_seconds() {
  local name="$1"
  local value="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]] || (( value < 1 || value > 3600 )); then
    echo "Error: $name must be an integer between 1 and 3600 seconds." >&2
    exit 1
  fi
}

report_bounded_failure() {
  local stage="$1"
  local rc="$2"
  local seconds="$3"

  case "$rc" in
    124)
      echo "Error: $stage timed out after ${seconds}s (rc=124)." >&2
      ;;
    137)
      echo "Error: $stage was force-killed (rc=137), possibly after exceeding its timeout." >&2
      ;;
    139)
      echo "Error: $stage crashed with SIGSEGV (rc=139)." >&2
      echo "The Python runtime or host may be corrupted, incompatible, or unstable." >&2
      ;;
    *)
      echo "Error: $stage failed (rc=$rc)." >&2
      ;;
  esac
}

validate_timeout_seconds "RUNNER_MCP_PIP_INSTALL_TIMEOUT_SECONDS" "$PIP_INSTALL_TIMEOUT_SECONDS"
validate_timeout_seconds "RUNNER_MCP_RUNTIME_SMOKE_TIMEOUT_SECONDS" "$RUNTIME_SMOKE_TIMEOUT_SECONDS"

if [[ -L "$INSTALL_ROOT" ]]; then
  echo "Error: install directory must not be a symlink." >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
chmod 700 "$INSTALL_ROOT"

echo "Checking Python venv support..."
if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  echo "Error: Python venv support is required." >&2
  echo "Install venv support for this Python 3.12+ interpreter (for Debian/Ubuntu, typically python3-venv)." >&2
  exit 1
fi

echo "Creating isolated Python environment..."
if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
  echo "Error: could not create the Python virtual environment." >&2
  echo "Install venv support for this Python 3.12+ interpreter (for Debian/Ubuntu, typically python3-venv)." >&2
  exit 1
fi

echo "Checking isolated installer runtime..."
PIP_VERSION_OUTPUT="$("$VENV_DIR/bin/python" -m pip --version 2>/dev/null || true)"
if [[ ! "$PIP_VERSION_OUTPUT" =~ ^pip[[:space:]]+([0-9]+)\.([0-9]+)(\.([0-9]+))?([[:space:]]|$) ]]; then
  echo "Error: pip is unavailable or its version could not be verified in the isolated Python environment." >&2
  exit 1
fi
PIP_MAJOR="${BASH_REMATCH[1]}"
PIP_MINOR="${BASH_REMATCH[2]}"
if (( PIP_MAJOR < 23 || (PIP_MAJOR == 23 && PIP_MINOR < 2) )); then
  echo "Error: pip 23.2 or newer is required in the isolated Python environment." >&2
  exit 1
fi

echo "Installing Runner MCP (bounded to ${PIP_INSTALL_TIMEOUT_SECONDS}s)..."
set +e
"$TIMEOUT_BIN" --signal=TERM --kill-after=10s "${PIP_INSTALL_TIMEOUT_SECONDS}s" \
  "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --no-input "$ROOT_DIR"
PIP_INSTALL_RC=$?
set -e
if (( PIP_INSTALL_RC != 0 )); then
  report_bounded_failure "Runner MCP dependency/package installation" "$PIP_INSTALL_RC" "$PIP_INSTALL_TIMEOUT_SECONDS"
  echo "Do not loop reinstall. Do not enable Runner MCP autostart until runtime/host integrity is verified." >&2
  exit 1
fi

echo "Stress-verifying installed Python runtime..."
for attempt in {1..32}; do
  set +e
  PYTHONPYCACHEPREFIX="$INSTALL_ROOT/.integrity-smoke-pycache" \
    "$TIMEOUT_BIN" --signal=TERM --kill-after=10s "${RUNTIME_SMOKE_TIMEOUT_SECONDS}s" \
    "$VENV_DIR/bin/python" -B -X faulthandler - <<'PY'
import importlib

for module_name in (
    "runner_mcp",
    "runner_mcp.cli",
    "mcp",
    "pydantic",
    "starlette",
    "uvicorn",
    "setuptools.build_meta",
):
    importlib.import_module(module_name)
PY
  IMPORT_STRESS_RC=$?
  set -e
  if (( IMPORT_STRESS_RC != 0 )); then
    report_bounded_failure "Runner MCP repeated import stress (attempt $attempt)" "$IMPORT_STRESS_RC" "$RUNTIME_SMOKE_TIMEOUT_SECONDS"
    echo "Error: Runner MCP installation integrity check failed during repeated import stress." >&2
    echo "The Python runtime may be incompatible, corrupted, or unstable." >&2
    echo "Do not loop reinstall. Do not enable Runner MCP autostart until runtime/host integrity is verified." >&2
    exit 1
  fi
done

for attempt in {1..8}; do
  set +e
  PYTHONDONTWRITEBYTECODE=1 \
    "$TIMEOUT_BIN" --signal=TERM --kill-after=10s "${RUNTIME_SMOKE_TIMEOUT_SECONDS}s" \
    "$VENV_DIR/bin/runner-mcp" --help >/dev/null 2>&1
  CLI_STRESS_RC=$?
  set -e
  if (( CLI_STRESS_RC != 0 )); then
    report_bounded_failure "Runner MCP CLI stress (attempt $attempt)" "$CLI_STRESS_RC" "$RUNTIME_SMOKE_TIMEOUT_SECONDS"
    echo "Error: Runner MCP installation self-check failed during repeated CLI stress." >&2
    echo "Do not enable Runner MCP autostart until runtime/host integrity is verified." >&2
    exit 1
  fi
done

ln -sfn "$VENV_DIR/bin/runner-mcp" "$BIN_DIR/runner-mcp"

echo
echo "Runner MCP was installed successfully."
echo "Command: $BIN_DIR/runner-mcp"
echo
echo "Next steps:"
echo "  1. runner-mcp setup"
echo "  2. runner-mcp doctor"
echo "  3. runner-mcp status"

case ":${PATH:-}:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo
    echo "Note: $BIN_DIR is not currently in PATH."
    echo "Add it to your shell PATH before using runner-mcp directly."
    ;;
esac
