# Runtime State Ownership

This document defines which files belong to the repository and which files belong to the Raspberry Pi runtime.

## Repository-managed assets

The repository owns files that should be identical before shop-specific setup starts:

- application code in `src/`
- templates and static assets in `src/templates/` and `src/static/`
- build and packaging files such as `api_server.spec`
- schema files such as `src/token_db_init.sql`
- deployment scripts and helper scripts
- example runtime files under `runtime/examples/`
- bootstrap scaffolding under `runtime/bootstrap/`
- documentation under `README.md`, `README-technical.md`, and `docs/`

## Pi-managed runtime state

The Pi owns mutable shop-specific state that changes during normal operation.

Typical Linux locations:
- `/var/lib/package-shop/shop_info.json`
- `/var/lib/package-shop/license.json`
- `/var/lib/package-shop/packets.db`
- `/var/lib/package-shop/token_db.sqlite`
- `/var/log/package-shop/*`
- `/run/package-shop/*`

These files should not be committed to Git.

## Deployment rule

Normal code deployments should update code and static assets only. They should not overwrite existing shop runtime state unless an explicit migration step is being run.

Preserve on update:
- `shop_info.json`
- `license.json`
- `packets.db`
- `token_db.sqlite`

Seed on first install only if missing:
- `shop_info.json`
- any future cached license or cloud config files

## Local development rule

Development should use env-var overrides instead of real production paths.

Supported overrides:
- `PACKAGE_SHOP_DATA_DIR`
- `PACKAGE_SHOP_CONFIG_DIR`
- `PACKAGE_SHOP_LOG_DIR`
- `PACKAGE_SHOP_RUN_DIR`

Recommended pattern:
- keep code in the repository
- keep mutable dev runtime files in an ignored folder such as `.runtime/dev/`
- seed that folder from `runtime/examples/`

## Why this matters

This separation keeps live shop state out of source control, makes deployments safer, and prepares the codebase for later cloud-managed licensing, configuration sync, and remote rollout without breaking the local Pi runtime model.