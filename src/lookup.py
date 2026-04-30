import sqlite3, os, re
from datetime import datetime
from paths import resolve_data, init_dirs_and_migrate

# ✅ Same DB used by dashboard (externalized)
init_dirs_and_migrate()
DB_PATH = str(resolve_data("packets.db"))


def _numeric_tail(value, length):
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits[-length:] if len(digits) >= length else None


def _derive_lookup_variant(barcode, fallback_digits, length):
    source = str(barcode or "").strip().upper()
    if source:
        if len(source) >= length and source[-2:].isdigit():
            candidate = source[-length:]
            if candidate.isdigit():
                return candidate
        if len(source) >= length + 2 and re.fullmatch(r"[A-Z]{2}", source[-2:]):
            candidate = source[-(length + 2):-2]
            if candidate.isdigit():
                return candidate
        if len(source) >= length + 7 and source[-1].isalpha() and source[-2].isdigit():
            candidate = source[-(length + 7):-7]
            if candidate.isdigit():
                return candidate
        numeric_tail = _numeric_tail(source, length)
        if numeric_tail:
            return numeric_tail
    return _numeric_tail(fallback_digits, length)


def derive_packet_lookup_variants(barcode=None, digits=None):
    return {
        "digit6": _derive_lookup_variant(barcode, digits, 6),
        "digit8": _derive_lookup_variant(barcode, digits, 8),
        "digit10": _derive_lookup_variant(barcode, digits, 10),
    }


def backfill_packet_lookup_variants(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, digits, barcode, digit6, digit8, digit10
        FROM packets
        WHERE COALESCE(digit6, '') = ''
           OR COALESCE(digit8, '') = ''
           OR COALESCE(digit10, '') = ''
        """
    )
    updates = []
    for packet_id, digits, barcode, digit6, digit8, digit10 in cursor.fetchall():
        variants = derive_packet_lookup_variants(barcode=barcode, digits=digits)
        next_digit6 = digit6 or variants["digit6"]
        next_digit8 = digit8 or variants["digit8"]
        next_digit10 = digit10 or variants["digit10"]
        if next_digit6 != digit6 or next_digit8 != digit8 or next_digit10 != digit10:
            updates.append((next_digit6, next_digit8, next_digit10, packet_id))
    if updates:
        cursor.executemany(
            """
            UPDATE packets
            SET digit6 = ?, digit8 = ?, digit10 = ?
            WHERE id = ?
            """,
            updates,
        )
    return len(updates)


# ---------------------- INIT ----------------------
def init_db():
    """Create the packets table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            digits TEXT NOT NULL,
            digit6 TEXT,
            digit8 TEXT,
            digit10 TEXT,
            barcode TEXT,
            status TEXT DEFAULT 'in_shop',
            scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration for existing DB: add variant columns if missing
    try:
        cursor.execute("PRAGMA table_info(packets)")
        cols = [r[1] for r in cursor.fetchall()]
        for col in ("digit6", "digit8", "digit10"):
            if col not in cols:
                cursor.execute(f"ALTER TABLE packets ADD COLUMN {col} TEXT")
        backfill_packet_lookup_variants(conn)
        conn.commit()
    except Exception:
        pass
    conn.commit()
    conn.close()


# ---------------------- INSERT ----------------------
def insert_parcel(provider, digits, barcode=None):
    """Insert a new packet entry.

    Duplicate prevention rule: if a row with the same provider and barcode
    already exists with status 'in_shop', block the new insert. The 4 digits
    do not affect duplicate detection.

    Store the supplied digits and barcode exactly as provided.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # If a barcode is provided, use provider+barcode to detect duplicates in_shop.
    # If no barcode is provided, do not block based on digits (as requested).
    if barcode:
        cursor.execute(
            """
            SELECT COUNT(*) FROM packets
            WHERE UPPER(provider) = UPPER(?) AND barcode = ? AND status = 'in_shop'
            """,
            (provider, barcode),
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            return {"warning": "Packet already exists (same provider+barcode) and is in_shop."}

    variants = derive_packet_lookup_variants(barcode=barcode, digits=digits)

    cursor.execute(
        """
        INSERT INTO packets (provider, digits, digit6, digit8, digit10, barcode, status, scan_time)
        VALUES (?, ?, ?, ?, ?, ?, 'in_shop', ?)
        """,
        (provider, digits, variants["digit6"], variants["digit8"], variants["digit10"], barcode, datetime.now()),
    )
    conn.commit()
    conn.close()
    return {"message": "Packet inserted successfully."}


# ---------------------- SEARCH ----------------------
def search_parcel(provider, digits):
    """Return all matching packets."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider, digits, barcode, status, scan_time
        FROM packets
        WHERE provider = ? AND digits = ?
        ORDER BY scan_time DESC
    """, (provider, digits))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------- UPDATE ----------------------
def update_status(provider, digits, new_status):
    """Mark a packet as collected, held, etc."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE packets
        SET status = ?, scan_time = ?
        WHERE provider = ? AND digits = ?
    """, (new_status, datetime.now(), provider, digits))
    conn.commit()
    conn.close()
    return {"message": f"Status updated to {new_status}."}


# ---------------------- DELETE ----------------------
def delete_parcel(provider, digits):
    """Staff can manually delete a packet record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM packets
        WHERE provider = ? AND digits = ?
    """, (provider, digits))
    conn.commit()
    conn.close()
    return {"message": "Packet deleted."}


# ---------------------- OTHER TABLES ----------------------
def init_customer_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            digits TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def init_collected_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collected_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            digits TEXT,
            barcode TEXT,
            log_type TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    init_db()
    init_customer_table()
    init_collected_log()
    print("✅ Database initialized at", DB_PATH)
