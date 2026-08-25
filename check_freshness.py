"""
Run right after scraper.py in the daily workflow. Checks that today's price
actually landed for all 8 chemicals. If anything is missing, it prints what
and exits with an error — that failure is what triggers the Telegram alert
step in daily-scrape.yml (via its `if: failure()` condition).
"""

import sys
from datetime import date
from db import get_latest_all

EXPECTED_CHEMICALS = 8  # number of chemicals we scrape


def main():
    # "today" here means the GitHub Actions runner's UTC date. This lines up
    # with the site's own reported date because the workflow runs at 05:00 UTC —
    # by then both UTC and China (the site's market) have already rolled over
    # to the same calendar day. If the schedule time in daily-scrape.yml ever
    # changes significantly, this assumption is worth rechecking.
    today = date.today().isoformat()
    rows = get_latest_all()

    if len(rows) < EXPECTED_CHEMICALS:
        print(f"Only {len(rows)}/{EXPECTED_CHEMICALS} chemicals have any data at all.")
        sys.exit(1)

    missing = [r["chemical_name"] for r in rows if r["date"] != today]
    if missing:
        print(f"Missing today's ({today}) price for: {', '.join(missing)}")
        sys.exit(1)

    print(f"OK — all {EXPECTED_CHEMICALS} chemicals have today's ({today}) price.")


if __name__ == "__main__":
    main()
