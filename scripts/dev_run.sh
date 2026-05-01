#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
RUNTIME_ROOT="$REPO_ROOT/.runtime/dev"
DATA_DIR="$RUNTIME_ROOT/data"
CONFIG_DIR="$RUNTIME_ROOT/config"
LOG_DIR="$RUNTIME_ROOT/log"
RUN_DIR="$RUNTIME_ROOT/run"

mkdir -p "$DATA_DIR" "$CONFIG_DIR" "$LOG_DIR" "$RUN_DIR"

if [ -f "$REPO_ROOT/runtime/examples/shop_info.example.json" ] && [ ! -f "$DATA_DIR/shop_info.json" ]; then
    cp "$REPO_ROOT/runtime/examples/shop_info.example.json" "$DATA_DIR/shop_info.json"
fi

export PACKAGE_SHOP_DATA_DIR="$DATA_DIR"
export PACKAGE_SHOP_CONFIG_DIR="$CONFIG_DIR"
export PACKAGE_SHOP_LOG_DIR="$LOG_DIR"
export PACKAGE_SHOP_RUN_DIR="$RUN_DIR"

if [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$REPO_ROOT/venv/bin/activate"
fi

cd "$REPO_ROOT"
python src/api_server.py