#!/usr/bin/env python3
import json
import os
import time
import subprocess

OUTPUT_PATH = "/home/pi/wifi_status.json"
CLIENT_IFACE = os.environ.get("PSHOP_CLIENT_IFACE", "wlan1")


def get_ipv4_address(iface: str) -> str:
    try:
        out = subprocess.check_output(["ip", "-4", "addr", "show", iface], text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                # Format: inet 192.168.1.23/24 brd ... scope global wlan1
                ip = line.split()[1].split("/")[0]
                return ip
    except subprocess.CalledProcessError:
        pass
    except Exception:
        pass
    return ""


def write_status(ip: str) -> None:
    data = {"wifi_connected_ip": (ip if ip else None)}
    try:
        # Ensure parent directory exists
        parent = os.path.dirname(OUTPUT_PATH)
        if parent:
            try:
                os.makedirs(parent, exist_ok=True)
            except Exception:
                pass
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        # Silent: watcher must not interfere
        pass


def main():
    while True:
        ip = get_ipv4_address(CLIENT_IFACE)
        write_status(ip)
        time.sleep(2)


if __name__ == "__main__":
    main()
