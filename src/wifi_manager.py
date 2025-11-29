import os
import platform
import subprocess
from typing import List, Dict, Tuple
import json


def _load_watchdog_service() -> str:
    """Return AP watchdog service name from shop_info.json if present."""
    try:
        base = os.path.dirname(__file__)
        cfg_path = os.path.join(base, "shop_info.json")
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = (data.get("ap_watchdog_service") or "").strip()
        return name
    except Exception:
        return ""


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
        return [
            {"ssid": "ShopWiFi", "signal": "70", "security": "WPA2"},
            {"ssid": "Guest", "signal": "40", "security": "Open"},
        ]

    # Prefer nmcli first while AP (hotspot) may still be active.
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

    # If no networks found and hotspot likely blocking scan, try cycling AP off briefly.
    ap_name = _ap_connection_name()
    cycled_ap = False
    if not nets and ap_name:
        try:
            subprocess.check_output(["nmcli", "connection", "down", ap_name], stderr=subprocess.STDOUT, text=True, timeout=6)
            cycled_ap = True
            # Short pause to let interface switch modes
            time.sleep(1.0)
            out2 = subprocess.check_output([
                "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"
            ], stderr=subprocess.STDOUT, text=True, timeout=8)
            for line in out2.splitlines():
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
        except Exception:
            pass
        finally:
            # Restore AP so tablet keeps access
            try:
                subprocess.check_output(["nmcli", "connection", "up", ap_name], stderr=subprocess.STDOUT, text=True, timeout=8)
            except Exception:
                pass
        # Annotate networks with meta flag if any found
        if nets:
            for n in nets:
                n.setdefault("_meta", {})
                if isinstance(n["_meta"], dict):
                    n["_meta"]["ap_cycled"] = True

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


def _nmcli_security_of_ssid(target: str) -> str:
    """Return SECURITY string reported by nmcli for a given SSID, or ''."""
    if not _is_linux_pi():
        return "WPA2"
    try:
        out = subprocess.check_output([
            "nmcli", "--fields", "SSID,SECURITY", "device", "wifi", "list"
        ], stderr=subprocess.STDOUT, text=True, timeout=8)
        for line in out.splitlines():
            # Lines like: SSID  SECURITY
            if not line.strip() or line.strip().startswith("SSID"):
                continue
            # Split by two or more spaces to avoid SSID spaces confusion
            parts = [p for p in line.strip().split("  ") if p]
            if len(parts) >= 2:
                ssid = parts[0].strip()
                sec = parts[-1].strip()
                if ssid == target:
                    return sec
            else:
                # Fallback: simple split
                cols = line.split()
                if len(cols) >= 2 and cols[0] == target:
                    return " ".join(cols[1:])
    except Exception:
        pass
    return ""


def _derive_key_mgmt(security: str) -> str:
    s = (security or "").upper()
    if "WPA3" in s or "SAE" in s:
        return "sae"
    if "WPA" in s:
        return "wpa-psk"
    if "WEP" in s:
        return "wep"  # discouraged; may not work
    return ""  # open network


