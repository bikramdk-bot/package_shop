# Pi Bootstrap Scaffolding

This directory contains scaffolding for fresh Raspberry Pi provisioning.

## Current scope

`bootstrap_pi.sh` creates the expected runtime directories and seeds `shop_info.json` if it is missing.

It does not yet:
- install system packages
- configure systemd services
- set file ownership or permissions
- migrate existing runtime data

Those steps should be added deliberately once the runtime-state model and deployment flow are finalized.

## Usage

Run on a Pi or Linux environment:

```bash
sh runtime/bootstrap/bootstrap_pi.sh
```

Optional overrides:
- `PACKAGE_SHOP_DATA_DIR`
- `PACKAGE_SHOP_CONFIG_DIR`
- `PACKAGE_SHOP_LOG_DIR`
- `PACKAGE_SHOP_RUN_DIR`