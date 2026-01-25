"""License management for simplified offline token system.

Responsibilities:
- Manage shop_id (shop_info.json)
- Manage license.json with expiry
- Ensure token DB exists (token_db.sqlite)
- Validate and apply tokens (non-reusable, shop-locked)

Token format: <shop_id>-<months>M-<rand4>-<mac6>
- mac6 = first 6 hex chars of HMAC-SHA256(SECRET_SALT, f"{shop_id}|{months}|{rand4}|{cpu_id}")

All paths are resolved relative to this file's directory.
"""
from __future__ import annotations

import os
import json
import base64
import sqlite3
import hashlib
import hmac
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Tuple

# Shared secret salt (prefer environment variable in production)
SECRET_SALT = os.environ.get("PACKAGE_SHOP_SECRET_SALT") or "SALT1234"
if SECRET_SALT == "SALT1234":
    # Informative message for developers (no secret management in repo)
    print("[License] WARNING: using default SECRET_SALT; set PACKAGE_SHOP_SECRET_SALT in env for production")

# Device CPU id binding: no default. This module is intended to run on the Raspberry Pi
# and will detect the device serial from /proc/cpuinfo. Tokens are Pi-only.
DEVICE_CPU_ID = os.environ.get("PACKAGE_SHOP_CPU_ID") or None

# Base directory (src/)
BASE_DIR = Path(__file__).resolve().parent
TOKEN_DB_PATH = BASE_DIR / "token_db.sqlite"
TOKEN_DB_INIT_SQL = BASE_DIR / "token_db_init.sql"
SHOP_INFO_PATH = BASE_DIR / "shop_info.json"
LICENSE_PATH = BASE_DIR / "license.json"

# Normalize LICENSE_PATH in case a directory named "license.json" exists.
# This can happen due to previous packaging or deployment mistakes on some systems.
try:
    if LICENSE_PATH.exists() and LICENSE_PATH.is_dir():
        print("[License] WARNING: 'license.json' is a directory; using file inside that directory.")
        LICENSE_PATH = LICENSE_PATH / "license.json"
except Exception:
    # If any error occurs while checking, keep original path and let downstream handle gracefully.
    pass

DATE_FMT = "%Y-%m-%d"

@dataclass
class LicenseInfo:
    expiry: date

    @property
    def expiry_str(self) -> str:
        return self.expiry.strftime(DATE_FMT)


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


# ---------------- License file helpers (base64 on-disk, JSON in-memory) ----------------
def _load_license_json(path: Path) -> Optional[dict]:
    """Load license JSON from `path`.

    On-disk format is expected to be base64-encoded JSON. For backward compatibility,
    if the file contains plain JSON we will migrate it to base64 automatically.
    Returns parsed dict or None on failure.
    """
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Try base64 decode first
    try:
        decoded = base64.b64decode(text.encode("utf-8")).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        # Not valid base64+json; try plain JSON and migrate
        try:
            data = json.loads(text)
        except Exception:
            return None
        # Migrate to base64 format
        try:
            _write_license_base64(path, data)
        except Exception:
            # ignore migration failure but return parsed data
            pass
        return data


