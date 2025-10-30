"""CLI tool to generate and register a shop-bound license token.

Usage:
    python generate_token.py SHOP07 3

This prints a token like SHOP07-3M-AB12-9F0C and inserts an unused row into token_db.sqlite.
"""
from __future__ import annotations

import sys
from datetime import date
import sqlite3
from pathlib import Path

from license_manager import generate_token as gen_token, TOKEN_DB_PATH, ensure_token_db


def main(argv):
    if len(argv) != 3:
        print("Usage: python generate_token.py <SHOP_ID> <MONTHS>")
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

    ensure_token_db()
    token = gen_token(shop_id, months)

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
