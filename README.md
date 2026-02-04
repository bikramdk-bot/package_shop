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

RTC Hardware Clock (RTC) on Raspberry Pi
---------------------------------------

This guide shows how to enable an I2C hardware RTC (DS1307/DS3231) using a systemd unit — no overlay edits or repo scripts required.

Steps (run on the Pi):

1) Enable I2C bus

```bash
sudo raspi-config nonint do_i2c 0
# If needed, append dtparam and reboot:
if [ -f /boot/config.txt ]; then sudo grep -q '^dtparam=i2c_arm=on' /boot/config.txt || echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/config.txt; fi
if [ -f /boot/firmware/config.txt ]; then sudo grep -q '^dtparam=i2c_arm=on' /boot/firmware/config.txt || echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/firmware/config.txt; fi
sudo reboot
```

2) Create and start the RTC init unit (bind device and set time)

```bash
sudo tee /etc/systemd/system/rtc-init.service > /dev/null <<'EOF'
[Unit]
Description=Initialize RTC device (bind I2C) and set system time from hardware clock
After=local-fs.target systemd-modules-load.service
Wants=systemd-modules-load.service
Before=time-sync.target

[Service]
Type=oneshot
Environment=RTC_ADDR=0x68

ExecStart=/bin/sh -lc 'modprobe i2c-bcm2835 || true; modprobe i2c-dev || true; modprobe rtc-ds1307 || modprobe rtc-ds3231 || true'
ExecStart=/bin/sh -lc '[ -e /sys/class/rtc/rtc0 ] || ( echo ds1307 ${RTC_ADDR} > /sys/bus/i2c/devices/i2c-1/new_device ) || true'
ExecStart=/bin/sh -lc '[ -e /sys/class/rtc/rtc0 ] || ( echo ds3231 ${RTC_ADDR} > /sys/bus/i2c/devices/i2c-1/new_device ) || true'
ExecStart=/bin/sh -lc '/usr/local/sbin/hwclock -s || /usr/sbin/hwclock -s || /sbin/hwclock -s || true'

RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start rtc-init.service
sudo systemctl enable rtc-init.service
```

3) Verify

```bash
ls -l /sys/class/rtc
sudo i2cdetect -y 1
sudo hwclock -r || /usr/local/sbin/hwclock -r
```

Optional: write system time to RTC on shutdown

```bash
sudo tee /etc/systemd/system/rtc-save.service > /dev/null <<'EOF'
[Unit]
Description=Save system time to RTC at shutdown
DefaultDependencies=no
Before=shutdown.target
Conflicts=shutdown.target

[Service]
Type=oneshot
ExecStart=/bin/true
ExecStop=/bin/sh -lc '/usr/local/sbin/hwclock -w || /usr/sbin/hwclock -w || /sbin/hwclock -w || true'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rtc-save.service
```


Notes:
- If your wiring uses a different I2C bus or address, replace `i2c-1` and/or set `RTC_ADDR=0x69` in the unit, then restart it.
- With a real RTC present, you can safely disable `fake-hwclock` to avoid time drift:
	- `sudo systemctl stop fake-hwclock.service && sudo systemctl mask fake-hwclock.service && sudo apt remove -y fake-hwclock`

24/7 Mode Checklist (Offline)
-----------------------------

Hardening steps to keep the system reliable without internet.

1) Disable Wi‑Fi power saving (both wlan0 and wlan1)

```bash
# Global NetworkManager default (disable powersave on all connections)
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf > /dev/null <<'EOF'
[connection]
wifi.powersave = 2
EOF

# Dispatcher guard to force power_save off whenever links change
sudo mkdir -p /etc/NetworkManager/dispatcher.d
sudo tee /etc/NetworkManager/dispatcher.d/99-wifi-powersave-off > /dev/null <<'EOF'
#!/bin/sh
IFACE="$1"; ACTION="$2"
case "$ACTION" in
	up|dhcp4-change|dhcp6-change|connectivity-change)
		command -v iw >/dev/null 2>&1 || exit 0
		iw dev "$IFACE" set power_save off 2>/dev/null || true
		;;
esac
EOF
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-wifi-powersave-off

# Apply now (no reboot needed)
sudo systemctl reload NetworkManager || true
sudo iw dev wlan0 set power_save off 2>/dev/null || true
sudo iw dev wlan1 set power_save off 2>/dev/null || true

# Verify
iw dev | sed -n '/Interface \(wlan0\|wlan1\)/,/^$/p' | grep -i 'power save' || true
```

2) Disable USB autosuspend (keep scanners/printers awake)

```bash
# Persistent: add kernel parameter (Bookworm uses /boot/firmware/cmdline.txt)
TARGET=/boot/firmware/cmdline.txt; [ -f /boot/cmdline.txt ] && TARGET=/boot/cmdline.txt
PARAM=usbcore.autosuspend=-1
grep -q "$PARAM" "$TARGET" || sudo sed -i "s/$/ $PARAM/" "$TARGET"
echo "Updated $TARGET; reboot required to take effect."

# Immediate (until reboot)
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend >/dev/null

# Verify after reboot
cat /proc/cmdline | tr ' ' '\n' | grep usbcore.autosuspend || true
cat /sys/module/usbcore/parameters/autosuspend
```

3) CPU governor: performance

```bash
# Persistent via kernel parameter
TARGET=/boot/firmware/cmdline.txt; [ -f /boot/cmdline.txt ] && TARGET=/boot/cmdline.txt
PARAM=cpufreq.default_governor=performance
grep -q "$PARAM" "$TARGET" || sudo sed -i "s/$/ $PARAM/" "$TARGET"
echo "Updated $TARGET; reboot required to take effect."

# Immediate (until reboot)
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | sudo tee "$f"; done

# Verify
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | uniq
```

4) RTC policy: local time only (no network time)

```bash
# Store local time in RTC and read at boot
sudo timedatectl set-local-rtc 1

# Optional: disable systemd-timesyncd if present, and fake-hwclock
sudo systemctl disable --now systemd-timesyncd.service 2>/dev/null || true
sudo systemctl mask systemd-timesyncd.service 2>/dev/null || true
sudo systemctl stop fake-hwclock.service 2>/dev/null || true
sudo systemctl mask fake-hwclock.service 2>/dev/null || true
```

