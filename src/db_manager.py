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
            digit6 TEXT,
            digit8 TEXT,
            digit10 TEXT,
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
            digit6 TEXT,
            digit8 TEXT,
            digit10 TEXT,
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
        digit6 TEXT,
        digit8 TEXT,
        digit10 TEXT,
        barcode TEXT,
        log_type TEXT DEFAULT 'auto_match',
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Lightweight migration: ensure variant columns exist if DB predated change
    for table in ("packets", "customer_entries", "collected_log"):
        try:
            c.execute(f"PRAGMA table_info({table})")
            existing_cols = [r[1] for r in c.fetchall()]
            for col in ("digit6", "digit8", "digit10"):
                if col not in existing_cols:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
        except Exception:
            pass


    conn.commit()
    conn.close()
    print("✅ Database initialized at", DB_PATH)


if __name__ == "__main__":
    init_db()