def _write_license_base64(path: Path, data: dict) -> None:
    """Write license JSON as base64-encoded content to disk atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    json_text = json.dumps(data, indent=2, ensure_ascii=False)
    b64 = base64.b64encode(json_text.encode("utf-8")).decode("utf-8")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(b64)
    tmp.replace(path)


# ---------------- Shop info ----------------

def ensure_shop_info(default_shop_id: str = "SHOP01") -> str:
    """Ensure shop_info.json exists; return shop_id.
    If file is missing, create with default_shop_id.
    """
    data = _load_json(SHOP_INFO_PATH)
    if not data or not isinstance(data, dict) or not data.get("shop_id"):
        data = {"shop_id": default_shop_id}
        _write_json(SHOP_INFO_PATH, data)
    return str(data["shop_id"]).strip()


def get_shop_id() -> str:
    return ensure_shop_info()


# ---------------- License management ----------------

def ensure_default_license(days: int = 30) -> LicenseInfo:
    """Ensure license.json exists with at least a default expiry of today + days."""
    today = date.today()
    data = _load_license_json(LICENSE_PATH) or {}
    existing = data.get("expiry")
    if existing:
        try:
            expiry = datetime.strptime(existing, DATE_FMT).date()
        except ValueError:
            expiry = today
    else:
        expiry = today

    # Ensure at least today + days
    min_expiry = today + timedelta(days=days)
    if expiry < min_expiry:
        expiry = min_expiry
        _write_license_base64(LICENSE_PATH, {"expiry": expiry.strftime(DATE_FMT)})
    else:
        # normalize format
        _write_license_base64(LICENSE_PATH, {"expiry": expiry.strftime(DATE_FMT)})

    return LicenseInfo(expiry=expiry)


def read_license() -> LicenseInfo:
    data = _load_license_json(LICENSE_PATH) or {}
    exp_str = data.get("expiry")
    if not exp_str:
        return ensure_default_license()
    try:
        expiry = datetime.strptime(exp_str, DATE_FMT).date()
    except ValueError:
        return ensure_default_license()
    return LicenseInfo(expiry=expiry)


def write_license(info: LicenseInfo) -> None:
    _write_license_base64(LICENSE_PATH, {"expiry": info.expiry_str})


# ---------------- Token DB ----------------

def ensure_token_db() -> None:
    """Ensure token_db.sqlite exists with the used_tokens table."""
    TOKEN_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(TOKEN_DB_PATH))
    try:
        cur = conn.cursor()
        if TOKEN_DB_INIT_SQL.exists():
            with TOKEN_DB_INIT_SQL.open("r", encoding="utf-8") as f:
                sql = f.read()
            cur.executescript(sql)
        else:
            # Fallback schema
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS used_tokens (
                    token_id TEXT PRIMARY KEY,
                    shop_id TEXT NOT NULL,
                    issued_date DATE,
                    used BOOLEAN DEFAULT 0,
                    used_at DATETIME
                )
                """
            )
        conn.commit()
    finally:
        conn.close()
    print("[License] token_db.sqlite checked/created.")


