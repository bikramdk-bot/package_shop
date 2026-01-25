Packet Shop – Raspberry Pi Scanner + Printer Setup
==================================================

This guide helps you get HID scanner input and Zebra ZD printing working on a fresh Raspberry Pi OS image.

Overview
- API: Flask app in src/api_server.py
- Scanner service: src/scanner_listener.py (reads /dev/input) and posts to API
- Printing: API now supports direct /dev write or CUPS queue (lp -o raw)

Prerequisites (Pi)
- OS packages:
	- sudo apt update
	- sudo apt install -y cups cups-client python3-evdev
- Add user to groups so services can access devices:
	- sudo usermod -aG lp,lpadmin,input pi
	- sudo systemctl enable --now cups

Configure the Zebra printer (CUPS)
1) Add the printer in CUPS (web UI or CLI) and note the queue name (e.g., Zebra_ZD).
2) For ZPL, set Queue to Raw (no filtering) or use a Zebra driver that accepts raw ZPL.
3) Test from shell:
	 echo '^XA^FO50,50^ADN,36,20^FDHello^FS^XZ' | lp -d Zebra_ZD -o raw

Make the API print via CUPS
- Set an environment variable to point at your queue:
	- PRINTER_DEVICE=cups:Zebra_ZD
	The API will send ZPL via lp -d Zebra_ZD -o raw. If you set PRINTER_DEVICE to a device path (/dev/usb/lp0), it will write directly instead.

Auto-detection and persistent config
- If `PRINTER_DEVICE` is not set, the API auto-detects the system default CUPS destination (via `lpstat -d`) and uses it as `cups:<queue>`.
Canonical config location is now `src/shop_info.json` (next to the code). On startup, the app will migrate `~/config/shop_info.json` to `src/shop_info.json` by overwriting the file, then remove the old HOME copy.
To persist settings, edit `src/shop_info.json`:
	{
		"printer_device": "cups:ZD411", "scanner_path": "/dev/input/by-id/usb-0581_011c-event-kbd"
	}
	- Manual: edit src/shop_info.json with a field scanner_path pointing to /dev/input/by-id/…-event-kbd
Scanner configuration
- The scanner service reads events from a single Linux input device. Set the device via the Staff page or manually:
	- Staff UI: /staff → Scanner section uses /list-scanners and /set-scanner
	- Manual: edit src/shop_info.json and set scanner_path to /dev/input/by-id/…-event-kbd

Run the scanner service for testing
- Activate logging and run in foreground:
	- sudo -E PRINT_VIA_API=1 python3 src/scanner_listener.py
	- Scan an LCN (letters only), then scan a barcode; you should see a /scan_and_print POST and a label print.

Permissions tips
- If scanner fails with permission denied, either run scanner_listener as root or ensure the service user is in the input group. Optionally create a udev rule to set MODE for your device.

Systemd (example)
Create /etc/systemd/system/package_shop.service (API):

[Unit]
Description=Packet Shop API
After=network-online.target

[Service]
WorkingDirectory=/home/pi/package_shop
Environment=PRINTER_DEVICE=cups:Zebra_ZD
ExecStart=/usr/bin/python3 /home/pi/package_shop/src/api_server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

Optional: separate scanner listener service
If you prefer to run the scanner listener as its own unit, create `/etc/systemd/system/scanner_listener.service` with the usual Python invocation. Otherwise, you can run only the API service; environments that launch the scanner via API don't need a separate unit.

Troubleshooting quick checks
- Single-unit alternative (API + Scanner in one service)
If you prefer one service to manage both the API and the scanner listener, use the helper script [src/scripts/run_both.sh](src/scripts/run_both.sh):

Create /etc/systemd/system/package_shop.service:

[Unit]
Description=Packet Shop (API + Scanner)
After=network-online.target

[Service]
WorkingDirectory=/home/admin/package_shop
Environment=PRINTER_DEVICE=cups:ZD411
Environment=PRINT_VIA_API=1
Environment=DISABLE_EVDEV_GRAB=0
ExecStart=/usr/bin/bash -lc '/home/admin/package_shop/src/scripts/run_both.sh'
Restart=on-failure

[Install]
WantedBy=multi-user.target

