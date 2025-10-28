from flask import Flask, request, jsonify, render_template
from lookup import search_parcel, insert_parcel, update_status, delete_parcel
from db_manager import init_db
import sqlite3, os
from datetime import datetime, timedelta

app = Flask(__name__)

# Use the exact same DB path as other modules (lookup.py/db_manager.py)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "packets.db")

# ---------- SQLite helpers ----------
def open_db():
    """Open a SQLite connection configured for concurrent reads/writes."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Enable WAL for better concurrency and set timeouts
    try:
        c.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("PRAGMA busy_timeout=5000")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("PRAGMA foreign_keys=ON")
    except sqlite3.OperationalError:
        pass
    return conn

def run_migrations():
    """One-time lightweight migrations: add missing columns if needed."""
    conn = open_db()
    cur = conn.cursor()
    try:
        # Ensure base tables exist
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                digits TEXT NOT NULL,
                barcode TEXT,
                status TEXT DEFAULT 'in_shop',
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                digits TEXT NOT NULL,
                kode TEXT,
                collection_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hold_started_at TEXT,
                hold_accumulated INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS collected_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT,
                digits TEXT,
                barcode TEXT,
                log_type TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute("PRAGMA table_info(customer_entries)")
        cols = [r[1] for r in cur.fetchall()]
        if 'kode' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN kode TEXT")
        if 'collection_id' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN collection_id TEXT")
        if 'hold_started_at' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN hold_started_at TEXT")
        if 'hold_accumulated' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN hold_accumulated INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        # If locked during startup, ignore; next startup/run can add these.
        pass
    finally:
        conn.close()


# Ensure the database and base tables exist as soon as the API module loads
try:
    init_db()
    run_migrations()
except Exception as e:
    # Don't crash the server if another process races to create/alter the DB
    print(f"[startup] DB initialization warning: {e}")

# ---------------------- LOOKUP ----------------------
@app.route("/lookup", methods=["GET", "POST"])
def lookup_parcel():
    """Fetch live customer entries, clean up expired, backfill IDs, and compute remaining time.
    Remaining time accounts for paused time while on hold.
    """
    # Fast path: when called with provider+digits (POST), return packet matches only (used by kiosk matching)
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        prov = (data.get("provider") or "").strip()
        digs = (data.get("digits") or "").strip()
        if prov and digs:
            conn = open_db()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                """
                SELECT id, provider, digits, barcode FROM packets
                WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                  AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)
                ORDER BY datetime(scan_time) DESC
                LIMIT 50
                """,
                (prov, digs, digs, digs),
            )
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return jsonify({"results": rows})

    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Load entries for expiry check
    cursor.execute(
        """
                                SELECT id, provider, digits, kode, collection_id, status, created_at,
               hold_started_at, COALESCE(hold_accumulated,0) AS hold_accumulated
        FROM customer_entries
        ORDER BY created_at ASC
        """
    )
    rows = cursor.fetchall()

    # Identify expired entries (status != 'hold') using effective elapsed time
    now = datetime.utcnow()
    expired_ids = []
    for e in rows:
        if e["status"] == 'hold':
            continue
        try:
            created_dt = datetime.strptime(e["created_at"], "%Y-%m-%d %H:%M:%S") if e["created_at"] else now
        except Exception:
            created_dt = now
        hold_acc = int(e["hold_accumulated"] or 0)
        # if held, include ongoing hold duration, else only accumulated
        hold_total = hold_acc
        # not held now, so no extra ongoing hold
        effective_elapsed = (now - created_dt).total_seconds() - hold_total
        if effective_elapsed >= 300:
            c2 = conn.cursor()
            c2.execute(
                        """
                        SELECT id, provider, digits, barcode FROM packets
                        WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                          AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)
                        ORDER BY datetime(scan_time) DESC
                        LIMIT 1
                        """,
                        (e["provider"], e["digits"], e["digits"], e["digits"]),
                    )
            packet = c2.fetchone()
            if packet:
                c2.execute(
                    """
                    INSERT INTO collected_log (provider, digits, barcode, log_type)
                    VALUES (?, ?, ?, 'collected')
                    """,
                    (packet["provider"], packet["digits"], packet["barcode"]),
                )
                c2.execute("DELETE FROM packets WHERE id=?", (packet["id"],))
            else:
                c2.execute(
                    """
                    INSERT INTO collected_log (provider, digits, log_type)
                    VALUES (?, ?, 'expired_unmatched')
                    """,
                    (e["provider"], e["digits"]),
                )
            expired_ids.append(e["id"])

    if expired_ids:
        placeholders = ",".join(["?"] * len(expired_ids))
        cursor.execute(f"DELETE FROM customer_entries WHERE id IN ({placeholders})", expired_ids)

    # Backfill collection_id across matching groups
    try:
        cursor.execute(
            """
            UPDATE customer_entries AS c
            SET collection_id = (
                SELECT c2.collection_id FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.kode IS NOT NULL
                  AND c2.provider = c.provider
                  AND (
                        (c2.provider IN ('UPS','BRING') AND c2.kode = c.kode)
                     OR (c2.provider NOT IN ('UPS','BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
                  )
                ORDER BY c2.created_at ASC
                LIMIT 1
            )
            WHERE c.collection_id IS NULL
              AND c.kode IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.kode IS NOT NULL
                  AND c2.provider = c.provider
                  AND (
                        (c2.provider IN ('UPS','BRING') AND c2.kode = c.kode)
                     OR (c2.provider NOT IN ('UPS','BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
                  )
              )
            """
        )
        cursor.execute(
            """
            UPDATE customer_entries AS c
            SET collection_id = (
                SELECT c2.collection_id FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.provider IN ('UPS','BRING')
                  AND c2.kode = c.kode
                ORDER BY c2.created_at ASC
                LIMIT 1
            )
            WHERE c.collection_id IS NULL
              AND c.provider IN ('UPS','BRING')
              AND EXISTS (
                SELECT 1 FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.provider IN ('UPS','BRING')
                  AND c2.kode = c.kode
              )
            """
        )
    except sqlite3.OperationalError:
        pass

    # Fetch current entries (including held) and compute remaining/matched
    cursor.execute(
        """
        SELECT id, provider, digits, kode, collection_id, status, created_at,
               hold_started_at, COALESCE(hold_accumulated,0) AS hold_accumulated
        FROM customer_entries
        ORDER BY created_at DESC
        """
    )
    entries = [dict(r) for r in cursor.fetchall()]

    now = datetime.utcnow()
    for e in entries:
        # matched flag (only consider packets still in shop), case-insensitive provider
        c2 = conn.cursor()
        c2.execute(
            "SELECT COUNT(*) FROM packets WHERE UPPER(provider)=UPPER(?) AND status='in_shop' AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)",
            (e["provider"], e["digits"], e["digits"], e["digits"]))
        e["matched"] = c2.fetchone()[0] > 0
        # remaining time
        try:
            created_dt = datetime.strptime(e["created_at"].replace('T',' ').replace('Z',''), "%Y-%m-%d %H:%M:%S") if e.get("created_at") else now
        except Exception:
            try:
                created_dt = datetime.strptime(e["created_at"], "%Y-%m-%d %H:%M:%S") if e.get("created_at") else now
            except Exception:
                created_dt = now
        hold_acc = int(e.get("hold_accumulated") or 0)
        hold_total = hold_acc
        if e.get("status") == 'hold' and e.get("hold_started_at"):
            try:
                hold_started = datetime.strptime(e["hold_started_at"], "%Y-%m-%d %H:%M:%S")
                hold_total += int((now - hold_started).total_seconds())
            except Exception:
                pass
        effective_elapsed = (now - created_dt).total_seconds() - hold_total
        e["remaining"] = max(0, 300 - int(effective_elapsed))
        e["held"] = e.get("status") == 'hold'

    # Normalize created_at for browser
    for e in entries:
        if "created_at" in e and e["created_at"] and 'T' not in e["created_at"]:
            e["created_at"] = e["created_at"].replace(" ", "T") + "Z"

    conn.commit()
    conn.close()
    return jsonify(entries)
    for g in groups:
        provider, digits, kode = g
        if provider in ('UPS','BRING'):
            cursor.execute(
                """
                UPDATE customer_entries
                SET collection_id = ?
                WHERE collection_id IS NULL
                  AND status != 'hold'
                  AND provider = ?
                  AND kode = ?
                """,
                (collection_id, provider, kode)
            )
            updated += cursor.rowcount
        else:
            cursor.execute(
                """
                UPDATE customer_entries
                SET collection_id = ?
                WHERE collection_id IS NULL
                  AND status != 'hold'
                  AND provider = ?
                  AND digits = ?
                  AND ((kode IS NULL AND ? IS NULL) OR (kode = ?))
                """,
                (collection_id, provider, digits, kode, kode)
            )
            updated += cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({"updated": updated, "collection_id": collection_id})


# ---------------------- CUSTOMER ENTRIES (auto-match + logging) ----------------------
@app.route("/customer_entries")
def get_customer_entries():
    """Fetch live customer entries, match vs packets, and clean + log all outcomes."""
    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1️⃣ Identify expired (non-held) customer entries
    cursor.execute("""
        SELECT id, provider, digits FROM customer_entries
        WHERE status != 'hold' AND created_at <= datetime('now', '-300 seconds')
    """)
    expired = cursor.fetchall()

    for e in expired:
        c2 = conn.cursor()

        # 2️⃣ Check if packet matched
        c2.execute(
                        """
                        SELECT id, provider, digits, barcode FROM packets
                        WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                            AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)
                        ORDER BY datetime(scan_time) DESC
                        LIMIT 1
                        """,
                        (e["provider"], e["digits"], e["digits"], e["digits"]))
        packet = c2.fetchone()

        if packet:
            # ✅ Case 1: Matched → collected
            c2.execute("""
                INSERT INTO collected_log (provider, digits, barcode, log_type)
                VALUES (?, ?, ?, 'collected')
            """, (packet["provider"], packet["digits"], packet["barcode"]))
            c2.execute("DELETE FROM packets WHERE id=?", (packet["id"],))
            print(f"Logged and deleted packet {packet['id']}")
        else:
            # ❌ Case 2: No packet match → expired_unmatched
            c2.execute("""
                INSERT INTO collected_log (provider, digits, log_type)
                VALUES (?, ?, 'expired_unmatched')
            """, (e["provider"], e["digits"]))

    # 3️⃣ Delete expired customer entries
    cursor.execute("""
        DELETE FROM customer_entries
        WHERE status != 'hold' AND created_at <= datetime('now', '-300 seconds')
    """)
    
    # 3.5️⃣ Backfill collection_id for entries that share the same code (LCN)
    # This ensures a constant collection_id is shown on the live page for the same group.
    # Rule: If an entry has NULL collection_id but there exists another entry with the same
    # provider + digits + kode that has a non-NULL collection_id, propagate that (prefer the earliest one).
    try:
        cursor.execute(
            """
                        UPDATE customer_entries AS c
                        SET collection_id = (
                                SELECT c2.collection_id FROM customer_entries AS c2
                                WHERE c2.collection_id IS NOT NULL
                                    AND c2.kode IS NOT NULL
                                    AND c2.provider = c.provider
                                    AND (
                                                (c2.provider IN ('UPS','BRING') AND c2.kode = c.kode)
                                         OR (c2.provider NOT IN ('UPS','BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
                                    )
                                ORDER BY c2.created_at ASC
                                LIMIT 1
                        )
                        WHERE c.collection_id IS NULL
                            AND c.kode IS NOT NULL
                            AND EXISTS (
                                SELECT 1 FROM customer_entries AS c2
                                WHERE c2.collection_id IS NOT NULL
                                    AND c2.kode IS NOT NULL
                                    AND c2.provider = c.provider
                                    AND (
                                                (c2.provider IN ('UPS','BRING') AND c2.kode = c.kode)
                                         OR (c2.provider NOT IN ('UPS','BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
                                    )
                            )
            """
        )

                # UPS/Bring case: their 5-digit code is stored in kode; propagate by provider+kode
        cursor.execute(
            """
            UPDATE customer_entries AS c
            SET collection_id = (
                SELECT c2.collection_id FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                                    AND c2.provider IN ('UPS','BRING')
                                    AND c2.kode = c.kode
                ORDER BY c2.created_at ASC
                LIMIT 1
            )
            WHERE c.collection_id IS NULL
                            AND c.provider IN ('UPS','BRING')
              AND EXISTS (
                SELECT 1 FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                                    AND c2.provider IN ('UPS','BRING')
                                    AND c2.kode = c.kode
              )
            """
        )
    except sqlite3.OperationalError:
        # In case of a transient lock, skip this backfill for now
        pass

    # Build fresh entries list including held and computed remaining
    cursor.execute(
        """
        SELECT id, provider, digits, kode, collection_id, status, created_at,
               hold_started_at, COALESCE(hold_accumulated,0) AS hold_accumulated
        FROM customer_entries
        ORDER BY created_at DESC
        """
    )
    entries = [dict(r) for r in cursor.fetchall()]

    now2 = datetime.utcnow()
    for e in entries:
        # compute remaining considering holds
        try:
            created_dt = datetime.strptime(e["created_at"], "%Y-%m-%d %H:%M:%S") if e.get("created_at") else now2
        except Exception:
            created_dt = now2
        hold_total = int(e.get("hold_accumulated") or 0)
        if e.get("status") == 'hold' and e.get("hold_started_at"):
            try:
                hold_started = datetime.strptime(e["hold_started_at"], "%Y-%m-%d %H:%M:%S")
                hold_total += int((now2 - hold_started).total_seconds())
            except Exception:
                pass
        effective_elapsed = (now2 - created_dt).total_seconds() - hold_total
        e["remaining"] = max(0, 300 - int(effective_elapsed))
        e["held"] = e.get("status") == 'hold'

    # 5️⃣ Add match flag
    for e in entries:
        c2 = conn.cursor()
        c2.execute(
                        """
                        SELECT COUNT(*) FROM packets
                        WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                            AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)
                        """,
                        (e["provider"], e["digits"], e["digits"], e["digits"]))
        e["matched"] = c2.fetchone()[0] > 0

    # 6️⃣ Convert created_at to ISO format for browser (so countdown works)
    for e in entries:
        if "created_at" in e and e["created_at"]:
            e["created_at"] = e["created_at"].replace(" ", "T") + "Z"

    conn.commit()
    conn.close()
    return jsonify(entries)


# ---------------------- UNHOLD / RESOLVE ENTRY ----------------------
@app.route("/unhold_entry", methods=["POST"])
def unhold_entry():
    data = request.get_json(force=True)
    entry_id = data.get("entry_id")
    if not entry_id:
        return jsonify({"error": "Missing entry_id"}), 400

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute("SELECT hold_started_at, COALESCE(hold_accumulated,0) FROM customer_entries WHERE id=?", (entry_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Entry not found"}), 404
    hold_started_at, hold_accumulated = row
    add_secs = 0
    if hold_started_at:
        try:
            started = datetime.strptime(hold_started_at, "%Y-%m-%d %H:%M:%S")
            add_secs = int((datetime.utcnow() - started).total_seconds())
        except Exception:
            add_secs = 0
    cursor.execute(
        """
        UPDATE customer_entries
        SET status='pending', hold_started_at=NULL, hold_accumulated=COALESCE(hold_accumulated,0)+?
        WHERE id=?
        """,
        (add_secs, entry_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Entry {entry_id} resumed."})


@app.route("/resolve_entry", methods=["POST"])
def resolve_entry():
    data = request.get_json(force=True)
    entry_id = data.get("entry_id")
    action = (data.get("action") or "").strip().lower()
    if not entry_id or action not in ("collected", "keep"):
        return jsonify({"error": "Missing entry_id or invalid action"}), 400

    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_entries WHERE id=?", (entry_id,))
    entry = cursor.fetchone()
    if not entry:
        conn.close()
        return jsonify({"error": "Entry not found"}), 404

    if action == 'keep':
        # Remove the live entry and keep packet in shop (no auto-expiry will act without an entry)
        # Log the decision
        cursor.execute(
            """
            INSERT INTO collected_log (provider, digits, log_type)
            SELECT provider, digits, 'kept' FROM customer_entries WHERE id=?
            """,
            (entry_id,)
        )
        cursor.execute("DELETE FROM customer_entries WHERE id=?", (entry_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Entry {entry_id} kept in shop and removed from live."})

    # collected: try to log and delete packet if present, then remove entry
    provider = entry["provider"]
    digits = entry["digits"]
    c2 = conn.cursor()
    packet = None
    if provider and digits:
        c2.execute(
            """
            SELECT id, provider, digits, barcode FROM packets
            WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
              AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits)
            ORDER BY datetime(scan_time) DESC
            LIMIT 1
            """,
            (provider, digits, digits, digits),
        )
        packet = c2.fetchone()
    if packet:
        c2.execute(
            "INSERT INTO collected_log (provider, digits, barcode, log_type) VALUES (?, ?, ?, 'collected_staff')",
            (packet["provider"], packet["digits"], packet["barcode"]),
        )
        c2.execute("DELETE FROM packets WHERE id=?", (packet["id"],))
    else:
        c2.execute(
            "INSERT INTO collected_log (provider, digits, log_type) VALUES (?, ?, 'collected_staff')",
            (provider, digits),
        )
    # Remove the entry from the live list
    cursor.execute("DELETE FROM customer_entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Entry {entry_id} marked collected."})


# ---------------------- LOG DATA (JSON) ----------------------
@app.route("/collected_log_data")
def collected_log_data():
    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT provider, digits, barcode, log_type, collected_at
        FROM collected_log
        ORDER BY collected_at DESC
        LIMIT 500
        """
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)


# ---------------------- HOLD ENTRY ----------------------
@app.route("/hold_entry", methods=["POST"])
def hold_entry():
    data = request.get_json(force=True)
    entry_id = data.get("entry_id")

    if not entry_id:
        return jsonify({"error": "Missing entry_id"}), 400

    conn = open_db()
    cursor = conn.cursor()

    # Update customer entry to 'hold' and record start time
    cursor.execute(
        """
        UPDATE customer_entries
        SET status = 'hold', hold_started_at = strftime('%Y-%m-%d %H:%M:%S','now')
        WHERE id = ?
        """,
        (entry_id,),
    )

    # Log held action
    cursor.execute("""
        INSERT INTO collected_log (provider, digits, barcode, log_type)
        SELECT provider, digits, NULL, 'held'
        FROM customer_entries
        WHERE id = ?
    """, (entry_id,))

    conn.commit()
    conn.close()
    return jsonify({"message": f"Entry {entry_id} held and hidden from live list."})


# ---------------------- COLLECTED LOG ----------------------
@app.route("/collected_log")
def collected_log():
    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provider, digits, barcode, log_type, collected_at
        FROM collected_log
        ORDER BY collected_at DESC
        LIMIT 200
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template("collected_log.html", rows=rows)


# ---------------------- PAGES ----------------------
@app.route("/customer")
def customer_page():
    return render_template("customer.html")

@app.route("/live_customers")
def live_customers():
    return render_template("live_customers.html")

@app.route("/manual_label_page")
def manual_label_page():
    return render_template("manual_label.html")

# ---------------------- KIOSK: CREATE ENTRY + ASSIGN COLLECTION ----------------------
@app.route("/customer_entry", methods=["POST"])
def create_customer_entry():
    data = request.get_json(force=True)
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    kode = (data.get("kode") or "").strip() or None

    # Canonicalize provider labels
    canon = {
        'POSTNORD': 'PostNord',
        'DAO': 'DAO',
        'GLS': 'GLS',
        'BRING': 'Bring',
        'UPS': 'UPS'
    }
    provider = canon.get(provider.upper(), provider)

    if not provider:
        return jsonify({"error": "Missing provider"}), 400
    # Provider-specific kode rules
    if provider in ("UPS", "Bring", "BRING"):
        if not kode or not kode.isdigit() or len(kode) != 5:
            return jsonify({"error": "UPS/Bring require 5-digit kode"}), 400
    if provider == "DAO":
        if not kode or not kode.isdigit() or len(kode) != 5:
            return jsonify({"error": "DAO requires 5-digit kode"}), 400

    conn = open_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO customer_entries (provider, digits, kode, status, created_at)
        VALUES (?, ?, ?, 'pending', strftime('%Y-%m-%d %H:%M:%S','now'))
        """,
        (provider, digits, kode)
    )
    entry_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": entry_id, "provider": provider, "digits": digits, "kode": kode})

@app.route("/assign_collection", methods=["POST"])
def assign_collection():
    data = request.get_json(force=True)
    entry_ids = data.get("entry_ids")
    provided_cid = (data.get("collection_id") or "").strip() or None

    # Case 1: Assign by explicit entry_ids (preferred when customer clicks "No, finish")
    if entry_ids:
        if not isinstance(entry_ids, list) or len(entry_ids) == 0:
            return jsonify({"error": "entry_ids must be a non-empty list"}), 400
        conn = open_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Determine collection id (use provided or generate)
        if provided_cid:
            collection_id = provided_cid
        else:
            cur.execute("SELECT strftime('%Y%m%d%H%M%S','now')")
            base = cur.fetchone()[0]
            collection_id = f"C{base}"

        # Fetch entries for grouping and update all matching groups to share same collection_id
        placeholders = ",".join(["?"] * len(entry_ids))
        cur.execute(
            f"""
            SELECT id, provider, digits, kode, collection_id
            FROM customer_entries
            WHERE id IN ({placeholders})
            """,
            entry_ids,
        )
        rows = cur.fetchall()
        updated = 0
        # Group by provider+kode for UPS/Bring, else provider+digits(+kode)
        for r in rows:
            prov = r["provider"]
            digs = r["digits"]
            kode = r["kode"]
            if prov in ("UPS", "Bring") and kode:
                cur.execute(
                    """
                    UPDATE customer_entries
                    SET collection_id=?
                    WHERE provider=? AND kode=?
                    """,
                    (collection_id, prov, kode),
                )
            else:
                cur.execute(
                    """
                    UPDATE customer_entries
                    SET collection_id=?
                    WHERE provider=? AND digits=?
                      AND ((kode IS NULL AND ? IS NULL) OR kode=?)
                    """,
                    (collection_id, prov, digs, kode, kode),
                )
            updated += cur.rowcount
        conn.commit()
        conn.close()
        return jsonify({"updated": updated, "collection_id": collection_id})

    # Case 2: Backward-compatible assignment by provider/digits/kode
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    kode = (data.get("kode") or "").strip() or None

    canon = {
        'POSTNORD': 'PostNord', 'DAO': 'DAO', 'GLS': 'GLS', 'BRING': 'Bring', 'UPS': 'UPS'
    }
    provider = canon.get(provider.upper(), provider)
    if not provider:
        return jsonify({"error": "Missing provider"}), 400

    conn = open_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Try to find existing collection_id for this group
    if provider in ("UPS", "Bring"):
        cur.execute(
            """
            SELECT collection_id FROM customer_entries
            WHERE provider=? AND kode IS NOT NULL AND kode=? AND collection_id IS NOT NULL
            ORDER BY created_at ASC LIMIT 1
            """, (provider, kode)
        )
    else:
        cur.execute(
            """
            SELECT collection_id FROM customer_entries
            WHERE provider=? AND digits=? AND ((kode IS NULL AND ? IS NULL) OR kode=?) AND collection_id IS NOT NULL
            ORDER BY created_at ASC LIMIT 1
            """, (provider, digits, kode, kode)
        )
    row = cur.fetchone()
    collection_id = None
    if row and row["collection_id"]:
        collection_id = row["collection_id"]
    else:
        cur.execute("SELECT strftime('%Y%m%d%H%M%S','now')")
        base = cur.fetchone()[0]
        collection_id = f"C{base}"

    if provider in ("UPS", "Bring"):
        cur.execute(
            """
            UPDATE customer_entries
            SET collection_id=?
            WHERE provider=? AND kode=? AND (collection_id IS NULL)
            """, (collection_id, provider, kode)
        )
    else:
        cur.execute(
            """
            UPDATE customer_entries
            SET collection_id=?
            WHERE provider=? AND digits=? AND ((kode IS NULL AND ? IS NULL) OR kode=?) AND (collection_id IS NULL)
            """, (collection_id, provider, digits, kode, kode)
        )
    conn.commit()
    conn.close()
    return jsonify({"collection_id": collection_id})

# ---------------------- STAFF DASHBOARD + APIs ----------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/all_parcels")
def all_parcels():
    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, provider, digits, barcode, status, scan_time
        FROM packets
        ORDER BY datetime(scan_time) DESC
        """
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/update_status", methods=["POST"])
def update_status_api():
    data = request.get_json(force=True)
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    new_status = (data.get("status") or "").strip()
    if not provider or not digits or not new_status:
        return jsonify({"error": "Missing provider/digits/status"}), 400

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE packets
        SET status = ?, scan_time = ?
        WHERE provider = ? AND digits = ?
        """,
        (new_status, datetime.now(), provider, digits),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Status updated to {new_status}."})

@app.route("/delete_parcel", methods=["POST"])
def delete_parcel_api():
    data = request.get_json(force=True)
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    if not provider or not digits:
        return jsonify({"error": "Missing provider/digits"}), 400

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM packets
        WHERE provider = ? AND digits = ?
        """,
        (provider, digits),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Packet deleted."})

# ---------------------- PUBLIC INSERT (for scanner or curl) ----------------------
@app.route("/insert", methods=["POST"])
def insert_packet():
    # Accept JSON, form, or query params
    data = request.get_json(silent=True) or dict(request.form) or dict(request.args)
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    barcode = (data.get("barcode") or "").strip() or None
    if not provider or not digits:
        return jsonify({"error": "Missing provider/digits"}), 400

    # Normalize provider to canonical labels used by UI
    canon = {
        'POSTNORD': 'PostNord',
        'DAO': 'DAO',
        'GLS': 'GLS',
        'BRING': 'Bring',
        'UPS': 'UPS'
    }
    provider = canon.get(provider.upper(), provider)
    result = insert_parcel(provider, digits, barcode)
    status = 200 if "message" in result else 409 if "warning" in result else 400
    return jsonify(result), status


if __name__ == "__main__":
    # Create database and run lightweight migrations when launched directly
    init_db()
    run_migrations()
    print("🚀 API Server running with packets.db")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
