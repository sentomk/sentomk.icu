#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python not found in PATH. Please install Python first." >&2
  exit 1
fi

echo "Starting static server at http://localhost:${PORT}"
exec "$PYTHON_CMD" -m http.server "$PORT"
