from flask import Flask, request, jsonify
from lookup import search_parcel, insert_parcel

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

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    insert_parcel(provider, digits)
    return jsonify({"status": "inserted", "provider": provider, "digits": digits})

# ---------------------- UPDATE STATUS ----------------------
@app.route("/update_status", methods=["POST"])
def update_status_api():
    """
    Staff marks parcel as collected, held, etc.
    Example:
    {"provider": "PostNord", "digits": "7890", "status": "collected"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")
    new_status = data.get("status")

    if not provider or not digits or not new_status:
        return jsonify({"error": "Missing provider, digits, or status"}), 400

    from lookup import update_status
    result = update_status(provider, digits, new_status)
    return jsonify(result)


# ---------------------- DELETE PARCEL ----------------------
@app.route("/delete_parcel", methods=["POST"])
def delete_parcel_api():
    """
    Staff manually deletes a parcel record.
    Example:
    {"provider": "PostNord", "digits": "7890"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    from lookup import delete_parcel
    result = delete_parcel(provider, digits)
    return jsonify(result)


# ---------------------- HEALTH ----------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

from flask import render_template
from lookup import search_parcel

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/all_parcels")
def all_parcels():
    """Return all parcels in the DB."""
    import sqlite3
    conn = sqlite3.connect("db/parcels.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parcels ORDER BY scan_time DESC;")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)
import sqlite3
from datetime import datetime, timedelta

# ---------------------- CUSTOMER ENTRY ----------------------
@app.route("/customer_entry", methods=["POST"])
def customer_entry():
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")
    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    conn = sqlite3.connect("db/parcels.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customer_entries (provider, digits, status)
        VALUES (?, ?, 'pending')
    """, (provider, digits))
    conn.commit()
    conn.close()
    return jsonify({"message": "Customer entry recorded."})


@app.route("/customer_entries")
def get_customer_entries():
    """Fetch live customer entries, match against parcels, and clean old ones."""
    import sqlite3

    conn = sqlite3.connect("db/parcels.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1️⃣ Find expired entries (>120s) that are NOT held
    cursor.execute("""
        SELECT id, provider, digits FROM customer_entries
        WHERE status != 'hold' AND created_at <= datetime('now', '-120 seconds')
    """)
    expired = cursor.fetchall()

    # 2️⃣ For each expired entry, if it matched a parcel, delete parcel as collected
    for e in expired:
        c2 = conn.cursor()
        c2.execute("""
            SELECT id FROM parcels
            WHERE provider=? AND digits=? AND status='in_shop'
        """, (e["provider"], e["digits"]))
        parcel = c2.fetchone()
        if parcel:
            # delete parcel (collected)
            c2.execute("DELETE FROM parcels WHERE id=?", (parcel["id"],))
            print(f"Deleted parcel {parcel['id']} (collected by customer)")

    # 3️⃣ Delete expired customer entries
    cursor.execute("""
        DELETE FROM customer_entries
        WHERE status != 'hold' AND created_at <= datetime('now', '-120 seconds')
    """)

    # 4️⃣ Fetch active entries
    cursor.execute("SELECT * FROM customer_entries ORDER BY created_at DESC")
    entries = [dict(r) for r in cursor.fetchall()]

    # 5️⃣ Add match info
    for e in entries:
        c2 = conn.cursor()
        c2.execute("""
            SELECT COUNT(*) FROM parcels
            WHERE provider=? AND digits=?
        """, (e["provider"], e["digits"]))
        e["matched"] = c2.fetchone()[0] > 0

    conn.commit()
    conn.close()
    return jsonify(entries)


@app.route("/hold_entry", methods=["POST"])
def hold_entry():
    """Mark a customer entry as hold."""
    data = request.get_json(force=True)
    entry_id = data.get("id")
    conn = sqlite3.connect("db/parcels.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE customer_entries SET status='hold' WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Entry held."})

@app.route("/customer")
def customer_page():
    return render_template("customer.html")

@app.route("/live_customers")
def live_customers():
    return render_template("live_customers.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
