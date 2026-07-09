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
