#!/usr/bin/env python3
from datetime import datetime
from evdev import InputDevice, ecodes
import os
import time
import traceback
import json
import urllib.request
import urllib.error
import re

# --- CONFIG ---
PRINTER_DEVICE = "/dev/usb/lp0"
SCANNER_PATH = "/dev/input/by-id/usb-0581_011c-event-kbd"

# LCN detection: treat purely alphabetic tokens (legacy behavior).
# Previously the code supported a SPECIAL_LCN_MATCH prefix and an
# accompanying STRIP_LAST_5_FOR_SPECIAL behavior; these were redundant
# in practice and caused surprising truncation of stored LCNs. The
# logic has been simplified to avoid accidental prefix-based matches.

current_lcn = None

KEYMAP = {
    2:"1",3:"2",4:"3",5:"4",6:"5",7:"6",8:"7",9:"8",10:"9",11:"0",
    16:"q",17:"w",18:"e",19:"r",20:"t",21:"y",22:"u",23:"i",24:"o",25:"p",
    30:"a",31:"s",32:"d",33:"f",34:"g",35:"h",36:"j",37:"k",38:"l",
    44:"z",45:"x",46:"c",47:"v",48:"b",49:"n",50:"m",
    28:"ENTER"
}

SHIFT_CODES = {42, 54}  # left/right shift

def process_barcode(code: str) -> str:
    code = code.strip().upper()
    if len(code) >= 4 and code[-2:].isdigit():
        return code[-4:]
    # If the last two characters are alphabetic (e.g. country/provider code),
    # treat the four characters before them as the digits to return.
    if len(code) >= 6 and re.fullmatch(r"[A-Z]{2}", code[-2:]):
        return code[-6:-2]
    if len(code) >= 11 and code[-1].isalpha() and code[-2].isdigit():
        return code[-11:-7]
    return code[-4:]


def is_lcn(s: str) -> bool:
    """Return True if the scanned buffer should be treated as an LCN.

    Heuristics used:
    - Matches SPECIAL_LCN_MATCH exactly or as a prefix
    - Or is purely alphabetic (legacy behavior)
    - Minimum length guard to avoid treating short tokens as LCNs
    """
    if not s:
        return False
    s = s.strip()
    su = s.upper()
    # Treat only purely alphabetic tokens as LCNs. This avoids classifying
    # mixed alphanumeric strings (e.g. "1231232131H") as LCNs — those are
    # barcodes and should be handled by the barcode path.
    if re.fullmatch(r"[A-Z]+", su) and len(su) >= 2:
        return True

    return False

def send_to_printer(lcn, digits, raw_barcode):
    # Build ZPL (keep same format as api_server)
    today = datetime.now().strftime("%d-%m-%y")
    zpl = f"""^XA
^PW394
^LL236
^FO280,10^A0N,25,25^FD{today}^FS
^FO10,10^A0N,50,50^FD{lcn}^FS
^FO35,90^A0N,170,170^FD{digits}^FS
^XZ
"""

    # By default prefer printing via the local API endpoint so the API
    # process owns the printer device. Override with PRINT_VIA_API=0 to
    # write directly to the device from this process.
    use_api = os.environ.get("PRINT_VIA_API", "1").lower() in ("1", "true", "yes")

    if use_api:
        # The provider is the LCN from the scanner logic (provider and LCN are the same)
        provider = lcn
        # include raw barcode string as 'barcode' for DB insert (send raw, not processed digits)
        # avoid redundancy: do not send 'lcn' since 'provider' already carries that value
        payload = {"provider": provider, "digits": digits, "barcode": raw_barcode}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:5000/scan_and_print", data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_body = resp.read().decode("utf-8")
                print("Printed via API, response:", resp.status, resp_body)
                return
        except Exception as e:
            print("Warning: API print failed, falling back to direct device write:", e)

    # Fallback: write directly to printer device
    print("sending to printer (direct):\n", zpl)
    try:
        with open(PRINTER_DEVICE, "wb") as p:
            p.write(zpl.encode("utf-8"))
    except Exception as e:
        print("Error: failed to write to printer device:", e)

def main():
    global current_lcn
    device = InputDevice(SCANNER_PATH)
    buffer = ""
    shift_active = False
    # Startup diagnostics
    try:
        import sys
        print("Service mode: listening on", device.path)
        print("PID", os.getpid(), "PPID", os.getppid(), "UID", os.geteuid(), "CWD", os.getcwd(), "PYEXE", sys.executable)
    except Exception:
        print("Service mode: listening on", device.path)

    # Robust device grab: optionally disable via DISABLE_EVDEV_GRAB=1
    disable_grab = os.environ.get("DISABLE_EVDEV_GRAB", "0").lower() in ("1", "true", "yes")
    def try_grab(dev, retries=5, delay=0.8):
        if disable_grab:
            print("Device grab disabled via DISABLE_EVDEV_GRAB")
            return False
        # If not root, warn (grab may fail due to permissions)
        try:
            euid = os.geteuid()
        except Exception:
            euid = None
        if euid is not None and euid != 0:
            print(f"Note: running as uid={euid}; grab may require root or input group membership")

        for attempt in range(1, retries + 1):
            try:
                dev.grab()
                print(f"Device grabbed successfully on attempt {attempt}")
                return True
            except Exception as e:
                # Print exception details to help debugging
                print(f"Warning: device.grab() attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
        # Failed all attempts; continue in non-exclusive mode
        print("Warning: could not grab device exclusively after retries; proceeding without exclusive grab")
        return False

    grabbed = try_grab(device)

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                if event.code in SHIFT_CODES:
                    if event.value == 1:
                        shift_active = True
                    elif event.value == 0:
                        shift_active = False
                elif event.value == 1:
                    key = KEYMAP.get(event.code)
                    if key:
                        if key == "ENTER":
                            if buffer:
                                # Use a more robust LCN detection instead of buffer.isalpha()
                                if is_lcn(buffer):
                                    # Simplified: store the detected LCN as-is (uppercased).
                                    current_lcn = buffer.strip().upper()
                                    print("Stored LCN:", current_lcn)
                                else:
                                    if current_lcn:
                                        digits = process_barcode(buffer)
                                        print("Barcode:", buffer, "→", digits, "| LCN:", current_lcn)
                                        # pass the raw scanned barcode (buffer) so DB gets raw value
                                        send_to_printer(current_lcn, digits, buffer)
                                    else:
                                        print("Error: No LCN set yet.")
                                buffer = ""
                        else:
                            if shift_active:
                                buffer += key.upper()
                            else:
                                buffer += key
    except KeyboardInterrupt:
        print("scanner_listener: interrupted by user")
    except Exception:
        print("scanner_listener: unexpected error:\n", traceback.format_exc())
    finally:
        # Attempt to release grab if we successfully grabbed it
        try:
            if 'grabbed' in locals() and grabbed:
                try:
                    device.ungrab()
                    print("Device ungrabbed")
                except Exception as e:
                    print("Warning: failed to ungrab device:", e)
        except Exception:
            pass

if __name__ == "__main__":
    main()
