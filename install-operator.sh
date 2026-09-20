#!/usr/bin/env bash
set -euo pipefail

SERVICE_USER="${1:-}"
if [[ -z "$SERVICE_USER" ]]; then
  echo "Usage: ./install-operator.sh SERVICE_USER" >&2
  exit 2
fi

if [[ ! "$SERVICE_USER" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]]; then
  echo "Error: invalid service-user name." >&2
  exit 2
fi

SERVICE_HOME="$(getent passwd "$SERVICE_USER" | cut -d: -f6)"
if [[ -z "$SERVICE_HOME" ]]; then
  echo "Error: service user does not exist." >&2
  exit 2
fi

RUNNER_BIN="${RUNNER_MCP_SERVICE_BIN:-$SERVICE_HOME/.local/bin/runner-mcp}"
CONFIG_DIR="${RUNNER_MCP_SERVICE_CONFIG_DIR:-$SERVICE_HOME/.config/runner-mcp}"
BIN_DIR="${RUNNER_MCP_OPERATOR_BIN_DIR:-$HOME/.local/bin}"
WRAPPER="$BIN_DIR/runner-mcp"

service_test() {
  if [[ "$(id -un)" == "$SERVICE_USER" ]]; then
    test "$@"
  else
    sudo -u "$SERVICE_USER" -- test "$@"
  fi
}

if ! service_test -x "$RUNNER_BIN"; then
  echo "Error: Runner MCP executable was not found for the service user." >&2
  exit 2
fi

if ! service_test -d "$CONFIG_DIR"; then
  echo "Error: Runner MCP private configuration was not found for the service user." >&2
  exit 2
fi

if [[ -L "$BIN_DIR" ]]; then
  echo "Error: operator bin directory must not be a symlink." >&2
  exit 2
fi

mkdir -p "$BIN_DIR"

if [[ -e "$WRAPPER" && ! -f "$WRAPPER" ]]; then
  echo "Error: operator command path exists and is not a regular file." >&2
  exit 2
fi

if [[ -e "$WRAPPER" ]]; then
  if ! grep -q '^# Runner MCP operator wrapper$' "$WRAPPER" 2>/dev/null; then
    echo "Error: $WRAPPER already exists and was not created by this installer." >&2
    exit 2
  fi
fi

{
  echo '#!/usr/bin/env bash'
  echo '# Runner MCP operator wrapper'
  echo 'set -euo pipefail'
  printf 'SERVICE_USER=%q\n' "$SERVICE_USER"
  printf 'RUNNER_BIN=%q\n' "$RUNNER_BIN"
  printf 'CONFIG_DIR=%q\n' "$CONFIG_DIR"
  cat <<'EOF'
if [[ "$(id -un)" == "$SERVICE_USER" ]]; then
  exec "$RUNNER_BIN" --config-dir "$CONFIG_DIR" "$@"
fi
exec sudo -u "$SERVICE_USER" -- "$RUNNER_BIN" --config-dir "$CONFIG_DIR" "$@"
EOF
} > "$WRAPPER"

chmod 700 "$WRAPPER"

echo "Runner MCP operator command installed."
echo "Command: $WRAPPER"
echo
echo "This wrapper does not copy Runner MCP secrets."
echo "It delegates commands to the configured service account through sudo."
echo "Next: runner-mcp guide"
