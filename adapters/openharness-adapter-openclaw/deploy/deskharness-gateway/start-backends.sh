#!/usr/bin/env bash
# Start pair-server + bridge-server on the loopback ports expected by Caddyfile / nginx example.
# Run from any cwd; resolves paths relative to this script.
set -euo pipefail

# deploy/deskharness-gateway/ → adapter root is two levels up
ADAPTER_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ADAPTER_ROOT"

PAIR_PORT="${PAIR_PORT:-8790}"
BRIDGE_PORT="${BRIDGE_PORT:-8788}"
HOST="${HOST:-127.0.0.1}"

PY="${PYTHON:-python3}"
CLI="$ADAPTER_ROOT/openharness-adapter-openclaw.py"

if [[ ! -f "$CLI" ]]; then
	echo "Expected $CLI — run from a clone of OpenHarness with adapters/openharness-adapter-openclaw." >&2
	exit 1
fi

echo "Starting pair-server on ${HOST}:${PAIR_PORT} and bridge-server on ${HOST}:${BRIDGE_PORT}" >&2
echo "OPENCLAW_HTTP_URL=${OPENCLAW_HTTP_URL:-unset (bridge uses stub echo)}" >&2

"$PY" "$CLI" pair-server --host "$HOST" --port "$PAIR_PORT" &
PAIR_PID=$!

cleanup() {
	kill "$PAIR_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

exec "$PY" "$CLI" bridge-server --host "$HOST" --port "$BRIDGE_PORT" "$@"
