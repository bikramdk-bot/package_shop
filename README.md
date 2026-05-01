# Package Shop

Package Shop is a fully offline edge system for parcel intake and pickup in kiosk-style package shops. It runs locally on-site, with no required cloud dependency, and combines a customer-facing lookup flow, a staff dashboard, local parcel storage, barcode and scanner handling, label printing, and Raspberry Pi-friendly deployment.

This project is designed for privacy-sensitive, GDPR-focused deployments: operational data stays on the local device or local shop network, which supports data minimization and avoids routine transfer of parcel and customer workflow data to external services.

## Project overview

The system is designed for environments where a small shop needs to receive parcels, identify them quickly, and hand them out with minimal staff friction. It supports both customer self-service and staff-operated workflows.

Core capabilities:
- Customer parcel lookup by provider and parcel digits
- QR-assisted lookup flows where supported
- Clash handling that escalates from 4 digits to longer identifiers
- Staff dashboard for collection and parcel status tracking
- Local SQLite-backed storage
- Scanner listener and label-printing support
- Raspberry Pi deployment with offline-friendly operation

## Main application pieces

- `src/api_server.py`: main Flask server, routing, lookup logic, and page endpoints
- `src/lookup.py`: parcel database operations and matching helpers
- `src/scanner_listener.py`: hardware scanner listener for barcode ingestion
- `src/templates/`: customer, staff, dashboard, and queue pages
- `src/static/`: styles, translations, and static assets
- `src/license_manager.py`: local licensing and device validation support

## How the system works

1. Parcels are inserted into the local database, usually through scanner-assisted flows.
2. Customers identify a parcel from the kiosk, either by digits or QR flow.
3. If multiple parcels share the same short digits, the system escalates to longer variants until it can resolve the match or asks staff to help.
4. Staff monitor the live queue and complete handover from the dashboard.

## Running locally

The main application entrypoint is:

```bash
python src/api_server.py
```

Helper scripts are also available:
- `run_api.sh`
- `run_api.bat`

## Documentation

- `README-technical.md`: Raspberry Pi setup, runtime directories, scanner and printer integration, hotspot and RTC configuration, and reliability hardening
- `src/README.md`: edge-runtime notes, licensing behavior, and local development path overrides
- `docs/runtime-state.md`: source of truth for repository-managed files versus Pi-managed runtime state
- `docs/dev-environment.md`: local development setup using env-var-based runtime directories

## Repository layout

```text
.
├── src/                Main edge application code
├── scripts/            Deployment and system helper scripts
├── runtime/            Runtime examples and bootstrap scaffolding
├── docs/               Deployment and runtime-state documentation
├── db/                 Database-related assets and certs
├── requirements.txt    Python dependencies
├── api_server.spec     PyInstaller build definition
├── run_api.sh          Linux launcher
└── run_api.bat         Windows launcher
```

## Deployment shape

The project is commonly deployed on Raspberry Pi hardware as a local kiosk system with attached scanner and printer hardware. The codebase itself is still organized so the application logic, templates, and data handling can be developed and maintained separately from the device-specific setup.

## Runtime state model

Production runtime state is external to the repository. On Linux, the application defaults to:
- `/var/lib/package-shop` for mutable application data such as `shop_info.json`, `license.json`, and SQLite files
- `/etc/package-shop` for configuration overrides when needed
- `/var/log/package-shop` for logs
- `/run/package-shop` for transient runtime files

For local development, these paths can be overridden with `PACKAGE_SHOP_DATA_DIR`, `PACKAGE_SHOP_CONFIG_DIR`, `PACKAGE_SHOP_LOG_DIR`, and `PACKAGE_SHOP_RUN_DIR`.

If you need hardware setup, service configuration, or operational Pi details, start with `README-technical.md`.