from flask import Flask, request, jsonify, render_template
from lookup import search_parcel, insert_parcel, update_status, delete_parcel
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

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
    conn = sqlite3.connect("db/packets.db")
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

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    # Ensure kode column exists for older DBs
    def ensure_kode_column(conn):
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(customer_entries)")
        cols = [r[1] for r in cur.fetchall()]
        if 'kode' not in cols:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN kode TEXT")
            conn.commit()

    conn = sqlite3.connect("db/packets.db")
    ensure_kode_column(conn)
    cursor = conn.cursor()

    # Check if there's a matching packet (provider + digits) currently in shop
    cursor.execute("SELECT COUNT(*) FROM packets WHERE provider=? AND digits=? AND status='in_shop'", (provider, digits))
    matched = cursor.fetchone()[0] > 0

    if not matched:
        # No match -> inform customer (front-end should display red message)
        conn.close()
        return jsonify({"message": "No match found for those details.", "matched": False}), 200

    # If provider is DAO, require a 5-digit numeric kode
    if provider.upper() == 'DAO':
        if not kode or not kode.isdigit() or len(kode) != 5:
            conn.close()
            return jsonify({"message": "DAO requires a 5-digit collection code.", "matched": True, "require_kode": True}), 200

    # Save the customer entry including kode if provided
    cursor.execute("""
    INSERT INTO customer_entries (provider, digits, kode, status, created_at)
    VALUES (?, ?, ?, 'pending', datetime('now'))
    """, (provider, digits, kode if kode else None))

    conn.commit()
    conn.close()
    return jsonify({"message": "Customer entry recorded.", "matched": True})


# ---------------------- CUSTOMER ENTRIES (auto-match + logging) ----------------------
@app.route("/customer_entries")
def get_customer_entries():
    """Fetch live customer entries, match vs packets, and clean + log all outcomes."""
    conn = sqlite3.connect("db/packets.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1️⃣ Identify expired (non-held) customer entries
    cursor.execute("""
        SELECT id, provider, digits FROM customer_entries
        WHERE status != 'hold' AND created_at <= datetime('now', '-120 seconds')
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
        WHERE status != 'hold' AND created_at <= datetime('now', '-120 seconds')
    """)

    # 4️⃣ Fetch only *active* (non-held) entries for live view
    cursor.execute("""
        SELECT * FROM customer_entries
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

    conn = sqlite3.connect("db/packets.db")
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
    conn = sqlite3.connect("db/packets.db")
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
    print("🚀 API Server running with packets.db")
    app.run(host="0.0.0.0", port=5000, debug=True)
