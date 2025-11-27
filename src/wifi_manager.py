import os
import platform
import subprocess
from typing import List, Dict, Tuple


def _is_linux_pi() -> bool:
    try:
        return platform.system() == "Linux"
    except Exception:
        return False


def scan_networks() -> List[Dict[str, str]]:
    """Return list of available Wi‑Fi SSIDs.

    Uses nmcli if available, else iwlist. Returns a list of dicts
    with keys: ssid, signal, security.
    """
    nets: List[Dict[str, str]] = []
    if not _is_linux_pi():
        # Dev fallback: return dummy networks on non‑Linux
        return [
            {"ssid": "ShopWiFi", "signal": "70", "security": "WPA2"},
            {"ssid": "Guest", "signal": "40", "security": "Open"},
        ]

    # Prefer nmcli
    try:
        out = subprocess.check_output([
            "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"
        ], stderr=subprocess.STDOUT, text=True, timeout=8)
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                ssid = parts[0].strip()
                if not ssid:
                    continue
                nets.append({
                    "ssid": ssid,
                    "signal": parts[1].strip() or "",
                    "security": parts[2].strip() or ""
                })
        if nets:
            return nets
    except Exception:
        pass

    # Fallback: iwlist (best effort)
    try:
        out = subprocess.check_output(["bash", "-lc", "iwlist scan"], stderr=subprocess.STDOUT, text=True, timeout=10)
        ssid = None
        signal = ""
        security = ""
        for line in out.splitlines():
            l = line.strip()
            if l.startswith("ESSID:"):
                ssid = l.split("ESSID:", 1)[1].strip().strip('"')
            elif "Signal level=" in l:
                signal = l.split("Signal level=", 1)[1].split()[0]
            elif "IE:" in l:
                security = l.split("IE:", 1)[1].strip()
            if ssid and (l == "" or l.startswith("Cell ")):
                nets.append({"ssid": ssid, "signal": signal, "security": security})
                ssid, signal, security = None, "", ""
        if ssid:
            nets.append({"ssid": ssid, "signal": signal, "security": security})
    except Exception:
        pass
    return nets


def set_credentials(ssid: str, password: str) -> Tuple[bool, str]:
    """Configure Wi‑Fi credentials and attempt to connect.

    On Linux with NetworkManager: uses nmcli to add or modify a connection.
    Returns (success, message).
    """
    ssid = (ssid or "").strip()
    password = (password or "").strip()
    if not ssid:
        return False, "Missing SSID"

    if not _is_linux_pi():
        # Dev stub
        return True, f"Stored credentials for {ssid} (dev mode)"

    # Try nmcli connect
    try:
        # If password empty, attempt open network
        cmd = ["nmcli", "device", "wifi", "connect", ssid]
        if password:
            cmd += ["password", password]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=20)
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        return False, e.output.strip() if isinstance(e.output, str) else str(e)
    except Exception as e:
        return False, str(e)


def current_status() -> Dict[str, str]:
    """Return Wi‑Fi status: connected SSID and IP if available."""
    if not _is_linux_pi():
        return {"ssid": "dev", "ip": "127.0.0.1", "mode": "stub"}
    try:
        ssid = ""
        ip = ""
        try:
            out = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid", "device", "wifi"], text=True)
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 2 and parts[0] == "yes":
                    ssid = parts[1]
                    break
        except Exception:
            pass
        try:
            ip = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
        except Exception:
            pass
        return {"ssid": ssid, "ip": ip, "mode": "wifi" if ssid else "hotspot"}
    except Exception:
        return {"ssid": "", "ip": "", "mode": "unknown"}
