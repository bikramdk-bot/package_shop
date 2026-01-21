from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from lookup import search_parcel, insert_parcel, update_status, delete_parcel
from license_manager import (
    ensure_token_db,
    ensure_default_license,
    get_current_expiry,
    apply_token,
)
import sqlite3, os
from datetime import datetime, timedelta, date
import threading, time
import json
import socket
import subprocess
import glob

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
app.config["PREFERRED_URL_SCHEME"] = "https"

# Use the exact same DB path as other modules (lookup.py/db_manager.py)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "packets.db")

# Default printer device (can be overridden by environment or request)
PRINTER_DEVICE = os.environ.get("PRINTER_DEVICE", "/dev/usb/lp0")


# Config path for shop info on Pi
SHOP_INFO_PATH = "/home/pi/config/shop_info.json"
SHOP_INFO_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "shop_info.json")

def read_shop_info():
    """Read shop configuration merging defaults and system overrides.

    Loads bundled defaults from src/shop_info.json, then overlays values from
    /home/pi/config/shop_info.json if present. Returns a dict (possibly empty).
    """
    data = {}
    # Load defaults bundled with app
    try:
        if os.path.exists(SHOP_INFO_DEFAULT_PATH):
            with open(SHOP_INFO_DEFAULT_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                data.update(d)
    except Exception:
        pass
    # Overlay with system config
    try:
        if os.path.exists(SHOP_INFO_PATH):
            with open(SHOP_INFO_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                data.update(d)
    except Exception:
        pass
    return data

def write_shop_info(patch: dict):
    data = read_shop_info()
    if not isinstance(data, dict):
        data = {}
    data.update(patch)
    os.makedirs(os.path.dirname(SHOP_INFO_PATH), exist_ok=True)
    with open(SHOP_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_cpu_serial():
    """Return Raspberry Pi CPU serial if available.

    Tries device-tree then /proc/cpuinfo. Returns None if not found.
    """
    # Device tree path (preferred on modern systems)
    try:
        p = "/sys/firmware/devicetree/base/serial-number"
        if os.path.exists(p):
            with open(p, "rb") as f:
                raw = f.read()
            s = raw.replace(b"\x00", b"").decode(errors="ignore").strip()
            if s:
                return s
    except Exception:
        pass
    # Fallback: parse /proc/cpuinfo
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.lower().startswith("serial\t:") or line.lower().startswith("serial:"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        s = parts[1].strip()
                        if s:
                            return s
    except Exception:
        pass
    return None

def get_shop_meta():
    cfg = read_shop_info() or {}
    shop_id = cfg.get("shop_id") if isinstance(cfg, dict) else None
    return {"shop_id": shop_id, "cpu_serial": get_cpu_serial()}

def _restart_api_service():
    # Restart the main systemd unit for this app.
    # Based on user confirmation, the unit name is package_shop.service.
    service = "package_shop.service"
    try:
        subprocess.check_output(["sudo", "systemctl", "restart", service], stderr=subprocess.STDOUT, text=True, timeout=10)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, f"systemctl failed: {e.output}"
    except Exception as e:
        return False, str(e)


def _build_zpl(lcn: str, digits: str) -> str:
    """Return ZPL for given LCN and digits."""
    now = datetime.now()
    today = f"{now.day}-{now.month}-{now.strftime('%y')}"
    return f"""^XA
^PW394
^LL236
^FO280,10^A0N,25,25^FD{today}^FS
^FO10,10^A0N,50,50^FD{lcn}^FS
^FO35,90^A0N,170,170^FD{digits}^FS
^XZ
"""


def _write_zpl_to_device(zpl: str, printer: str) -> None:
    """Send ZPL to a printer destination.

    Supports multiple strategies:
    - If `printer` is a writable path (e.g., /dev/usb/lp0), write directly.
    - If `printer` starts with "cups:" (e.g., cups:Zebra_ZD), use `lp -d <queue> -o raw`.
    - If `printer` looks like a CUPS queue name (no path separators), try `lp -d <queue> -o raw`.

    Raises an exception if all strategies fail.
    """
    dest = (printer or "").strip()
    data = zpl.encode("utf-8")

    # 1) Direct device write if path exists and is writable
    try:
        if dest and ("/" in dest or dest.startswith(".")) and os.path.exists(dest):
            # Ensure parent dir exists for file paths (no-op for device nodes)
            try:
                parent = os.path.dirname(dest)
                if parent:
                    os.makedirs(parent, exist_ok=True)
            except Exception:
                pass
            with open(dest, "wb") as p:
                p.write(data)
            return
    except Exception as e:
        last_err = e
    else:
        last_err = RuntimeError("Unknown print error")

    # 2) cups:<queue> explicit syntax
    if dest.lower().startswith("cups:"):
        queue = dest.split(":", 1)[1].strip()
        if not queue:
            raise ValueError("Invalid cups destination: missing queue name")
        try:
            proc = subprocess.run([
                "lp", "-d", queue, "-o", "raw"
            ], input=data, check=True)
            return
        except Exception as e:
            last_err = e

    # 3) Treat bare token (no slashes) as a CUPS queue name
    if dest and "/" not in dest and "\\" not in dest:
        try:
            proc = subprocess.run([
                "lp", "-d", dest, "-o", "raw"
            ], input=data, check=True)
            return
        except Exception as e:
            last_err = e

    # If we got here, all strategies failed
    raise (last_err if last_err else RuntimeError("Failed to print ZPL"))

@app.route("/list-scanners", methods=["GET"])
def list_scanners():
    # Find all by-id entries ending with event-kbd
    paths = sorted(glob.glob("/dev/input/by-id/*event-kbd"))
    names = [os.path.basename(p) for p in paths]
    current = read_shop_info().get("scanner_path")
    return jsonify({"available": names, "current": current})

@app.route("/set-scanner", methods=["POST"])
def set_scanner():
    try:
        payload = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400
    name = payload.get("scanner_path")
    if not isinstance(name, str) or not name:
        return jsonify({"ok": False, "error": "scanner_path required"}), 400
    full = f"/dev/input/by-id/{name}"
    # Update config without removing other fields
    try:
        write_shop_info({"scanner_path": full})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to write config: {e}"}), 500
    # Restart the api server service
    ok, err = _restart_api_service()
    if not ok:
        return jsonify({"ok": True, "warning": f"Scanner updated but restart failed: {err}"})
    return jsonify({"ok": True, "message": "Scanner updated, restarting system…"})


def _derive_variant_from_barcode(code, n):
    """Mirror 4-digit extraction rules for N in {6,8,10}.

    - If ends with two digits: use last N
    - If ends with two letters: take N before those two
    - If ends with digit+letter and len>=N+7: slice s[-(N+7):-7]
    - Else: fallback to last N if available
    """
    if not code:
        return None
    s = str(code).strip()
    if len(s) >= n and s[-2:].isdigit():
        return s[-n:]
    if len(s) >= n + 2 and s[-2:].isalpha():
        return s[-(n + 2):-2]
    if len(s) >= n + 7 and s[-1].isalpha() and s[-2].isdigit():
        return s[-(n + 7):-7]
    return s[-n:] if len(s) >= n else None

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
                digit6 TEXT,
                digit8 TEXT,
                digit10 TEXT,
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
                digit6 TEXT,
                digit8 TEXT,
                digit10 TEXT,
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
                digit6 TEXT,
                digit8 TEXT,
                digit10 TEXT,
                barcode TEXT,
                log_type TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Migration: ensure desired variant columns exist; handle legacy names
        for table in ("packets", "customer_entries", "collected_log"):
            cur.execute(f"PRAGMA table_info({table})")
            existing = [r[1] for r in cur.fetchall()]
            for col in ("digit6", "digit8", "digit10"):
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError:
                        pass
            # Rename legacy columns digits6/8/10 -> digit6/8/10 when needed
            cur.execute(f"PRAGMA table_info({table})")
            cols2 = [r[1] for r in cur.fetchall()]
            for legacy, want in (("digits6","digit6"),("digits8","digit8"),("digits10","digit10")):
                if legacy in cols2 and want not in cols2:
                    try:
                        cur.execute(f"ALTER TABLE {table} RENAME COLUMN {legacy} TO {want}")
                    except sqlite3.OperationalError:
                        pass
            # Drop legacy columns if both exist (best-effort; may be unsupported)
            cur.execute(f"PRAGMA table_info({table})")
            cols3 = [r[1] for r in cur.fetchall()]
            for legacy, want in (("digits6","digit6"),("digits8","digit8"),("digits10","digit10")):
                if legacy in cols3 and want in cols3:
                    try:
                        cur.execute(f"ALTER TABLE {table} DROP COLUMN {legacy}")
                    except sqlite3.OperationalError:
                        pass
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
        # Countdown will start upon number assignment
        cur.execute("PRAGMA table_info(customer_entries)")
        cols2 = [r[1] for r in cur.fetchall()]
        if 'number_assigned_at' not in cols2:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN number_assigned_at TEXT")
        if 'ticket_number' not in cols2:
            cur.execute("ALTER TABLE customer_entries ADD COLUMN ticket_number INTEGER")
        # Simple single-row counter for kiosk ticket numbers (1..99 roll-over)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kiosk_counter (
                id INTEGER PRIMARY KEY CHECK (id=1),
                last_number INTEGER DEFAULT 0
            )
            """
        )
        cur.execute("INSERT OR IGNORE INTO kiosk_counter (id, last_number) VALUES (1, 0)")
        # Settings table for global flags (e.g., print_enabled)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        # Ensure default print_enabled = 1 (true)
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('print_enabled', '1')")
        # Boot-time policy: always reset print mode to ON regardless of previous choice
        # This ensures printing starts enabled after any restart.
        try:
            cur.execute("UPDATE settings SET value='1' WHERE key='print_enabled'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    except sqlite3.OperationalError:
        # If locked during startup, ignore; next startup/run can add these.
        pass
    finally:
        conn.close()

    # Start background cleanup scheduler to remove old packets daily.
    try:
        start_cleanup_scheduler()
    except Exception:
        # non-fatal: if thread can't start, app still runs
        pass

    # Backfill digit6/8/10 for existing rows based on barcode (best-effort)
    try:
        conn = open_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, barcode, digit6, digit8, digit10 FROM packets
            WHERE barcode IS NOT NULL AND (digit6 IS NULL OR digit8 IS NULL OR digit10 IS NULL)
            """
        )
        rows = cur.fetchall()
        for rid, barcode, d6, d8, d10 in rows:
            n6 = d6 or _derive_variant_from_barcode(barcode, 6)
            n8 = d8 or _derive_variant_from_barcode(barcode, 8)
            n10 = d10 or _derive_variant_from_barcode(barcode, 10)
            cur.execute("UPDATE packets SET digit6=?, digit8=?, digit10=? WHERE id=?", (n6, n8, n10, rid))
        conn.commit()
        conn.close()
    except Exception:
        pass


def cleanup_old_packets():
    """Delete packets whose scan_time is older than 8 days.

    Uses SQLite builtin datetime('now','-8 days') so no timezone arithmetic in Python.
    Returns number of deleted rows.
    """
    conn = open_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM packets WHERE datetime(scan_time) <= datetime('now','-8 days')")
        row = cur.fetchone()
        to_delete = int(row[0] or 0)
        if to_delete > 0:
            cur.execute("DELETE FROM packets WHERE datetime(scan_time) <= datetime('now','-8 days')")
            conn.commit()
        return to_delete
    finally:
        conn.close()


def start_cleanup_scheduler(interval_hours: int = 24):
    """Start a daemon thread that runs cleanup_old_packets() once every `interval_hours` hours.

    The thread is best-effort (exceptions logged to stdout) and runs as a daemon so it
    doesn't block process exit.
    """
    def loop():
        while True:
            try:
                n = cleanup_old_packets()
                if n:
                    print(f"[cleanup] removed {n} packets older than 8 days")
            except Exception as e:
                print(f"[cleanup] error: {e}")
            # Sleep between runs; small sleep to allow quicker shutdown responsiveness
            for _ in range(max(1, int(interval_hours * 3600 / 5))):
                time.sleep(5)

    t = threading.Thread(target=loop, daemon=True)
    t.start()




def get_setting(key: str, default: str = None):
    conn = open_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            return row[0]
        return default
    finally:
        conn.close()


def set_setting(key: str, value: str):
    conn = open_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        conn.commit()
    finally:
        conn.close()

# -------- Offer text (Tilbud) --------
@app.route("/offer_text", methods=["GET"])
def get_offer_text():
    val = get_setting("offer_text", "")
    return jsonify({"offer_text": val or ""})

@app.route("/offer_text", methods=["POST"])
def set_offer_text():
    data = request.get_json(silent=True) or {}
    txt = (data.get("offer_text") or "").strip()
    try:
        # Empty string means clear
        set_setting("offer_text", txt)
        return jsonify({"ok": True, "offer_text": txt})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Ensure license token DB exists at startup (non-fatal if missing).
# NOTE: removed automatic license normalization on startup so expired
# licenses remain expired until explicitly extended by a token.
try:
    ensure_token_db()
    # do NOT call ensure_default_license() here; require explicit activation
except Exception as e:
    print(f"[startup] License initialization warning: {e}")

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
            # Choose column by input length: 4->digits, 6->digit6, 8->digit8, 10->digit10
            n = len(digs)
            if n >= 10:
                col = "digit10"
            elif n >= 8:
                col = "digit8"
            elif n >= 6:
                col = "digit6"
            else:
                col = "digits"
            # Build query: match by chosen column, with lenient suffix matching fallback
            q = f"""
                SELECT id, provider, digits, barcode FROM packets
                WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                  AND (
                        {col} = ?
                     OR {col} LIKE '%' || ?
                     OR ? LIKE '%' || COALESCE({col}, '')
                     OR barcode = ?
                     OR barcode LIKE '%' || ?
                  )
                ORDER BY datetime(scan_time) DESC
                LIMIT 50
            """
            c.execute(q, (prov, digs, digs, digs, digs, digs))
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
        # Start countdown only after number is assigned
        num_at = e["number_assigned_at"] if isinstance(e, sqlite3.Row) else None
        try:
            start_dt = datetime.strptime(num_at, "%Y-%m-%d %H:%M:%S") if num_at else None
        except Exception:
            start_dt = None
        if not start_dt:
            continue  # not started yet, do not expire
        hold_acc = int(e["hold_accumulated"] or 0)
        # if held, include ongoing hold duration, else only accumulated
        hold_total = hold_acc
        # not held now, so no extra ongoing hold
        effective_elapsed = (now - start_dt).total_seconds() - hold_total
        if effective_elapsed >= 300:
            c2 = conn.cursor()
            c2.execute(
                        """
                                                SELECT id, provider, digits, barcode FROM packets
                                                WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                                                    AND (
                                                                digits = ? OR digit6 = ? OR digit8 = ? OR digit10 = ?
                                                         OR ? LIKE '%' || digits OR ? LIKE '%' || digit6 OR ? LIKE '%' || digit8 OR ? LIKE '%' || digit10
                                                         OR digits LIKE '%' || ? OR digit6 LIKE '%' || ? OR digit8 LIKE '%' || ? OR digit10 LIKE '%' || ?
                                                    )
                                                ORDER BY datetime(scan_time) DESC
                                                LIMIT 1
                                                """,
                                                (e["provider"], e["digits"], e["digits"], e["digits"], e["digits"],
                                                 e["digits"], e["digits"], e["digits"], e["digits"],
                                                 e["digits"], e["digits"], e["digits"], e["digits"]),
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
                                    (c2.provider IN ('BRING') AND c2.kode = c.kode)
                                OR (c2.provider NOT IN ('BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
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
                                (c2.provider IN ('BRING') AND c2.kode = c.kode)
                            OR (c2.provider NOT IN ('BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
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
                                    AND c2.provider IN ('BRING')
                                    AND c2.kode = c.kode
                                ORDER BY c2.created_at ASC
                                LIMIT 1
                        )
                        WHERE c.collection_id IS NULL
                            AND c.provider IN ('BRING')
                            AND EXISTS (
                                SELECT 1 FROM customer_entries AS c2
                                WHERE c2.collection_id IS NOT NULL
                                    AND c2.provider IN ('BRING')
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
               hold_started_at, COALESCE(hold_accumulated,0) AS hold_accumulated,
               number_assigned_at, ticket_number
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
            """
            SELECT COUNT(*) FROM packets
            WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
              AND (
                    digits = ? OR digit6 = ? OR digit8 = ? OR digit10 = ?
                 OR ? LIKE '%' || digits OR ? LIKE '%' || digit6 OR ? LIKE '%' || digit8 OR ? LIKE '%' || digit10
                 OR digits LIKE '%' || ? OR digit6 LIKE '%' || ? OR digit8 LIKE '%' || ? OR digit10 LIKE '%' || ?
              )
            """,
            (
                e["provider"], e["digits"], e["digits"], e["digits"], e["digits"],
                e["digits"], e["digits"], e["digits"], e["digits"],
                e["digits"], e["digits"], e["digits"], e["digits"]
            )
        )
        e["matched"] = c2.fetchone()[0] > 0
        # remaining time starts after number_assigned_at
        start_str = e.get("number_assigned_at")
        start_dt = None
        if start_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                start_dt = None
        hold_acc = int(e.get("hold_accumulated") or 0)
        hold_total = hold_acc
        if e.get("status") == 'hold' and e.get("hold_started_at"):
            try:
                hold_started = datetime.strptime(e["hold_started_at"], "%Y-%m-%d %H:%M:%S")
                hold_total += int((now - hold_started).total_seconds())
            except Exception:
                pass
        if start_dt:
            effective_elapsed = (now - start_dt).total_seconds() - hold_total
            e["remaining"] = max(0, 300 - int(effective_elapsed))
        else:
            e["remaining"] = 300
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
        # Treat only BRING as kode-based grouping; UPS should behave like GLS
        if provider and provider.upper() == 'BRING':
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

    # 1️⃣ Identify expired (non-held) customer entries (only after number assignment)
    cursor.execute("""
        SELECT id, provider, digits FROM customer_entries
        WHERE status != 'hold'
          AND number_assigned_at IS NOT NULL
          AND number_assigned_at <= datetime('now', '-300 seconds')
    """)
    expired = cursor.fetchall()

    for e in expired:
        c2 = conn.cursor()

        # 2️⃣ Check if packet matched
        c2.execute(
                        """
                                                SELECT id, provider, digits, barcode FROM packets
                                                WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                                                    AND (
                                                                digits = ? OR digit6 = ? OR digit8 = ? OR digit10 = ?
                                                         OR ? LIKE '%' || digits OR ? LIKE '%' || digit6 OR ? LIKE '%' || digit8 OR ? LIKE '%' || digit10
                                                         OR digits LIKE '%' || ? OR digit6 LIKE '%' || ? OR digit8 LIKE '%' || ? OR digit10 LIKE '%' || ?
                                                    )
                                                ORDER BY datetime(scan_time) DESC
                                                LIMIT 1
                                                """,
                                                (e["provider"], e["digits"], e["digits"], e["digits"], e["digits"],
                                                 e["digits"], e["digits"], e["digits"], e["digits"],
                                                 e["digits"], e["digits"], e["digits"], e["digits"]))
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
        WHERE status != 'hold'
          AND number_assigned_at IS NOT NULL
          AND number_assigned_at <= datetime('now', '-300 seconds')
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
                                           (c2.provider IN ('BRING') AND c2.kode = c.kode)
                                     OR (c2.provider NOT IN ('BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
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
                                       (c2.provider IN ('BRING') AND c2.kode = c.kode)
                                 OR (c2.provider NOT IN ('BRING') AND c2.digits = c.digits AND c2.kode = c.kode)
                             )
                            )
            """
        )

                                # Bring case: their 5-digit code is stored in kode; propagate by provider+kode
        cursor.execute(
            """
            UPDATE customer_entries AS c
            SET collection_id = (
                SELECT c2.collection_id FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                                                                        AND c2.provider IN ('BRING')
                                    AND c2.kode = c.kode
                ORDER BY c2.created_at ASC
                LIMIT 1
            )
            WHERE c.collection_id IS NULL
                                                        AND c.provider IN ('BRING')
              AND EXISTS (
                SELECT 1 FROM customer_entries AS c2
                WHERE c2.collection_id IS NOT NULL
                                                                        AND c2.provider IN ('BRING')
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
               hold_started_at, COALESCE(hold_accumulated,0) AS hold_accumulated,
               number_assigned_at, ticket_number
        FROM customer_entries
        ORDER BY created_at DESC
        """
    )
    entries = [dict(r) for r in cursor.fetchall()]

    now2 = datetime.utcnow()
    for e in entries:
        # compute remaining considering holds
        # Countdown starts after number assignment
        start_dt = None
        if e.get("number_assigned_at"):
            try:
                start_dt = datetime.strptime(e["number_assigned_at"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                start_dt = None
        hold_total = int(e.get("hold_accumulated") or 0)
        if e.get("status") == 'hold' and e.get("hold_started_at"):
            try:
                hold_started = datetime.strptime(e["hold_started_at"], "%Y-%m-%d %H:%M:%S")
                hold_total += int((now2 - hold_started).total_seconds())
            except Exception:
                pass
        if start_dt:
            effective_elapsed = (now2 - start_dt).total_seconds() - hold_total
            e["remaining"] = max(0, 300 - int(effective_elapsed))
        else:
            e["remaining"] = 300
        e["held"] = e.get("status") == 'hold'

    # 5️⃣ Add match flag
    for e in entries:
        c2 = conn.cursor()
        prov_upper = (e.get("provider") or "").upper()
        # BRING entries are matched by their 5-digit kode (often stored in digits or barcode)
        if prov_upper == 'BRING' and e.get("kode"):
            kode = e.get("kode")
            c2.execute(
                """
                SELECT COUNT(*) FROM packets
                WHERE UPPER(provider)=UPPER(?) AND status='in_shop'
                  AND (digits = ? OR digits LIKE '%' || ? OR ? LIKE '%' || digits OR barcode = ? OR barcode LIKE '%' || ?)
                """,
                (e["provider"], kode, kode, kode, kode, kode),
            )
        else:
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
                            AND (
                                        digits = ? OR digit6 = ? OR digit8 = ? OR digit10 = ?
                                 OR ? LIKE '%' || digits OR ? LIKE '%' || digit6 OR ? LIKE '%' || digit8 OR ? LIKE '%' || digit10
                                 OR digits LIKE '%' || ? OR digit6 LIKE '%' || ? OR digit8 LIKE '%' || ? OR digit10 LIKE '%' || ?
                            )
                        ORDER BY datetime(scan_time) DESC
                        LIMIT 1
                        """,
                        (provider, digits, digits, digits, digits,
                         digits, digits, digits, digits,
                         digits, digits, digits, digits),
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
    # Normalize provider labels for display
    canon = {
        'POSTNORD': 'PostNord',
        'DAO': 'DAO',
        'GLS': 'GLS',
        'BRING': 'Bring',
        'UPS': 'UPS',
        'DHL': 'DHL'
    }
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        prov = (d.get('provider') or '').strip()
        d['provider'] = canon.get(prov.upper(), prov)
        # expose entry_date as an alias for scan_time so UI can use a stable name
        d['entry_date'] = d.get('scan_time')
        rows.append(d)
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


@app.route("/print_label", methods=["POST"])
def print_label():
    """Print a label using ZPL. Expects JSON { lcn, digits, printer_device (optional) }.
    This mirrors the ZPL used by the local `scanner_listener.py` so the scanner can POST
    the label payload to the API instead of writing the device directly.
    """
    data = request.get_json(force=True) or {}
    lcn = (data.get("lcn") or "").strip()
    digits = (data.get("digits") or "").strip()
    printer = (data.get("printer_device") or "").strip() or PRINTER_DEVICE

    if not lcn or not digits:
        return jsonify({"error": "Missing lcn or digits"}), 400


    # Build a date string similar to the scanner helper (avoid platform-specific %- modifiers)
    zpl = _build_zpl(lcn, digits)
    try:
        _write_zpl_to_device(zpl, printer)
    except Exception as e:
        return jsonify({"error": "Failed to write to printer device", "details": str(e)}), 500

    return jsonify({"status": "printed", "lcn": lcn, "digits": digits, "printer": printer})


@app.route("/scan_and_print", methods=["POST"])
def scan_and_print():
    """Insert a scanned parcel into the DB and print a label.

    Expects JSON: { provider (optional), lcn, digits, barcode (optional), printer_device (optional) }
    Returns combined JSON with DB result and print status.
    """
    data = request.get_json(force=True) or {}
    provider = (data.get("provider") or "").strip() or "UNKNOWN"
    lcn = (data.get("lcn") or "").strip()
    digits = (data.get("digits") or "").strip()
    barcode = (data.get("barcode") or "").strip() or None
    printer = (data.get("printer_device") or "").strip() or PRINTER_DEVICE

    # Require digits; allow lcn to be omitted (scanner sends provider instead).
    if not digits:
        return jsonify({"error": "Missing digits"}), 400

    # If caller didn't include explicit 'lcn', fall back to the provided 'provider'
    # (scanner sends 'provider' but not 'lcn'). This preserves backward compatibility.
    if not lcn:
        lcn = provider


    # Insert into DB (lookup.insert_parcel returns a dict with message or warning)
    try:
        db_result = insert_parcel(provider, digits, barcode)
    except Exception as e:
        return jsonify({"error": "DB insert failed", "details": str(e)}), 500

    # Determine printing behavior: request may include explicit 'print' boolean.
    # If absent, fall back to server-side setting 'print_enabled'.
    req_print = data.get('print', None)
    if req_print is None:
        val = get_setting('print_enabled', '1')
        try:
            do_print = bool(int(val))
        except Exception:
            do_print = True
    else:
        do_print = bool(req_print)

    # Print label if enabled
    printed_info = None
    if do_print:
        try:
            zpl = _build_zpl(lcn, digits)
            _write_zpl_to_device(zpl, printer)
            printed_info = {"lcn": lcn, "digits": digits, "printer": printer}
        except Exception as e:
            return jsonify({"error": "Printed failed", "details": str(e), "db": db_result}), 500

    return jsonify({"status": "ok", "db": db_result, "printed": printed_info})


@app.route("/print_mode", methods=["GET"])
def get_print_mode():
    """Return current server-side print mode as JSON: { print: true|false }"""
    val = get_setting('print_enabled', '1')
    try:
        enabled = bool(int(val))
    except Exception:
        enabled = True
    return jsonify({"print": enabled})


@app.route("/print_mode", methods=["POST"])
def set_print_mode():
    """Set server-side print mode. Expects JSON { print: true|false }"""
    data = request.get_json(force=True) or {}
    p = data.get('print')
    if p is None:
        return jsonify({"error": "Missing 'print' boolean in request body"}), 400
    try:
        val = '1' if bool(p) else '0'
        set_setting('print_enabled', val)
    except Exception as e:
        return jsonify({"error": "Failed to set print mode", "details": str(e)}), 500
    return jsonify({"print": bool(p)})

 

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
        'UPS': 'UPS',
        'DHL': 'DHL'
    }
    provider = canon.get(provider.upper(), provider)

    if not provider:
        return jsonify({"error": "Missing provider"}), 400
    # Provider-specific kode rules
    # Bring requires a 5-digit kode; UPS should behave like GLS (no kode requirement)
    if provider == "Bring":
        if not kode or not kode.isdigit() or len(kode) != 5:
            return jsonify({"error": "Bring requires 5-digit kode"}), 400
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
        # Group by provider+kode for Bring only, else provider+digits(+kode)
        for r in rows:
            prov = r["provider"]
            digs = r["digits"]
            kode = r["kode"]
            if prov and prov.upper() == "BRING" and kode:
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
        'POSTNORD': 'PostNord', 'DAO': 'DAO', 'GLS': 'GLS', 'BRING': 'Bring', 'UPS': 'UPS', 'DHL': 'DHL'
    }
    provider = canon.get(provider.upper(), provider)
    if not provider:
        return jsonify({"error": "Missing provider"}), 400

    conn = open_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Try to find existing collection_id for this group
    # For Bring look up by kode; UPS should be treated like GLS (digits-based)
    if provider and provider.upper() == "BRING":
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

    if provider and provider.upper() == "BRING":
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

# ---------------------- KIOSK: CUSTOMER NUMBER (1..99) ----------------------
@app.route("/assign_customer_number", methods=["POST"]) 
def assign_customer_number():
    data = request.get_json(silent=True) or {}
    entry_ids = data.get("entry_ids")

    conn = open_db()
    cur = conn.cursor()
    # Ensure the single row exists
    cur.execute("INSERT OR IGNORE INTO kiosk_counter (id, last_number) VALUES (1, 0)")
    # Use an immediate transaction to avoid race conditions for concurrent requests
    try:
        cur.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        # If cannot escalate lock, continue; UPDATE should still serialize under busy_timeout
        pass
    cur.execute("SELECT last_number FROM kiosk_counter WHERE id=1")
    row = cur.fetchone()
    last = int(row[0]) if row and row[0] is not None else 0
    new_num = (last % 99) + 1
    cur.execute("UPDATE kiosk_counter SET last_number=? WHERE id=1", (new_num,))
    # If provided, mark the listed entries as having started countdown now, and store ticket number
    if isinstance(entry_ids, list) and entry_ids:
        placeholders = ",".join(["?"] * len(entry_ids))
        cur.execute(
            f"""
            UPDATE customer_entries
            SET number_assigned_at = strftime('%Y-%m-%d %H:%M:%S','now'),
                ticket_number = ?
            WHERE id IN ({placeholders})
            """,
            [new_num, *entry_ids]
        )
    conn.commit()
    conn.close()
    return jsonify({"number": new_num})

# ---------------------- STAFF DASHBOARD + APIs ----------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/staff", methods=["GET"])
def staff_dashboard():
    info = get_current_expiry()
    meta = get_shop_meta()
    return render_template(
        "staff_dashboard.html",
        expiry=info.expiry_str,
        message=None,
        success=None,
        shop_id=meta.get("shop_id"),
        cpu_serial=meta.get("cpu_serial"),
    )


@app.route("/activate", methods=["POST"])
def activate_token():
    # Accept token from form or JSON
    token = (request.form.get("token") if request.form else None) or (
        (request.get_json(silent=True) or {}).get("token")
    )
    if not token:
        info = get_current_expiry()
        meta = get_shop_meta()
        return render_template(
            "staff_dashboard.html",
            expiry=info.expiry_str,
            message="Missing token",
            success=False,
            shop_id=meta.get("shop_id"),
            cpu_serial=meta.get("cpu_serial"),
        ), 400

    success, message, info = apply_token(token)

    if request.is_json:
        payload = {"success": success, "message": message, "expiry": (info.expiry_str if info else get_current_expiry().expiry_str)}
        return jsonify(payload), (200 if success else 400)

    final_info = info or get_current_expiry()
    meta = get_shop_meta()
    return render_template(
        "staff_dashboard.html",
        expiry=final_info.expiry_str,
        message=message,
        success=success,
        shop_id=meta.get("shop_id"),
        cpu_serial=meta.get("cpu_serial"),
    ), (200 if success else 400)

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
    # Normalize provider labels for UI display (do not modify DB)
    canon = {
        'POSTNORD': 'PostNord',
        'DAO': 'DAO',
        'GLS': 'GLS',
        'BRING': 'Bring',
        'UPS': 'UPS',
        'DHL': 'DHL'
    }
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        prov = (d.get('provider') or '').strip()
        d['provider'] = canon.get(prov.upper(), prov)
        rows.append(d)
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
        WHERE UPPER(provider) = UPPER(?) AND digits = ?
        """,
        (new_status, datetime.now(), provider, digits),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Status updated to {new_status}."})

@app.route("/delete_parcel", methods=["POST"])
def delete_parcel_api():
    data = request.get_json(force=True)
    try:
        row_id = int(data.get("id"))
    except Exception:
        return jsonify({"error": "Missing or invalid id"}), 400

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM packets
        WHERE id = ?
        """,
        (row_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Packet deleted."})

# ---------------------- LICENSE STATUS (for UI gating) ----------------------
@app.route("/license_status")
def license_status():
    try:
        info = get_current_expiry()
        today = date.today()
        exp_dt = datetime.strptime(info.expiry_str, "%Y-%m-%d").date()
        active = today <= exp_dt
        return jsonify({
            "expiry": info.expiry_str,
            "today": today.strftime("%Y-%m-%d"),
            "active": active
        })
    except Exception as e:
        return jsonify({"error": "license_status_failed", "detail": str(e)}), 500

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
        'UPS': 'UPS',
        'DHL': 'DHL'
    }
    provider = canon.get(provider.upper(), provider)
    result = insert_parcel(provider, digits, barcode)
    status = 200 if "message" in result else 409 if "warning" in result else 400
    return jsonify(result), status


if __name__ == "__main__":
    # Run lightweight migrations once at startup to avoid ALTER TABLE during traffic
    run_migrations()
    print("🚀 API Server running with packets.db")
    # Disable the Werkzeug reloader so startup actions (like launching scanner)
    # aren't executed twice (parent + child) which can cause exclusive device
    # grabs to fail. If you rely on the reloader, start the scanner only when
    # WERKZEUG_RUN_MAIN=="true".
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
