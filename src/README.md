## Networking Overview

- Wi‑Fi dongle: a dedicated USB Wi‑Fi dongle handles client Wi‑Fi. By default, `wlan0` runs the hotspot (AP) and `wlan1` (the dongle) connects to shop Wi‑Fi.
- Hotspot as initiator/fallback: the Pi boots with its hotspot up so staff devices can reach the app. The hotspot remains the fallback if client Wi‑Fi is unavailable.
- Manager modules: client Wi‑Fi and AP control logic lives in `wifi_manager.py` and a lightweight status writer in `scripts/wifi_status_watcher.py`.
- Behavior: scanning and connecting prefer NetworkManager (`nmcli`) on Linux; AP is paused only when needed (e.g., single interface setups), otherwise scans run concurrently when AP and client use separate interfaces.

Deployment and scaling:
- Base image: we use a base Raspberry Pi OS image that already contains all system-level setup (NetworkManager, AP config, polkit rules if used, services), so a new device works out of the box.
- Code updates: operational scaling is done by cloning the base image to new Pis, booting, and pulling the latest app code from Git on the clone. This “clone then git pull” procedure is the current standard.

Related code paths:
- `wifi_manager.py`: scanning networks, setting credentials, pausing/resuming hotspot, disconnecting client Wi‑Fi, and reporting combined status.
- `scripts/wifi_status_watcher.py`: writes a small `/home/pi/wifi_status.json` with the current client interface IPv4, updated every few seconds.

Notes:
- Interfaces are configurable via environment: `PSHOP_AP_IFACE` (default `wlan0`), `PSHOP_CLIENT_IFACE` (default `wlan1`).
- An optional AP watchdog service name can be set in `shop_info.json` as `ap_watchdog_service`; it will be stopped/started around scans and connects.

## Staff Wi‑Fi Setup

This app helps staff scan and connect the Pi to shop Wi‑Fi while using the Pi hotspot as a fallback.

What the app does:
- Temporarily pauses the hotspot (and stops `wifi_watchdog.service` + its timer) to improve scanning/connecting.
- Scans with `nmcli` and shows all visible networks (you can be connected and still see others).
- Connects using the correct security automatically:
    - WPA/WPA2 → `wpa-psk`
    - WPA3 → `sae`
    - Open → no password
- Resumes the hotspot and restarts the watchdog so the tablet reconnects.

UI controls (Staff Settings → Wi‑Fi):
- Scan Networks: pauses AP, scans, populates SSID list.
- Password field + Hidden SSID toggle.
- Connect: pauses AP, connects, then resumes AP.
- Pause AP / Resume AP: manual control if you need extra time.
- Disconnect: disconnects the current client Wi‑Fi (keeps AP intact).

Permissions (NetworkManager):
- If you see "Not authorized to control networking":
    1) Run as root, or
    2) Allow via polkit for users in `netdev` (recommended). Example rule `/etc/polkit-1/rules.d/10-nm.rules`:
         ```javascript
         polkit.addRule(function(action, subject) {
             var allowed = [
                 "org.freedesktop.NetworkManager.settings.modify.system",
                 "org.freedesktop.NetworkManager.network-control",
                 "org.freedesktop.NetworkManager.wifi.share.open",
                 "org.freedesktop.NetworkManager.wifi.share.protected"
             ];
             if (allowed.indexOf(action.id) >= 0 && subject.isInGroup("netdev")) {
                 return polkit.Result.YES;
             }
         });
         ```
         Then add your user to `netdev` and re-login.

Watchdog integration:
- Set the unit name in `shop_info.json` as `ap_watchdog_service` (e.g., `wifi_watchdog.service`). The app will stop/start both the service and its `.timer` around scanning/connecting.

Country code (one-time, improves scanning):
```bash
sudo raspi-config nonint do_wifi_country DK
sudo iw reg set DK
sudo sed -i 's/^country=.*/country=DK/' /etc/wpa_supplicant/wpa_supplicant.conf || true
grep -q '^country=' /etc/wpa_supplicant/wpa_supplicant.conf || echo 'country=DK' | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf >/dev/null
sudo systemctl restart NetworkManager
```

Notes:
- When AP is up on `wlan0`, scanning can be limited. The app handles pausing the AP for accurate scans.
- Hidden SSIDs: check the Hidden box if your SSID doesn’t appear in the list.
- WPA3 networks require devices/driver support; the app selects `sae` automatically when detected.
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
- JSON files: `shop_info.json` for shop ID, `license.json` for expiry
- Date format: `YYYY-MM-DD`
- Month extension uses 30-day months; extension is from the later of today or the current expiry
- Flask returns HTML by default; `/activate` also supports JSON requests

## Notes

- You can edit `shop_info.json` to change the current `shop_id`.
- If you change `SECRET_SALT` in `license_manager.py`, regenerate tokens accordingly.

## HTTPS via Nginx (Raspberry Pi)

This project can be secured with HTTPS by placing Nginx in front of Flask and terminating TLS on the Pi.

Steps:

1) Install Nginx on Raspberry Pi OS (Debian-based):

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

2) Generate a self-signed certificate (or install your CA-issued cert):

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /etc/nginx/ssl/packetshop.key \
  -out /etc/nginx/ssl/packetshop.crt \
  -subj "/C=DK/ST=Denmark/L=Copenhagen/O=PacketShop/OU=IT/CN=packetshop.local"
sudo chmod 600 /etc/nginx/ssl/packetshop.key
```

3) Configure Nginx to reverse proxy HTTPS → Flask (`localhost:5000`). Create `/etc/nginx/sites-available/packetshop`:

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/packetshop.crt;
    ssl_certificate_key /etc/nginx/ssl/packetshop.key;

    # Recommended SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Static files (optional)
    location /static/ {
        alias /home/pi/package_shop/src/static/;
        access_log off;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/packetshop /etc/nginx/sites-enabled/packetshop
sudo nginx -t
sudo systemctl reload nginx
```

4) Adjust Flask for reverse proxy:

- Already handled in `api_server.py` via `ProxyFix` and `PREFERRED_URL_SCHEME = 'https'`.
- Keep Flask listening on `0.0.0.0:5000` (HTTP). Nginx terminates TLS.

5) Connect tablets to `https://<PI-IP>`:

- Staff and customer devices should use the Pi address with HTTPS.
- Traffic is encrypted; Nginx forwards to Flask securely on localhost.

Troubleshooting:
- Check Flask: `curl -v http://127.0.0.1:5000/`
- Check Nginx: `sudo tail -f /var/log/nginx/error.log`
- If using a self-signed cert, trust it on tablets or click through the warning.
