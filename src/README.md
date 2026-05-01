## Edge Runtime Notes

This directory contains the Raspberry Pi edge runtime. In production, mutable state is stored outside the repository and the code reads it through the path helpers in `paths.py`.

## Runtime directories

Default runtime directories:
- Linux production: `/var/lib/package-shop`, `/etc/package-shop`, `/var/log/package-shop`, `/run/package-shop`
- Windows development: `%PROGRAMDATA%\PackageShop` for data/config/log and `%TEMP%` for runtime files

Development overrides:
- `PACKAGE_SHOP_DATA_DIR`
- `PACKAGE_SHOP_CONFIG_DIR`
- `PACKAGE_SHOP_LOG_DIR`
- `PACKAGE_SHOP_RUN_DIR`

Common runtime files on Linux:
- `/var/lib/package-shop/shop_info.json`
- `/var/lib/package-shop/license.json`
- `/var/lib/package-shop/packets.db`
- `/var/lib/package-shop/token_db.sqlite`

These files are persistent shop state and should not be committed to Git.

## Networking overview

- Hotspot/AP only: the Pi runs as a dedicated hotspot for staff devices.
- Wi-Fi client management inside the app has been removed.
- AP configuration is handled at the system level, not by the Flask app.

## Licensing overview

The local licensing flow is implemented by `license_manager.py` and exposed through the staff dashboard.

- Tokens are shop-bound and non-reusable.
- `license.json` is created or normalized on first run.
- `token_db.sqlite` tracks token usage.
- The staff dashboard can activate new tokens locally.

Generate a token:

```bash
python src/generate_token.py SHOP07 3
```

Redeem a token:
- Open `/staff`
- Enter the token
- Activate it to extend the local license expiry

## Running locally

Run the API from the repository root:

```bash
python src/api_server.py
```

For local development, point the app at a dev runtime folder with the `PACKAGE_SHOP_*` environment variables instead of using production paths.

## Offline time policy

For permanently offline sites, the Pi uses hardware RTC and local system time only.

- At boot, `rtc-init.service` binds DS1307/DS3231 on `i2c-1` and loads system time from RTC.
- Periodic RTC writes can persist updated system time.
- Network time sync can remain disabled for offline-only sites.