def set_credentials(ssid: str, password: str, hidden: bool = False) -> Tuple[bool, str]:
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
        msg = e.output.strip() if isinstance(e.output, str) else str(e)
        # If key-mgmt missing or general failure, attempt explicit connection profile
        if "key-mgmt" in msg or "property is missing" in msg or "No network with SSID" in msg or "No suitable" in msg:
            try:
                security = _nmcli_security_of_ssid(ssid)
                key_mgmt = _derive_key_mgmt(security)
                add_cmd = [
                    "nmcli", "connection", "add", "type", "wifi",
                    "ifname", "wlan0", "con-name", ssid, "ssid", ssid
                ]
                if key_mgmt:
                    add_cmd += ["wifi-sec.key-mgmt", key_mgmt]
                if password and key_mgmt in ("wpa-psk", "sae"):
                    add_cmd += ["wifi-sec.psk", password]
                if hidden or not security:
                    add_cmd += ["connection.autoconnect", "yes", "wifi.hidden", "yes"]
                out = subprocess.check_output(add_cmd, stderr=subprocess.STDOUT, text=True, timeout=20)
                # Bring it up
                out2 = subprocess.check_output(["nmcli", "connection", "up", ssid], stderr=subprocess.STDOUT, text=True, timeout=20)
                return True, (out2.strip() or out.strip())
            except subprocess.CalledProcessError as e3:
                msg3 = e3.output.strip() if isinstance(e3.output, str) else str(e3)
                # Last resort: try with sudo
                try:
                    sudo_add = ["sudo", "-n"] + add_cmd
                    out = subprocess.check_output(sudo_add, stderr=subprocess.STDOUT, text=True, timeout=20)
                    out2 = subprocess.check_output(["sudo", "-n", "nmcli", "connection", "up", ssid], stderr=subprocess.STDOUT, text=True, timeout=20)
                    return True, (out2.strip() or out.strip())
                except subprocess.CalledProcessError as e4:
                    msg4 = e4.output.strip() if isinstance(e4.output, str) else str(e4)
                    return False, f"Explicit profile failed: {msg3}; sudo retry: {msg4}"
        # Handle authorization failure by retrying with sudo (non-interactive)
        if "Not authorized" in msg or "not authorized" in msg or "Failed to add/activate" in msg:
            try:
                sudo_cmd = ["sudo", "-n"] + cmd
                out = subprocess.check_output(sudo_cmd, stderr=subprocess.STDOUT, text=True, timeout=20)
                return True, out.strip()
            except subprocess.CalledProcessError as e2:
                msg2 = e2.output.strip() if isinstance(e2.output, str) else str(e2)
                guidance = (
                    "Authorization required to control networking. "
                    "Run this app as root, or configure a polkit rule to allow nmcli for this user. "
                    "Example: create /etc/polkit-1/rules.d/10-nmcli.rules to permit org.freedesktop.NetworkManager.settings.modify.system."
                )
                return False, f"{msg}\nRetry with sudo failed: {msg2}\n{guidance}"
        return False, msg
    except Exception as e:
        return False, str(e)


