# Local Development Environment

This project supports a local development runtime that is logically equivalent to the Raspberry Pi layout without requiring real Linux system paths.

## Goal

Run the application locally while keeping mutable runtime files out of the repository and away from production shop state.

## Recommended local layout

Use an ignored local runtime folder such as:

```text
.runtime/
└── dev/
    ├── data/
    ├── config/
    ├── log/
    └── run/
```

## Environment variables

Point the application at those directories with:

```powershell
$env:PACKAGE_SHOP_DATA_DIR = "$PWD/.runtime/dev/data"
$env:PACKAGE_SHOP_CONFIG_DIR = "$PWD/.runtime/dev/config"
$env:PACKAGE_SHOP_LOG_DIR = "$PWD/.runtime/dev/log"
$env:PACKAGE_SHOP_RUN_DIR = "$PWD/.runtime/dev/run"
```

On Linux:

```bash
export PACKAGE_SHOP_DATA_DIR="$PWD/.runtime/dev/data"
export PACKAGE_SHOP_CONFIG_DIR="$PWD/.runtime/dev/config"
export PACKAGE_SHOP_LOG_DIR="$PWD/.runtime/dev/log"
export PACKAGE_SHOP_RUN_DIR="$PWD/.runtime/dev/run"
```

## Seed files

Copy example files from `runtime/examples/` into the local runtime data directory before first run.

Suggested minimum seed:
- `shop_info.example.json` -> `.runtime/dev/data/shop_info.json`

`license.json` and SQLite files can be created by the application when needed.

## Run the app

From the repository root:

```bash
python src/api_server.py
```

Helper launchers are also available:
- `scripts/dev_run.ps1` for PowerShell
- `scripts/dev_run.sh` for POSIX shells

## Hardware-specific testing

Scanner device access, CUPS, printer devices, and Raspberry Pi service behavior should be validated on a staging Pi, not only on a workstation development environment.