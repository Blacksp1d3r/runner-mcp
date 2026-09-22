#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${RUNNER_MCP_PYTHON:-python3}"
INSTALL_ROOT="${RUNNER_MCP_INSTALL_ROOT:-$HOME/.local/share/runner-mcp}"
BIN_DIR="${RUNNER_MCP_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="$INSTALL_ROOT/venv"

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

if [[ -L "$INSTALL_ROOT" ]]; then
  echo "Error: install directory must not be a symlink." >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
chmod 700 "$INSTALL_ROOT"

echo "Creating isolated Python environment..."
if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
  echo "Error: could not create the Python virtual environment." >&2
  echo "Install venv support for this Python 3.12+ interpreter (for Debian/Ubuntu, typically python3-venv)." >&2
  exit 1
fi

echo "Installing Runner MCP..."
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check "$ROOT_DIR"

if ! "$VENV_DIR/bin/runner-mcp" --help >/dev/null 2>&1; then
  echo "Error: Runner MCP installation self-check failed." >&2
  exit 1
fi

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
