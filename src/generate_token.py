"""CLI tool to generate and register a shop-bound license token.

Usage:
    python generate_token.py <SHOP_ID> <MONTHS> [CPU_ID]

If CPU_ID is omitted the script will try to auto-detect the local CPU serial
when running on a Raspberry Pi (Linux /proc/cpuinfo). When run on Windows or
non-Pi Linux hosts you must provide the Pi CPU serial as CPU_ID.

This prints a token like SHOP07-3M-AB12-9F0C and inserts an unused row into token_db.sqlite.
"""
from __future__ import annotations

import sys
from datetime import date
import sqlite3
from pathlib import Path

from license_manager import generate_token as gen_token, TOKEN_DB_PATH, ensure_token_db
import platform
from pathlib import Path


def main(argv):
    if len(argv) not in (3, 4):
        print("Usage: python generate_token.py <SHOP_ID> <MONTHS> [CPU_ID]")
        return 2
    shop_id = argv[1].strip().upper()
    try:
        months = int(argv[2])
    except ValueError:
        print("MONTHS must be an integer")
        return 2
    if months <= 0:
        print("MONTHS must be > 0")
        return 2

    cpu_id = argv[3].strip() if len(argv) == 4 else None

    # If CPU_ID not provided, try auto-detect on Pi (Linux)
    if not cpu_id:
        try:
            if platform.system() == "Linux":
                cpuinfo = Path("/proc/cpuinfo")
                if cpuinfo.exists():
                    txt = cpuinfo.read_text(encoding="utf-8", errors="ignore")
                    for line in txt.splitlines():
                        if line.lower().startswith("serial"):
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                cpu_id = parts[1].strip()
                                break
        except Exception:
            cpu_id = None

    if not cpu_id:
        print("ERROR: CPU_ID (Pi serial) is required when running off-device. Provide it as the third argument.")
        return 2

    ensure_token_db()
    token = gen_token(shop_id, months, cpu_id=cpu_id)

    conn = sqlite3.connect(str(TOKEN_DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO used_tokens (token_id, shop_id, issued_date, used)
            VALUES (?, ?, DATE('now'), 0)
            ON CONFLICT(token_id) DO NOTHING
            """,
            (token, shop_id),
        )
        conn.commit()
    finally:
        conn.close()

    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
