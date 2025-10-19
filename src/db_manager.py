import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "packets.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 📨 Packets table
    c.execute("""
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            digits TEXT,
            barcode TEXT,
            status TEXT DEFAULT 'in_shop',
            scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 👥 Customer entries table
    c.execute("""
        CREATE TABLE IF NOT EXISTS customer_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            digits TEXT,
            kode TEXT,
            collection_id TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 🗒️ Collected log table
    c.execute("""
    CREATE TABLE IF NOT EXISTS collected_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider TEXT,
        digits TEXT,
        barcode TEXT,
        log_type TEXT DEFAULT 'auto_match',
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    conn.commit()
    conn.close()
    print("✅ Database initialized at", DB_PATH)


if __name__ == "__main__":
    init_db()
