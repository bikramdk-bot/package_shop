import sqlite3, os 
from datetime import datetime
from paths import resolve_data, init_dirs_and_migrate

# ✅ Same DB used by dashboard (externalized)
init_dirs_and_migrate()
DB_PATH = str(resolve_data("packets.db"))


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

    cursor.execute(
        """
        INSERT INTO packets (provider, digits, digit6, digit8, digit10, barcode, status, scan_time)
        VALUES (?, ?, ?, ?, ?, ?, 'in_shop', ?)
        """,
        (provider, digits, None, None, None, barcode, datetime.now()),
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
