#!/bin/sh
set -eu

APP_NAME="package-shop"
DATA_DIR="${PACKAGE_SHOP_DATA_DIR:-/var/lib/$APP_NAME}"
CONFIG_DIR="${PACKAGE_SHOP_CONFIG_DIR:-/etc/$APP_NAME}"
LOG_DIR="${PACKAGE_SHOP_LOG_DIR:-/var/log/$APP_NAME}"
RUN_DIR="${PACKAGE_SHOP_RUN_DIR:-/run/$APP_NAME}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
EXAMPLES_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../examples" && pwd)

mkdir -p "$DATA_DIR" "$CONFIG_DIR" "$LOG_DIR" "$RUN_DIR"

if [ ! -f "$DATA_DIR/shop_info.json" ]; then
    cp "$EXAMPLES_DIR/shop_info.example.json" "$DATA_DIR/shop_info.json"
    echo "Seeded $DATA_DIR/shop_info.json"
fi

echo "Runtime directories ready:"
echo "  data   $DATA_DIR"
echo "  config $CONFIG_DIR"
echo "  log    $LOG_DIR"
echo "  run    $RUN_DIR"
echo "Review seeded files before starting production services."