#!/usr/bin/env bash
set -euo pipefail

# Build both api_server and scanner_listener using the combined spec
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Clean previous outputs
[ -d build ] && rm -rf build
[ -d dist ] && rm -rf dist

# Prefer venv's PyInstaller if available (.venv, venv, .env, env)
PI=""
for VENV in ".venv" "venv" ".env" "env"; do
  if [ -x "$ROOT/$VENV/bin/pyinstaller" ]; then
    PI="$ROOT/$VENV/bin/pyinstaller"
    break
  fi
done

# Fallback to system pyinstaller if not found in venv
if [ -z "$PI" ]; then
  if command -v pyinstaller >/dev/null 2>&1; then
    PI="pyinstaller"
  else
    echo "PyInstaller not found. Please activate your venv or install pyinstaller."
    echo "Examples:"
    echo "  python3 -m venv .venv && source .venv/bin/activate && pip install pyinstaller"
    echo "  source /home/admin/package_shop/venv/bin/activate    # if your venv is named 'venv'"
    exit 1
  fi
fi

"$PI" --noconfirm api_server.spec

echo
echo "Build complete. Outputs:"
ls -la dist || true

echo "API binary:      dist/api_server/api_server"
echo "Scanner binary:  dist/scanner_listener/scanner_listener"
