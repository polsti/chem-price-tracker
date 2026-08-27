"""
Run right after scraper.py in the daily workflow. Checks that no chemical
has gone silent for too long. If so, prints what and exits with an error —
that failure is what triggers the Telegram alert step in daily-scrape.yml
(via its `if: failure()` condition).

Deliberately NOT checking "does every chemical have *today's* price" —
the site publishes each chemical's daily price at its own time, not all
at once, and the scraper only runs once a day, so a chemical that hasn't
published yet when we check is normal, not a failure. Thanks to the site's
rolling 7-day window and upsert-based saving, a late chemical's price gets
backfilled automatically on the next run. What actually matters is whether
a chemical has gone quiet for multiple real days in a row — that's what
indicates the automation itself is broken, not just a normal delay.
"""

import sys
from datetime import date
from db import get_latest_all

EXPECTED_CHEMICALS = 8  # number of chemicals we scrape
MAX_DAYS_STALE = 2      # allow up to this many days of silence before alerting


def main():
    today = date.today()
    rows = get_latest_all()

    if len(rows) < EXPECTED_CHEMICALS:
        print(f"Only {len(rows)}/{EXPECTED_CHEMICALS} chemicals have any data at all.")
        sys.exit(1)

    stale = []
    for row in rows:
        last_updated = date.fromisoformat(row["date"])
        days_since = (today - last_updated).days
        if days_since > MAX_DAYS_STALE:
            stale.append(f"{row['chemical_name']} (last seen {row['date']}, {days_since} days ago)")

    if stale:
        print(f"These chemicals haven't updated in over {MAX_DAYS_STALE} days:")
        for s in stale:
            print(f"  - {s}")
        sys.exit(1)

    print(f"OK — no chemical has gone more than {MAX_DAYS_STALE} days without an update.")


if __name__ == "__main__":
    main()
