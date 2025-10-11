# src/scanner_listener.py
import sys
import time
from lookup import insert_parcel

def get_provider_from_prefix(barcode: str):
    """Simple logic to detect provider from barcode prefix."""
    if barcode.startswith("0037") or barcode.startswith("731"):
        return "PostNord"
    elif barcode.startswith("570"):
        return "DAO"
    elif barcode.startswith("1Z"):
        return "UPS"
    elif barcode.startswith("JJD"):
        return "DHL"
    else:
        return "Unknown"


def handle_scan(barcode: str):
    """Process one scanned barcode string."""
    provider = get_provider_from_prefix(barcode)
    digits = barcode[-4:]
    insert_parcel(provider, digits)


def listen_scanner():
    """Continuously read from stdin (HID scanner)."""
    print("🔎 Listening for scanner input... (press Ctrl+C to stop)\n")
    buffer = ""
    while True:
        char = sys.stdin.read(1)
        if char == "\n":
            barcode = buffer.strip()
            if barcode:
                handle_scan(barcode)
            buffer = ""
        else:
            buffer += char


if __name__ == "__main__":
    try:
        listen_scanner()
    except KeyboardInterrupt:
        print("\n🛑 Scanner listener stopped.")
