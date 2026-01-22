#!/usr/bin/env bash
set -euo pipefail

# Build both api_server and scanner_listener using the combined spec
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Clean previous outputs
[ -d build ] && rm -rf build
[ -d dist ] && rm -rf dist

# Prefer venv's PyInstaller if available
PI="$ROOT/.venv/bin/pyinstaller"
if [ ! -x "$PI" ]; then
  PI="pyinstaller"
fi

"$PI" --noconfirm api_server.spec

echo
echo "Build complete. Outputs:"
ls -la dist || true

echo "API binary:      dist/api_server/api_server"
echo "Scanner binary:  dist/scanner_listener/scanner_listener"