def _ap_connection_name() -> str:
    """Return hotspot/AP connection name if active, else empty."""
    if not _is_linux_pi():
        return ""
    try:
        out = subprocess.check_output(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show"], text=True)
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                name, ctype, dev = parts[0], parts[1], parts[2]
                if ctype == "wifi" and dev == "wlan0" and name.upper().endswith("AP"):
                    return name
    except Exception:
        pass
    return ""


def pause_ap() -> Tuple[bool, str]:
    """Temporarily bring down the hotspot/AP to allow scanning."""
    if not _is_linux_pi():
        return True, "AP paused (dev)"
    # Try to pause any AP watchdog to avoid auto re-enable during scanning
    wd = _load_watchdog_service()
    if wd:
        try:
            subprocess.check_output(["sudo", "-n", "systemctl", "stop", wd], stderr=subprocess.STDOUT, text=True, timeout=5)
            # Stop potential timer unit as well
            if wd.endswith(".service"):
                timer = wd.replace(".service", ".timer")
                try:
                    subprocess.check_output(["sudo", "-n", "systemctl", "stop", timer], stderr=subprocess.STDOUT, text=True, timeout=5)
                except Exception:
                    pass
        except Exception:
            pass
    name = _ap_connection_name()
    if not name:
        return True, "No AP active"
    try:
        out = subprocess.check_output(["nmcli", "connection", "down", name], stderr=subprocess.STDOUT, text=True, timeout=10)
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        msg = e.output.strip() if isinstance(e.output, str) else str(e)
        try:
            out = subprocess.check_output(["sudo", "-n", "nmcli", "connection", "down", name], stderr=subprocess.STDOUT, text=True, timeout=10)
            return True, out.strip()
        except subprocess.CalledProcessError as e2:
            msg2 = e2.output.strip() if isinstance(e2.output, str) else str(e2)
            return False, f"Failed to pause AP: {msg}\nRetry with sudo failed: {msg2}"


def resume_ap() -> Tuple[bool, str]:
    """Bring the hotspot/AP back up."""
    if not _is_linux_pi():
        return True, "AP resumed (dev)"
    name = _ap_connection_name() or "PSHOP-PI-AP"
    try:
        out = subprocess.check_output(["nmcli", "connection", "up", name], stderr=subprocess.STDOUT, text=True, timeout=10)
        # Resume watchdog if configured
        wd = _load_watchdog_service()
        if wd:
            try:
                subprocess.check_output(["sudo", "-n", "systemctl", "start", wd], stderr=subprocess.STDOUT, text=True, timeout=5)
                if wd.endswith(".service"):
                    timer = wd.replace(".service", ".timer")
                    try:
                        subprocess.check_output(["sudo", "-n", "systemctl", "start", timer], stderr=subprocess.STDOUT, text=True, timeout=5)
                    except Exception:
                        pass
            except Exception:
                pass
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        msg = e.output.strip() if isinstance(e.output, str) else str(e)
        try:
            out = subprocess.check_output(["sudo", "-n", "nmcli", "connection", "up", name], stderr=subprocess.STDOUT, text=True, timeout=10)
            # Resume watchdog if configured
            wd = _load_watchdog_service()
            if wd:
                try:
                    subprocess.check_output(["sudo", "-n", "systemctl", "start", wd], stderr=subprocess.STDOUT, text=True, timeout=5)
                    if wd.endswith(".service"):
                        timer = wd.replace(".service", ".timer")
                        try:
                            subprocess.check_output(["sudo", "-n", "systemctl", "start", timer], stderr=subprocess.STDOUT, text=True, timeout=5)
                        except Exception:
                            pass
                except Exception:
                    pass
            return True, out.strip()
        except subprocess.CalledProcessError as e2:
            msg2 = e2.output.strip() if isinstance(e2.output, str) else str(e2)
            return False, f"Failed to resume AP: {msg}\nRetry with sudo failed: {msg2}"


def disconnect_wifi() -> Tuple[bool, str]:
    """Disconnect current Wi‑Fi client connection on wlan0 (not the AP).

    Finds active wifi connection(s) on wlan0 that are not the hotspot name and brings them down.
    """
    if not _is_linux_pi():
        return True, "Disconnected (dev)"
    ap_name = _ap_connection_name()
    try:
        out = subprocess.check_output(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,ACTIVE", "connection", "show", "--active"], text=True)
        to_down = []
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                name, ctype, dev, active = parts[0], parts[1], parts[2], parts[3]
                if ctype == "wifi" and dev == "wlan0" and active == "yes" and name != ap_name:
                    to_down.append(name)
        if not to_down:
            return True, "No client Wi‑Fi connection to disconnect"
        msgs = []
        for name in to_down:
            try:
                msg = subprocess.check_output(["nmcli", "connection", "down", name], stderr=subprocess.STDOUT, text=True, timeout=10).strip()
                msgs.append(msg)
            except subprocess.CalledProcessError:
                # retry with sudo
                msg = subprocess.check_output(["sudo", "-n", "nmcli", "connection", "down", name], stderr=subprocess.STDOUT, text=True, timeout=10).strip()
                msgs.append(msg)
        return True, "; ".join(msgs)
    except subprocess.CalledProcessError as e:
        return False, e.output.strip() if isinstance(e.output, str) else str(e)
    except Exception as e:
        return False, str(e)


def current_status() -> Dict[str, str]:
    """Return Wi‑Fi status: connected SSID and IP if available."""
    if not _is_linux_pi():
        return {"ssid": "dev", "client_ssid": "dev", "ap_name": "PSHOP-PI-AP", "ip": "127.0.0.1", "mode": "stub"}
    try:
        client_ssid = ""
        ap_name = ""
        ip = ""
        # Determine active connections on wlan0
        try:
            out = subprocess.check_output([
                "nmcli", "-t", "-f", "NAME,TYPE,DEVICE,ACTIVE", "connection", "show", "--active"
            ], text=True)
            ap_guess = _ap_connection_name() or "PSHOP-PI-AP"
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 4:
                    name, ctype, dev, active = parts[0], parts[1], parts[2], parts[3]
                    if ctype == "wifi" and dev == "wlan0" and active == "yes":
                        if name == ap_guess or name.upper().endswith("AP"):
                            ap_name = name
                        else:
                            client_ssid = name
        except Exception:
            pass
        try:
            ip = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
        except Exception:
            pass
        mode = "both" if (client_ssid and ap_name) else ("wifi" if client_ssid else ("hotspot" if ap_name else "unknown"))
        return {"ssid": client_ssid, "client_ssid": client_ssid, "ap_name": ap_name, "ip": ip, "mode": mode}
    except Exception:
        return {"ssid": "", "client_ssid": "", "ap_name": "", "ip": "", "mode": "unknown"}
