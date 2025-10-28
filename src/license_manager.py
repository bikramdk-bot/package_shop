"""License management for simplified offline token system.

Responsibilities:
- Manage shop_id (shop_info.json)
- Manage license.json with expiry
- Ensure token DB exists (token_db.sqlite)
- Validate and apply tokens (non-reusable, shop-locked)

Token format: <shop_id>-<months>M-<rand4>-<check4>
- check4 = first 4 hex of SHA1(shop_id + rand4 + SECRET_SALT)

All paths are resolved relative to this file's directory.
"""
from __future__ import annotations

import os
import json
import sqlite3
import hashlib
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Tuple

# Shared secret salt
SECRET_SALT = "SALT1234"

# Base directory (src/)
BASE_DIR = Path(__file__).resolve().parent
TOKEN_DB_PATH = BASE_DIR / "token_db.sqlite"
TOKEN_DB_INIT_SQL = BASE_DIR / "token_db_init.sql"
SHOP_INFO_PATH = BASE_DIR / "shop_info.json"
LICENSE_PATH = BASE_DIR / "license.json"

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
    data = _load_json(LICENSE_PATH) or {}
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
        _write_json(LICENSE_PATH, {"expiry": expiry.strftime(DATE_FMT)})
    else:
        # normalize format
        _write_json(LICENSE_PATH, {"expiry": expiry.strftime(DATE_FMT)})

    return LicenseInfo(expiry=expiry)


def read_license() -> LicenseInfo:
    data = _load_json(LICENSE_PATH) or {}
    exp_str = data.get("expiry")
    if not exp_str:
        return ensure_default_license()
    try:
        expiry = datetime.strptime(exp_str, DATE_FMT).date()
    except ValueError:
        return ensure_default_license()
    return LicenseInfo(expiry=expiry)


def write_license(info: LicenseInfo) -> None:
    _write_json(LICENSE_PATH, {"expiry": info.expiry_str})


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


def parse_token(token: str) -> Tuple[str, int, str, str]:
    """Return tuple (shop_id, months, rand4, check4) or raise ValueError."""
    if not token or not isinstance(token, str):
        raise ValueError("Token is required")
    token = token.strip().upper()
    parts = token.split("-")
    if len(parts) != 4:
        raise ValueError("Invalid token format")
    shop_id, months_part, rand4, check4 = parts
    if not rand4 or len(rand4) != 4 or any(ch not in string.ascii_uppercase + string.digits for ch in rand4):
        raise ValueError("Invalid random section")
    if not check4 or len(check4) != 4 or any(ch not in string.hexdigits.upper() for ch in check4):
        raise ValueError("Invalid checksum section")
    if not months_part.endswith("M"):
        raise ValueError("Invalid months section")
    try:
        months = int(months_part[:-1])
        if months <= 0:
            raise ValueError
    except Exception:
        raise ValueError("Invalid months value")

    expected = _sha1_hex(shop_id + rand4 + SECRET_SALT)[:4].upper()
    if expected != check4.upper():
        raise ValueError("Checksum mismatch or wrong shop")

    # Optional: sanity cap months to avoid accidents
    if months > 36:
        raise ValueError("Months too large")

    return shop_id, months, rand4, check4.upper()


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

def generate_token(shop_id: str, months: int) -> str:
    """Generate a token for shop_id and months. Random section is 4 chars [A-Z0-9]."""
    shop_id = shop_id.strip().upper()
    if months <= 0:
        raise ValueError("months must be positive")
    rand4 = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    check4 = _sha1_hex(shop_id + rand4 + SECRET_SALT)[:4].upper()
    return f"{shop_id}-{months}M-{rand4}-{check4}"
