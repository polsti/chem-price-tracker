import sqlite3
from datetime import datetime

DB_PATH = "prices.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    # makes rows behave like dictionaries: row["price"] instead of row[2]
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chemical_prices (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            chemical_id  TEXT NOT NULL,
            chemical_name TEXT NOT NULL,
            date         DATE NOT NULL,
            price        REAL,
            change_abs   REAL,
            change_pct   REAL,
            avg_price_7d REAL,
            scraped_at   DATETIME NOT NULL,
            source_url   TEXT,
            UNIQUE(chemical_id, date)
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready: {DB_PATH}")


def get_latest_all():
    # returns the most recent price row for each chemical
    conn = get_connection()
    rows = conn.execute("""
        SELECT chemical_id, chemical_name, date, price, change_abs, change_pct, avg_price_7d
        FROM chemical_prices
        WHERE (chemical_id, date) IN (
            SELECT chemical_id, MAX(date)
            FROM chemical_prices
            GROUP BY chemical_id
        )
        ORDER BY chemical_name
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_history(chemical_id, limit=30):
    # returns last N days of prices for one chemical, oldest first
    conn = get_connection()
    rows = conn.execute("""
        SELECT chemical_id, chemical_name, date, price, change_abs, change_pct, avg_price_7d
        FROM chemical_prices
        WHERE chemical_id = ?
        ORDER BY date DESC
        LIMIT ?
    """, (chemical_id, limit)).fetchall()
    conn.close()
    # reverse so oldest is first (better for charts)
    return [dict(row) for row in reversed(rows)]


def get_monthly_summary(year, month):
    # returns one summary row per chemical for the given month
    # e.g. year=2026, month=7 → all rows from 2026-07-01 to 2026-07-31
    period = f"{year}-{month:02d}"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            chemical_id,
            chemical_name,
            MIN(price)  AS min_price,
            MAX(price)  AS max_price,
            ROUND(AVG(price), 2) AS avg_price,
            MIN(date)   AS first_date,
            MAX(date)   AS last_date,
            COUNT(*)    AS trading_days
        FROM chemical_prices
        WHERE strftime('%Y-%m', date) = ?
        GROUP BY chemical_id, chemical_name
        ORDER BY chemical_name
    """, (period,)).fetchall()

    result = []
    for row in rows:
        row = dict(row)
        # also fetch the actual price on first and last date for % change
        first = conn.execute("""
            SELECT price FROM chemical_prices
            WHERE chemical_id = ? AND date = ?
        """, (row["chemical_id"], row["first_date"])).fetchone()

        last = conn.execute("""
            SELECT price FROM chemical_prices
            WHERE chemical_id = ? AND date = ?
        """, (row["chemical_id"], row["last_date"])).fetchone()

        row["first_price"] = first["price"] if first else None
        row["last_price"]  = last["price"]  if last  else None

        if row["first_price"] and row["first_price"] != 0:
            change = ((row["last_price"] - row["first_price"]) / row["first_price"]) * 100
            row["change_pct"] = round(change, 2)
        else:
            row["change_pct"] = None

        result.append(row)

    conn.close()
    return result


def insert_rows(chemical_id, chemical_name, rows, source_url):
    conn = get_connection()
    scraped_at = datetime.now().isoformat()
    inserted = 0
    skipped = 0

    for row in rows:
        # parse "0.95%" → 0.95
        change_pct_raw = row.get("changeRate", "0")
        change_pct = float(change_pct_raw.replace("%", "")) if change_pct_raw else None

        try:
            conn.execute("""
                INSERT INTO chemical_prices
                    (chemical_id, chemical_name, date, price, change_abs, change_pct,
                     avg_price_7d, scraped_at, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chemical_id,
                chemical_name,
                row["dateRange"],
                float(row["mdataValue"]) if row["mdataValue"] else None,
                float(row["change"]) if row["change"] else None,
                change_pct,
                float(row["ndaysAvgPrice"]) if row["ndaysAvgPrice"] else None,
                scraped_at,
                source_url,
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            # UNIQUE(chemical_id, date) violation — row already exists, skip it
            skipped += 1

    conn.commit()
    conn.close()
    print(f"  [{chemical_name}] inserted {inserted}, skipped {skipped} duplicate(s)")
