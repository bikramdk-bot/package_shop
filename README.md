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

Scanner configuration
- The scanner service reads events from a single Linux input device. Set the device via the Staff page or manually:
	- Staff UI: /staff → Scanner section uses /list-scanners and /set-scanner
	- Manual: write /home/pi/config/shop_info.json with a field scanner_path pointing to /dev/input/by-id/…-event-kbd

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

Create /etc/systemd/system/scanner_listener.service:

[Unit]
Description=Packet Shop Scanner Listener
After=multi-user.target

[Service]
WorkingDirectory=/home/pi/package_shop
Environment=PRINT_VIA_API=1
ExecStart=/usr/bin/python3 /home/pi/package_shop/src/scanner_listener.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

Enable both:
- sudo systemctl daemon-reload
- sudo systemctl enable --now package_shop.service scanner_listener.service

Troubleshooting quick checks
- Printer:
	- lpstat -p -d
	- echo ZPL | lp -d <queue> -o raw
- Scanner:
	- ls -l /dev/input/by-id/*event-kbd
	- sudo -E python3 src/scanner_listener.py (scan and watch logs)
- API endpoints:
	- curl -s http://127.0.0.1:5000/list-scanners | jq
	- curl -s -X POST http://127.0.0.1:5000/print_label -H 'Content-Type: application/json' -d '{"lcn":"TEST","digits":"1234"}'

