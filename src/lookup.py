import sqlite3
from datetime import datetime

DB_PATH = "db/packets.db"


def connect_db():
    """Return a connection to the local packets database."""
    return sqlite3.connect(DB_PATH)


def search_parcel(provider: str, digits: str):
    """Return parcel records matching provider and digits."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider, digits, status, scan_time
        FROM packets
        WHERE provider = ? AND digits = ?
    """, (provider, digits))
    rows = cursor.fetchall()
    conn.close()
    return rows


def insert_parcel(provider: str, digits: str, status: str = "in_shop"):
    """Insert a new parcel entry (scanner or manual)."""
    conn = connect_db()
    cursor = conn.cursor()

    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO packets (provider, digits, status, scan_time)
        VALUES (?, ?, ?, ?)
    """, (provider, digits, status, scan_time))

    conn.commit()
    conn.close()

    print(f"📦 Inserted: {provider} {digits} [{status}] @ {scan_time}")


def get_all_parcels(limit: int = 20):
    """Return the most recent parcels (for staff dashboard)."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, provider, digits, status, scan_time
        FROM packets
        ORDER BY scan_time DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
