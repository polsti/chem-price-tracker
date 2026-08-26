"""
Temporary investigation script — NOT part of the daily production scrape.

Checks each chemical's page and records the newest date the site is
currently showing, tagged with when we checked. Run repeatedly (see
.github/workflows/investigate-update-time.yml) over a day or two to see
what time each chemical's price actually updates on sci99.com.

Reuses scrape_one() from scraper.py instead of duplicating the
browser/interception logic — we just look at the dates we got back,
we don't need the full row list the real scraper cares about.
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from scraper import CHEMICALS, scrape_one
from db import get_client


async def main():
    client = get_client()
    checked_at = datetime.now().isoformat()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for chemical in CHEMICALS:
            data = await scrape_one(browser, chemical)

            if data is None:
                print(f"  [{chemical['name']}] check failed, skipping this round")
                await asyncio.sleep(4)
                continue

            latest_date = max(row["dateRange"] for row in data["rows"])
            client.table("price_check_log").insert({
                "chemical_id": data["chemical_id"],
                "chemical_name": data["chemical_name"],
                "checked_at": checked_at,
                "latest_date_seen": latest_date,
            }).execute()
            print(f"  [{data['chemical_name']}] latest date on site right now: {latest_date}")

            await asyncio.sleep(4)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