def _open_token_db():
    conn = sqlite3.connect(str(TOKEN_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- Token parsing/validation ----------------

def _sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _hmac_sha256_hex(key: str, msg: str) -> str:
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def get_local_cpu_id() -> Optional[str]:
    """Detect CPU id from /proc/cpuinfo (Raspberry Pi).

    This function is intended to run on the Raspberry Pi. It reads the
    Serial field from /proc/cpuinfo and returns it. If not running on
    Linux or the serial cannot be read, return None.
    """
    try:
        import platform

        if platform.system() != "Linux":
            return None
        cpuinfo = Path("/proc/cpuinfo")
        if not cpuinfo.exists():
            return None
        text = cpuinfo.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if line.lower().startswith("serial"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    except Exception:
        pass
    return None


def parse_token(token: str, cpu_id: Optional[str] = None) -> Tuple[str, int, str, str]:
    """Return tuple (shop_id, months, rand4, mac6) or raise ValueError.
    Only supports the current short format: RAND4 (4 hex) and MAC6 (6 hex) using HMAC-SHA256.
    If cpu_id is not provided, the configured DEVICE_CPU_ID (or env) is used.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Token is required")
    token = token.strip().upper()
    parts = token.split("-")
    if len(parts) != 4:
        raise ValueError("Invalid token format")
    shop_id, months_part, rand, mac = parts

    if not months_part.endswith("M"):
        raise ValueError("Invalid months section")
    try:
        months = int(months_part[:-1])
        if months <= 0:
            raise ValueError
    except Exception:
        raise ValueError("Invalid months value")

    HEX_UPPER = "0123456789ABCDEF"
    if not rand or len(rand) != 4 or any(ch not in HEX_UPPER for ch in rand):
        raise ValueError("Invalid random section")
    if not mac or len(mac) != 6 or any(ch not in HEX_UPPER for ch in mac):
        raise ValueError("Invalid checksum section")

    # determine cpu_id to use for verification (prefer explicit, then configured/detected)
    cpu = cpu_id or get_local_cpu_id()
    if not cpu:
        raise ValueError("No device CPU id available for token verification; must run on Raspberry Pi (Serial in /proc/cpuinfo) or set PACKAGE_SHOP_CPU_ID")
    cpu = str(cpu).strip()
    msg = f"{shop_id}|{months}|{rand}|{cpu}"
    expected = _hmac_sha256_hex(SECRET_SALT, msg)[:6].upper()
    if not hmac.compare_digest(expected, mac.upper()):
        raise ValueError("Checksum mismatch or wrong shop/device")

    # Optional: sanity cap months to avoid accidents
    if months > 36:
        raise ValueError("Months too large")

    return shop_id, months, rand, mac.upper()


def token_used(token: str) -> bool:
    conn = _open_token_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT used FROM used_tokens WHERE token_id=?", (token.upper(),))
        row = cur.fetchone()
        return bool(row and row[0])
    finally:
        conn.close()


def mark_token_used(token: str, shop_id: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = _open_token_db()
    try:
        cur = conn.cursor()
        # Ensure row exists
        cur.execute(
            """
            INSERT INTO used_tokens (token_id, shop_id, issued_date, used, used_at)
            VALUES (?, ?, DATE('now'), 1, ?)
            ON CONFLICT(token_id) DO UPDATE SET used=1, used_at=excluded.used_at
            """,
            (token.upper(), shop_id, now),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------- High-level operations ----------------

def get_current_expiry() -> LicenseInfo:
    return read_license()


def extend_license_by_months(months: int) -> LicenseInfo:
    """Extend license by N months (30 days per month) from the later of today or current expiry."""
    if months <= 0:
        raise ValueError("Months must be positive")
    info = read_license()
    start = max(date.today(), info.expiry)
    new_expiry = start + timedelta(days=30 * months)
    new_info = LicenseInfo(expiry=new_expiry)
    write_license(new_info)
    return new_info


def apply_token(token: str) -> Tuple[bool, str, Optional[LicenseInfo]]:
    """Validate and apply token. Returns (success, message, license_info)."""
    try:
        shop_id_expected = get_shop_id().upper()
        shop_id, months, rand4, check4 = parse_token(token)
        if shop_id.upper() != shop_id_expected:
            return False, "Token is for a different shop", None
        if token_used(token):
            return False, "Token already used", None
        info = extend_license_by_months(months)
        mark_token_used(token, shop_id)
        return True, f"License extended by {months} month(s).", info
    except ValueError as e:
        return False, str(e), None
    except Exception:
        return False, "Unexpected error applying token", None


# ---------------- Token generation (utility) ----------------

def generate_token(shop_id: str, months: int, cpu_id: Optional[str] = None) -> str:
    """Generate a token for shop_id and months bound to a device cpu_id.

    Token format: <SHOP>-<months>M-<RAND4>-<MAC6>
    """
    shop_id = shop_id.strip().upper()
    if months <= 0:
        raise ValueError("months must be positive")
    # 4 hex chars of crypto random (shorter for UI entry)
    rand4 = secrets.token_hex(2).upper()
    cpu = cpu_id or get_local_cpu_id()
    if not cpu:
        raise ValueError("cpu_id is required to generate a token; must run on Raspberry Pi or set PACKAGE_SHOP_CPU_ID")
    cpu = str(cpu).strip()
    msg = f"{shop_id}|{months}|{rand4}|{cpu}"
    mac6 = _hmac_sha256_hex(SECRET_SALT, msg)[:6].upper()
    return f"{shop_id}-{months}M-{rand4}-{mac6}"
