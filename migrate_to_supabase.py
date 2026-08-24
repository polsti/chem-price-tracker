"""
One-time migration: copies every row from local prices.db (SQLite)
into the chemical_prices table on Supabase (Postgres).

Run once, by hand:  ./venv/bin/python3 migrate_to_supabase.py

Uses upsert (not insert) so it's safe to run more than once — if a
(chemical_id, date) row already exists on Supabase, it gets overwritten
with the local value instead of raising a duplicate-key error.
"""

import os
import sqlite3
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()  # reads SUPABASE_URL / SUPABASE_KEY from .env into the environment

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
DB_PATH = "prices.db"


def read_local_rows():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT chemical_id, chemical_name, date, price, change_abs,
               change_pct, avg_price_7d, scraped_at, source_url
        FROM chemical_prices
        ORDER BY chemical_id, date
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def main():
    rows = read_local_rows()
    print(f"Read {len(rows)} rows from local {DB_PATH}")

    if not rows:
        print("Nothing to migrate.")
        return

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Supabase's upsert needs to know which columns define "a duplicate" —
    # that's the same (chemical_id, date) UNIQUE constraint we set up in the table.
    result = client.table("chemical_prices").upsert(
        rows, on_conflict="chemical_id,date"
    ).execute()

    print(f"Upserted {len(result.data)} rows into Supabase.")


if __name__ == "__main__":
    main()
