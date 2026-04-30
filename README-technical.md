Packet Shop Technical README
============================

This document keeps the system-level setup and device operations details that used to live in the top-level README. It is aimed at Raspberry Pi deployment, scanner integration, label printing, hotspot setup, RTC configuration, and reliability hardening.

Overview
- API: Flask app in `src/api_server.py`
- Scanner service: `src/scanner_listener.py` reads `/dev/input` and posts to the API
- Printing: the API can print through CUPS or write directly to a printer device

Prerequisites (Pi)
- Install packages:
	- `sudo apt update`
	- `sudo apt install -y cups cups-client python3-evdev`
- Add the runtime user to required groups:
	- `sudo usermod -aG lp,lpadmin,input pi`
	- `sudo systemctl enable --now cups`

Configure the Zebra printer (CUPS)
1. Add the printer in CUPS and note the queue name, for example `Zebra_ZD`.
2. Use a raw queue for ZPL where possible.
3. Test printing:

```bash
echo '^XA^FO50,50^ADN,36,20^FDHello^FS^XZ' | lp -d Zebra_ZD -o raw
```

Make the API print via CUPS
- Set `PRINTER_DEVICE=cups:Zebra_ZD`
- If `PRINTER_DEVICE` is a path such as `/dev/usb/lp0`, the API writes directly instead.
- If `PRINTER_DEVICE` is not set, the app tries to auto-detect the default CUPS destination.

Persistent config
- Main runtime config lives in `src/shop_info.json`.
- The app migrates older HOME-based config into `src/shop_info.json` on startup.
- Example:

```json
{
  "printer_device": "cups:ZD411",
  "scanner_path": "/dev/input/by-id/usb-0581_011c-event-kbd"
}
```

Scanner configuration
- Staff UI: `/staff` uses `/list-scanners` and `/set-scanner`
- Manual config: set `scanner_path` in `src/shop_info.json`

Run the scanner service in the foreground

```bash
sudo -E PRINT_VIA_API=1 python3 src/scanner_listener.py
```

Permissions tips
- If the scanner cannot open the input device, run the listener as root or ensure the service user is in the `input` group.

Systemd example for API

```ini
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
```

Scanner listener service
- You can run `scanner_listener.py` as a separate unit when the deployment expects a dedicated hardware listener.

Useful checks
- Printer:
	- `lpstat -p -d`
	- `echo ZPL | lp -d <queue> -o raw`
- Scanner:
	- `ls -l /dev/input/by-id/*event-kbd`
	- `sudo -E python3 src/scanner_listener.py`
- API:
	- `curl -s http://127.0.0.1:5000/list-scanners | jq`
	- `curl -s -X POST http://127.0.0.1:5000/print_label -H 'Content-Type: application/json' -d '{"lcn":"TEST","digits":"1234"}'`

Offline Wi-Fi AP (MT7612U)
--------------------------

Goal
- Use the MT7612U USB adapter as the only access point and keep the network fully local.

Linux setup
- Script: `scripts/setup_ap_linux.sh`
- Requirement: `iw list` must show `AP` for the target adapter.

Example

```bash
sudo ./scripts/setup_ap_linux.sh -i wlan0 -s ShopAP -p StrongPass123! -f 5
sudo ./scripts/setup_ap_linux.sh -i wlan1 -s ShopAP -p StrongPass123! -c DK -f 2 -X
```

Notes
- `-X` disables other Wi-Fi adapters for a dedicated AP setup.
- The default subnet is local-only and no NAT is configured.
- Use `-f 2` for broader handheld compatibility when needed.

Troubleshooting AP mode
- Check capabilities with `iw dev` and `iw phy... info`.
- If `AP` is missing, update firmware or switch to a known AP-capable adapter.

Windows hotspot notes
- Prefer the Windows Mobile Hotspot UI.
- Disable other wireless adapters if the host keeps switching uplinks.
- `netsh hostednetwork` is deprecated on modern Windows and should only be treated as a fallback.

RTC Hardware Clock on Raspberry Pi
----------------------------------

Use an I2C RTC such as DS1307 or DS3231 to keep time offline.

1. Enable I2C with `raspi-config`.
2. Create and enable `rtc-init.service` to bind the RTC and load system time at boot.
3. Verify using `i2cdetect` and `hwclock -r`.

Optional shutdown save service
- Add `rtc-save.service` to write system time back to the RTC on shutdown.

Notes
- Adjust the I2C address if your module is not using `0x68`.
- With a real RTC present, `fake-hwclock` can be disabled.

24/7 Mode Checklist
-------------------

Recommended hardening for always-on offline deployments:
- Disable Wi-Fi power saving
- Disable USB autosuspend
- Set CPU governor to `performance`
- Keep RTC in local-time mode when no network time is available

Examples
- Disable Wi-Fi power saving through NetworkManager config and `iw`.
- Add `usbcore.autosuspend=-1` to the kernel command line.
- Add `cpufreq.default_governor=performance` to the kernel command line.
- Run `sudo timedatectl set-local-rtc 1` when the box should stay offline.

Where to look next
- Top-level `README.md`: general project overview
- `src/README.md`: networking, hotspot-only notes, and license-related internal docs