import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()  # reads SUPABASE_URL / SUPABASE_KEY from .env into the environment

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    # The table already exists on Supabase (created once, by hand, via the
    # SQL editor). Real databases are changed deliberately, not recreated
    # automatically on every run, so there's nothing to do here — this
    # function is kept only so scraper.py's existing init_db() call still works.
    print("Using Supabase — table already exists, nothing to initialize.")


def get_latest_all():
    # returns the most recent price row for each chemical
    client = get_client()
    rows = client.table("chemical_prices") \
        .select("chemical_id, chemical_name, date, price, change_abs, change_pct, avg_price_7d") \
        .order("date", desc=True) \
        .execute().data

    # Supabase gives back every row, not "the latest per chemical" —
    # since we sorted newest-first, the first time we see a given
    # chemical_id is its most recent row.
    latest = {}
    for row in rows:
        if row["chemical_id"] not in latest:
            latest[row["chemical_id"]] = row

    result = list(latest.values())
    result.sort(key=lambda r: r["chemical_name"])
    return result


def get_history(chemical_id, limit=30):
    # returns last N days of prices for one chemical, oldest first
    client = get_client()
    rows = client.table("chemical_prices") \
        .select("chemical_id, chemical_name, date, price, change_abs, change_pct, avg_price_7d") \
        .eq("chemical_id", chemical_id) \
        .order("date", desc=True) \
        .limit(limit) \
        .execute().data

    return list(reversed(rows))  # oldest first, better for charts


def get_monthly_summary(year, month):
    # returns one summary row per chemical for the given month
    client = get_client()
    start = f"{year}-{month:02d}-01"
    # first day of the *next* month — used as an exclusive upper bound
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    rows = client.table("chemical_prices") \
        .select("chemical_id, chemical_name, date, price") \
        .gte("date", start) \
        .lt("date", end) \
        .order("date") \
        .execute().data

    # Group by chemical in plain Python — at this data size it's simpler
    # and clearer than reaching for Postgres-specific aggregate syntax.
    by_chemical = {}
    for row in rows:
        by_chemical.setdefault(row["chemical_id"], []).append(row)

    result = []
    for chem_id, chem_rows in by_chemical.items():
        prices = [r["price"] for r in chem_rows if r["price"] is not None]
        first, last = chem_rows[0], chem_rows[-1]

        change_pct = None
        if first["price"]:
            change_pct = round((last["price"] - first["price"]) / first["price"] * 100, 2)

        result.append({
            "chemical_id": chem_id,
            "chemical_name": chem_rows[0]["chemical_name"],
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "avg_price": round(sum(prices) / len(prices), 2) if prices else None,
            "first_date": first["date"],
            "last_date": last["date"],
            "trading_days": len(chem_rows),
            "first_price": first["price"],
            "last_price": last["price"],
            "change_pct": change_pct,
        })

    result.sort(key=lambda r: r["chemical_name"])
    return result


def insert_rows(chemical_id, chemical_name, rows, source_url):
    client = get_client()
    scraped_at = datetime.now().isoformat()

    payload = []
    for row in rows:
        # parse "0.95%" → 0.95
        change_pct_raw = row.get("changeRate", "0")
        change_pct = float(change_pct_raw.replace("%", "")) if change_pct_raw else None

        payload.append({
            "chemical_id": chemical_id,
            "chemical_name": chemical_name,
            "date": row["dateRange"],
            "price": float(row["mdataValue"]) if row["mdataValue"] else None,
            "change_abs": float(row["change"]) if row["change"] else None,
            "change_pct": change_pct,
            "avg_price_7d": float(row["ndaysAvgPrice"]) if row["ndaysAvgPrice"] else None,
            "scraped_at": scraped_at,
            "source_url": source_url,
        })

    # upsert = insert, but overwrite instead of erroring if a row for this
    # (chemical_id, date) already exists — safe to run more than once per day.
    result = client.table("chemical_prices").upsert(
        payload, on_conflict="chemical_id,date"
    ).execute()

    print(f"  [{chemical_name}] upserted {len(result.data)} row(s)")