Then reload and enable:
- sudo systemctl daemon-reload
- sudo systemctl enable --now package_shop.service

Notes:
- If either API or scanner exits, the unit restarts and brings both back up.
- Set `DISABLE_EVDEV_GRAB=1` if exclusive keyboard grab interferes with desktop usage.
- You can still keep the two-unit setup for cleaner isolation; choose the model that fits your ops.

- Printer:
	- lpstat -p -d
	- echo ZPL | lp -d <queue> -o raw
- Scanner:
	- ls -l /dev/input/by-id/*event-kbd
	- sudo -E python3 src/scanner_listener.py (scan and watch logs)
- API endpoints:
	- curl -s http://127.0.0.1:5000/list-scanners | jq
	- curl -s -X POST http://127.0.0.1:5000/print_label -H 'Content-Type: application/json' -d '{"lcn":"TEST","digits":"1234"}'

Offline Wi‑Fi AP (MT7612U)
---------------------------

- Goal: Use the MT7612U USB dongle as the Access Point, disable other Wi‑Fi adapters, and provide a pure offline hotspot for scanners/printers.
- Linux recommended: hostapd + dnsmasq with `mt76x2u` driver.

Linux setup

- Script: scripts/setup_ap_linux.sh
- Requirements: root, `iw list` shows `AP` under Supported interface modes, MT7612U appears as `wlanX`.

Steps:

1) Identify the MT7612U interface:

	```bash
	sudo iw dev
	```

2) Run the setup (example):

	```bash
	sudo ./scripts/setup_ap_linux.sh -i wlan0 -s ShopAP -p StrongPass123! -f 5
	sudo ./scripts/setup_ap_linux.sh -i wlan0 -s ShopAP -p StrongPass123! -c DK -f 5

   Persistently disable other Wi‑Fi adapters (keep only the chosen interface active):

	sudo ./scripts/setup_ap_linux.sh -i wlan1 -s ShopAP -p StrongPass123! -c DK -f 2 -X

   - `-X`: Blacklists drivers of other Wi‑Fi interfaces, disables their `wpa_supplicant@iface` units, and on Raspberry Pi sets `dtoverlay=disable-wifi` in `/boot/config.txt`. Reboot recommended.
	```

- Flags:
  - `-i`: Wi‑Fi interface (e.g., `wlan0`)
  - `-s`: SSID
  - `-p`: WPA2 passphrase
  - `-c`: Country code
  - `-f`: Band (`2` or `5`; default `5`)
  - `-n`: Subnet CIDR (default `10.10.0.0/24`)

- Outcome:
  - Starts `hostapd` and `dnsmasq`, assigns gateway IP `.1`, serves DHCP, and brings down other Wi‑Fi interfaces to keep only the AP active.

Pure offline behavior (no internet/NAT):

- The AP host acts as a local gateway with IP `10.10.0.1` (by default).
- DHCP leases are handed out to clients (default `10.10.0.10-50`).
- No NAT or routing to external networks is configured; clients can only reach services on the AP host.
- Recommended:
	- Bind your API to `0.0.0.0` so clients on the AP can access it: `FLASK_RUN_HOST=0.0.0.0` or app config.
	- Ensure `ufw`/firewall allows inbound on the API port (e.g., `5000`) from the AP subnet.
	- Keep other Wi‑Fi adapters down to prevent Windows/Linux from switching gateways.
	- Use `-f 2` if you need wider compatibility (some handhelds are 2.4 GHz only).

Troubleshooting:

- AP mode missing: Update kernel or ensure MT7612U uses `mt76x2u`. Confirm with `iw list`.
- Check services:

	```bash
	systemctl status hostapd --no-pager
	systemctl status dnsmasq --no-pager
	journalctl -u hostapd -u dnsmasq -b --no-pager
	```

Windows (Mobile Hotspot)

- Prefer the Settings UI; command-line control is limited.

Steps:

1) Disable other Wi‑Fi adapters (keep MT7612U enabled):

	Get-NetAdapter -InterfaceDescription '*Wireless*' | Where-Object {$_.Name -ne 'Wi-Fi (MT7612U)'} | Disable-NetAdapter -Confirm:$false

2) Enable Mobile Hotspot:
   - Settings → Network & Internet → Mobile hotspot → Turn On
   - Edit SSID and password as needed

3) Optional: Re-enable adapters after testing:

	Get-NetAdapter -InterfaceDescription '*Wireless*' | Enable-NetAdapter -Confirm:$false

Notes:

- `netsh hostednetwork` is deprecated on recent Windows versions. If your driver supports it:

	netsh wlan set hostednetwork mode=allow ssid=ShopAP key=StrongPass123!
	netsh wlan start hostednetwork

AP Compatibility & Fallbacks
----------------------------

- Observed: On Raspberry Pi OS kernel 6.12, both onboard `brcmfmac` (wlan0) and MT7612U `mt76x2u` (wlan1) may not advertise `AP` in `iw phy` capabilities, preventing hostapd from starting an AP.
- Verify capabilities before AP setup:

	```bash
	iw dev

	# Check driver for each interface
	readlink -f /sys/class/net/<iface>/device/driver | xargs basename

	# Check supported modes — look for a line containing 'AP'
	iw phy$(iw dev <iface> info | awk '/wiphy/{print $2}') info | sed -n '/Supported interface modes:/,/^$/p'
	```

- If `AP` is not listed for your target interface:
  - Hardware fallback: use a USB adapter with upstream AP support (e.g., Atheros AR9271/AR7010 using `ath9k_htc`).
  - OS/firmware updates: `sudo apt update && sudo apt full-upgrade -y`, then install firmware: `sudo apt install -y firmware-misc-nonfree || sudo apt install -y linux-firmware`; reboot and re-check.
  - Regulatory domain: `sudo iw reg set DK` to match local rules and channel availability.
  - Disable other Wi‑Fi adapters to avoid conflicts and ensure hostapd binds the intended device.

- Using onboard Wi‑Fi instead:
  - If `brcmfmac` eventually shows `AP`, you can run: `sudo ./scripts/setup_ap_linux.sh -i wlan0 -s ShopAP -p StrongPass123! -c DK -f 2` (2.4 GHz recommended for handheld compatibility).

- If AP remains unsupported on current hardware/software:
  - Keep the pure offline design by introducing a dedicated AP device (external router/AP) configured without WAN/NAT and with DHCP pointing devices to the Pi host, or swap to a known AP-capable USB dongle.

Nginx TLS (Self‑Signed until ~2055)
-----------------------------------

Goal: run Nginx as a reverse proxy on HTTPS (443) with a self‑signed certificate valid until around year 2055, proxying to the Flask API on port 5000.

Files:
- scripts/nginx.conf — TLS reverse proxy config targeting 127.0.0.1:5000
- scripts/generate_self_signed_cert.sh — OpenSSL (Linux/macOS) cert generator
- scripts/generate_self_signed_cert.ps1 — OpenSSL (Windows) cert generator
- scripts/run_nginx_linux.sh — starts Nginx with our config
- scripts/run_nginx_windows.bat — starts Nginx with our config

Generate the certificate

Linux/macOS:

```bash
chmod +x scripts/generate_self_signed_cert.sh
./scripts/generate_self_signed_cert.sh
```

Windows (PowerShell):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\u200bscripts\generate_self_signed_cert.ps1
```

This creates db/certs/server.key and db/certs/server.crt with SAN=localhost and IP=127.0.0.1 and ~10650 days validity.

Start Nginx

Linux:

```bash
chmod +x scripts/run_nginx_linux.sh
./scripts/run_nginx_linux.sh
```

Windows:

1) Install Nginx (download from nginx.org or via a package manager).
2) Edit scripts/run_nginx_windows.bat and set NGINX_HOME if auto‑detection fails.
3) Double‑click scripts/run_nginx_windows.bat or run from cmd.

Access:
- Browser: https://localhost/ → proxies to Flask API.
- Self‑signed warning is expected; optionally trust the cert in your OS.

Notes:
- The API already sets ProxyFix and prefers HTTPS scheme; Nginx forwards standard headers.
- If you serve static assets via Nginx, uncomment the /static/ location in scripts/nginx.conf.
- On Linux, binding to 443 requires root; the run script uses daemon off for foreground logs.

