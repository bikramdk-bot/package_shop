import sqlite3
from datetime import datetime

DB_PATH = "db/parcels.db"


# ---------------------- INIT ----------------------
def init_db():
    """Create the parcels table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parcels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            digits TEXT NOT NULL,
            barcode TEXT,
            status TEXT DEFAULT 'in_shop',
            scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------------------- INSERT ----------------------
def insert_parcel(provider, digits, barcode=None):
    """Insert a new parcel entry (only if not already in_shop)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM parcels
        WHERE provider = ? AND digits = ? AND status = 'in_shop'
    """, (provider, digits))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return {"warning": "Parcel already exists and is in_shop."}

    cursor.execute("""
        INSERT INTO parcels (provider, digits, barcode, status, scan_time)
        VALUES (?, ?, ?, 'in_shop', ?)
    """, (provider, digits, barcode, datetime.now()))
    conn.commit()
    conn.close()
    return {"message": "Parcel inserted successfully."}


# ---------------------- SEARCH ----------------------
def search_parcel(provider, digits):
    """Return all matching parcels."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider, digits, barcode, status, scan_time
        FROM parcels
        WHERE provider = ? AND digits = ?
        ORDER BY scan_time DESC
    """, (provider, digits))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------- UPDATE ----------------------
def update_status(provider, digits, new_status):
    """Mark a parcel as collected, held, etc."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE parcels
        SET status = ?, scan_time = ?
        WHERE provider = ? AND digits = ?
    """, (new_status, datetime.now(), provider, digits))
    conn.commit()
    conn.close()
    return {"message": f"Status updated to {new_status}."}


# ---------------------- DELETE ----------------------
def delete_parcel(provider, digits):
    """Staff can manually delete a parcel record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM parcels
        WHERE provider = ? AND digits = ?
    """, (provider, digits))
    conn.commit()
    conn.close()
    return {"message": "Parcel deleted."}


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
