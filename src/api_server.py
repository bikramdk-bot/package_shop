from flask import Flask, request, jsonify, render_template
from lookup import search_parcel, insert_parcel, update_status, delete_parcel
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
        cur.execute("PRAGMA table_info(customer_entries)")
        cols = [r[1] for r in cur.fetchall()]
        if 'kode' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN kode TEXT")
        if 'collection_id' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN collection_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # If locked during startup, ignore; next startup/run can add these.
        pass
    finally:
        conn.close()

# ---------------------- LOOKUP ----------------------
@app.route("/lookup", methods=["GET", "POST"])
def lookup_parcel():
    """
    Customer tablet sends either:
    POST JSON: {"provider": "PostNord", "digits": "1234"}
    or
    GET params: /lookup?provider=PostNord&digits=1234
    """
    if request.method == "GET":
        provider = request.args.get("provider")
        digits = request.args.get("digits")
    else:
        data = request.get_json(force=True)
        provider = data.get("provider")
        digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    results = search_parcel(provider, digits)
    return jsonify({"results": results})


# ---------------------- INSERT ----------------------
@app.route("/insert", methods=["POST"])
def insert_parcel_api():
    """
    For manual add or future scanner API call:
    {"provider": "DAO", "digits": "5678"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")
    barcode = data.get("barcode")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    result = insert_parcel(provider, digits, barcode)
    return jsonify(result)


# ---------------------- UPDATE STATUS ----------------------
@app.route("/update_status", methods=["POST"])
def update_status_api():
    """
    Staff marks packet as collected, held, etc.
    Example:
    {"provider": "PostNord", "digits": "7890", "status": "collected"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")
    new_status = data.get("status")

    if not provider or not digits or not new_status:
        return jsonify({"error": "Missing provider, digits, or status"}), 400

    result = update_status(provider, digits, new_status)
    return jsonify(result)


# ---------------------- DELETE ----------------------
@app.route("/delete_parcel", methods=["POST"])
def delete_parcel_api():
    """
    Staff manually deletes a packet record.
    Example:
    {"provider": "PostNord", "digits": "7890"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    result = delete_parcel(provider, digits)
    return jsonify(result)


# ---------------------- HEALTH ----------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


# ---------------------- DASHBOARD ----------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/all_parcels")
def all_parcels():
    """Return all packets in the DB."""
    conn = open_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packets ORDER BY scan_time DESC;")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)


# ---------------------- CUSTOMER ENTRY ----------------------
@app.route("/customer_entry", methods=["POST"])
def customer_entry():
    data = request.get_json(force=True)
    provider = (data.get("provider") or "").strip()
    digits = (data.get("digits") or "").strip()
    kode = (data.get("kode") or "").strip()
    collection_id = (data.get("collection_id") or "").strip()

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    conn = open_db()
    cursor = conn.cursor()

    provider_upper = provider.upper()

    # Check if there's a matching packet (provider + digits) currently in shop
    if provider_upper == 'UPS':
        # UPS uses a 5-digit collection code; we accept the entry without requiring a packet match
        matched = True
    else:
        cursor.execute("SELECT COUNT(*) FROM packets WHERE provider=? AND digits=? AND status='in_shop'", (provider, digits))
        matched = cursor.fetchone()[0] > 0

    if not matched:
        # No match -> inform customer (front-end should display red message)
        conn.close()
        return jsonify({"message": "No match found for those details.", "matched": False}), 200

    # If provider is DAO, require a 5-digit numeric kode
    if provider_upper == 'DAO':
        if not kode or not kode.isdigit() or len(kode) != 5:
            conn.close()
            return jsonify({"message": "DAO requires a 5-digit collection code.", "matched": True, "require_kode": True}), 200

    # Save the customer entry including kode if provided
    cursor.execute("""
    INSERT INTO customer_entries (provider, digits, kode, collection_id, status, created_at)
    VALUES (?, ?, ?, ?, 'pending', datetime('now'))
    """, (provider, digits, kode if kode else None, collection_id if collection_id else None))
    entry_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return jsonify({"message": "Customer entry recorded.", "matched": True, "entry_id": entry_id})


# ---------------------- ASSIGN COLLECTION ID ----------------------
@app.route("/assign_collection", methods=["POST"])
def assign_collection():
    data = request.get_json(force=True)
    entry_ids = data.get("entry_ids") or []
    collection_id = (data.get("collection_id") or "").strip()

    if not isinstance(entry_ids, list) or len(entry_ids) == 0 or not collection_id:
        return jsonify({"error": "Missing entry_ids or collection_id"}), 400

    conn = open_db()
    cursor = conn.cursor()

    # First, set the collection_id for the specified entry ids
    placeholders = ",".join(["?"] * len(entry_ids))
    params = [collection_id] + entry_ids
    cursor.execute(f"""
        UPDATE customer_entries
        SET collection_id = ?
        WHERE id IN ({placeholders})
    """, params)
    updated = cursor.rowcount

    # Then, propagate collection_id to matching group entries that are currently visible (not held)
    # Non-UPS: provider+digits+kode match; UPS: provider='UPS' + digits match
    # Derive all distinct groups represented by entry_ids and propagate per group.
    cursor.execute(f"SELECT DISTINCT provider, digits, kode FROM customer_entries WHERE id IN ({placeholders})", entry_ids)
    groups = cursor.fetchall()
    for g in groups:
        provider, digits, kode = g
        if provider == 'UPS':
            cursor.execute(
                """
                UPDATE customer_entries
                SET collection_id = ?
                WHERE collection_id IS NULL
                  AND status != 'hold'
                  AND provider = 'UPS'
                  AND digits = ?
                """,
                (collection_id, digits)
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
        c2.execute("""
            SELECT id, provider, digits, barcode FROM packets
            WHERE provider=? AND digits=? AND status='in_shop'
        """, (e["provider"], e["digits"]))
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
    
    # 3.5️⃣ Backfill collection_id for entries that share the same digits + kode (LCN)
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
                  AND c2.digits = c.digits
                  AND c2.kode = c.kode
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
                  AND c2.digits = c.digits
                  AND c2.kode = c.kode
              )
            """
        )

        # UPS case: their 5-digit code is provided as 'digits' and kode is NULL.
        # Propagate collection_id among UPS entries with the same digits.
        cursor.execute(
            """
            UPDATE customer_entries AS c
            SET collection_id = (
                SELECT c2.collection_id FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.provider = 'UPS'
                  AND c2.digits = c.digits
                ORDER BY c2.created_at ASC
                LIMIT 1
            )
            WHERE c.collection_id IS NULL
              AND c.provider = 'UPS'
              AND EXISTS (
                SELECT 1 FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                  AND c2.provider = 'UPS'
                  AND c2.digits = c.digits
              )
            """
        )
    except sqlite3.OperationalError:
        # In case of a transient lock, skip this backfill for now
        pass

    # 4️⃣ Fetch only *active* (non-held) entries for live view
    cursor.execute("""
        SELECT id, provider, digits, kode, collection_id, status, created_at
        FROM customer_entries
        WHERE status != 'hold'
        ORDER BY created_at DESC
    """)
    entries = [dict(r) for r in cursor.fetchall()]

    # 5️⃣ Add match flag
    for e in entries:
        c2 = conn.cursor()
        c2.execute("""
            SELECT COUNT(*) FROM packets
            WHERE provider=? AND digits=?
        """, (e["provider"], e["digits"]))
        e["matched"] = c2.fetchone()[0] > 0

    # 6️⃣ Convert created_at to ISO format for browser (so countdown works)
    for e in entries:
        if "created_at" in e and e["created_at"]:
            e["created_at"] = e["created_at"].replace(" ", "T") + "Z"

    conn.commit()
    conn.close()
    return jsonify(entries)


# ---------------------- HOLD ENTRY ----------------------
@app.route("/hold_entry", methods=["POST"])
def hold_entry():
    data = request.get_json(force=True)
    entry_id = data.get("entry_id")

    if not entry_id:
        return jsonify({"error": "Missing entry_id"}), 400

    conn = open_db()
    cursor = conn.cursor()

    # Update customer entry to 'hold'
    cursor.execute("""
        UPDATE customer_entries
        SET status = 'hold'
        WHERE id = ?
    """, (entry_id,))

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


if __name__ == "__main__":
    # Run lightweight migrations once at startup to avoid ALTER TABLE during traffic
    run_migrations()
    print("🚀 API Server running with packets.db")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
