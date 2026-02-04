## Networking Overview (Hotspot‑Only)

- Hotspot/AP only: the Pi runs as a dedicated hotspot for staff devices. Client Wi‑Fi scanning/connecting features have been removed.
- Wi‑Fi scripts removed: `wifi_manager.py` and `scripts/wifi_status_watcher.py` are no longer part of the app.

Deployment and scaling:
- Base image: we use a base Raspberry Pi OS image that already contains all system-level setup (NetworkManager, AP config, polkit rules if used, services), so a new device works out of the box.
- Code updates: operational scaling is done by cloning the base image to new Pis, booting, and pulling the latest app code from Git on the clone. This “clone then git pull” procedure is the current standard.

Related code paths:
- Wi‑Fi client management and status watcher have been retired in favor of a simpler hotspot‑only setup.

Notes:
- AP/hotspot configuration is handled at the system level. No client Wi‑Fi configuration is needed within the app.

## Staff Wi‑Fi Setup

Wi‑Fi client features have been removed. The app operates over the device’s hotspot only; staff connect to the hotspot to use the dashboard and tools.
# Simplified License System + Staff Dashboard Integration

This adds a small offline license system to the Packet Shop app with:

- Shop-bound short tokens (e.g., `SHOP07-3M-X9A7-Q2F1`)
- One central SQLite token DB (`token_db.sqlite`)
- Default 1-month license loaded automatically on first run
- A staff dashboard to view the current expiry and activate a token

## Folder layout

```
src/
 ├── api_server.py              # Flask app (adds /staff and /activate)
 ├── generate_token.py          # CLI to mint tokens and register them in token DB
 ├── license_manager.py         # License + token utilities
 ├── token_db_init.sql          # Schema for token_db.sqlite
 ├── shop_info.json             # { "shop_id": "SHOP07" }
 ├── license.json               # { "expiry": "YYYY-MM-DD" }
 ├── templates/
 │    └── staff_dashboard.html  # Minimal UI for staff license activation
 └── static/                    # (optional CSS)
```

## Token design

Format: `SHOP07-3M-X9A7-Q2F1`

- parts: `<shop_id>-<months>M-<rand4>-<check4>`
- `check4 = first 4 hex of SHA1(shop_id + rand4 + SECRET_SALT)`
- `SECRET_SALT = "SALT1234"`

Properties:
- Non-reusable (marked `used=1` in `used_tokens` table)
- Shop-locked via checksum validation
- Typing-friendly

## Database schema

`token_db_init.sql`:

```sql
CREATE TABLE IF NOT EXISTS used_tokens (
    token_id TEXT PRIMARY KEY,
    shop_id TEXT NOT NULL,
    issued_date DATE,
    used BOOLEAN DEFAULT 0,
    used_at DATETIME
);
```

## How to run the API

1. Activate your Python environment, ensure Flask is available.
2. From `src/`, run:

```bash
python api_server.py
```

The server ensures the token DB exists and prints:

```
[License] token_db.sqlite checked/created.
```

Visit http://localhost:5000/staff to view the staff dashboard.

## Default 1-month license

On first run, `license.json` is created (or normalized) and set to at least `today + 30 days`.
The current expiry is shown on `/staff`.

## Generate and redeem tokens

### 1) Generate a token (admin/owner)

```bash
python generate_token.py SHOP07 3
```

- Outputs a token like `SHOP07-3M-AB12-9F0C`
- Inserts a row into `token_db.sqlite` with `used=0`

### 2) Redeem a token (staff)

- Open http://localhost:5000/staff
- Enter the token and click "Activate Token"
- If valid and not used, the license is extended by N months (30-day months)
- The token is then marked as used

## Implementation details

- Paths are relative to the directory of the scripts (`src/`)
- JSON files: `shop_info.json` for shop ID and runtime settings, `license.json` for expiry
- Date format: `YYYY-MM-DD`
- Month extension uses 30-day months; extension is from the later of today or the current expiry
- Flask returns HTML by default; `/activate` also supports JSON requests

## Notes

- You can edit `shop_info.json` to change the current `shop_id`, `scanner_path`, or `printer_device`.
- If you change `SECRET_SALT` in `license_manager.py`, regenerate tokens accordingly.

## Offline RTC Time Policy (No Internet)

For permanently offline sites, the Pi uses the hardware RTC and local system time only:

- At boot, `rtc-init.service` binds DS1307/DS3231 on `i2c-1` (0x68) and sets system time from RTC.
- Periodically (every 15 minutes), `rtc-write.timer` writes system time back to RTC.
- On shutdown, `rtc-save.service` writes system time to RTC to persist changes.
- Network time sync is disabled; `fake-hwclock` is removed/masked.

Adjust bus/address if wiring differs: change `i2c-1` in units and override `RTC_ADDR` to the correct address.
