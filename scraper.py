import asyncio
import json
from playwright.async_api import async_playwright
from db import init_db, insert_rows

CHEMICALS = [
    {"id": "449",       "name": "acetone"},
    {"id": "678",       "name": "yellow phosphorus"},
    {"id": "1658",      "name": "fatty alcohols"},
    {"id": "114793214", "name": "monoethanolamine"}, # for some reason ignored 
    {"id": "499",       "name": "acetic acid"},
    {"id": "366",       "name": "methanol"},
    {"id": "377",       "name": "pure benzene"},
    {"id": "367",       "name": "ethylene glycol"},
]

BASE_URL = "https://www.sci99.com/monitor-{id}-0.html"
TARGET = "listProductPagePrice"


MAX_RETRIES = 3
PAGE_TIMEOUT = 60000   # 60 seconds — some pages are just slow
WAIT_AFTER_FAIL = 5    # seconds to wait before retrying


async def scrape_one(browser, chemical):
    chem_id = chemical["id"]
    chem_name = chemical["name"]
    url = BASE_URL.format(id=chem_id)

    for attempt in range(1, MAX_RETRIES + 1):
        page = await browser.new_page()
        result = None

        async def handle_response(response):
            nonlocal result
            if TARGET in response.url and f"oldId={chem_id}" in response.url:
                try:
                    result = await response.json()
                except Exception as e:
                    print(f"  [{chem_name}] failed to parse response: {e}")

        page.on("response", handle_response)

        if attempt == 1:
            print(f"Scraping {chem_name} (id={chem_id})...")
        else:
            print(f"  [{chem_name}] retrying (attempt {attempt}/{MAX_RETRIES})...")

        try:
            # domcontentloaded fires as soon as HTML is parsed —
            # we don't need images/fonts/ads to finish loading,
            # just early enough for JS to trigger the XHR price call
            await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        except Exception as e:
            # page timed out — but the XHR might have fired already
            # so don't close yet, fall through and check result first
            print(f"  [{chem_name}] page load timed out, checking if data was captured...")

        # wait up to 20 seconds for the price response
        # (runs whether goto succeeded or timed out)
        for _ in range(40):
            if result is not None:
                break
            await asyncio.sleep(0.5)

        await page.close()

        if result is None:
            print(f"  [{chem_name}] no data captured")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(WAIT_AFTER_FAIL)
            continue

        if result.get("code") != 200:
            print(f"  [{chem_name}] unexpected code {result.get('code')}")
            return None

        rows = result["data"]
        print(f"  [{chem_name}] got {len(rows)} rows")
        return {"chemical_id": chem_id, "chemical_name": chem_name, "rows": rows}

    print(f"  [{chem_name}] FAILED after {MAX_RETRIES} attempts")
    return None


async def scrape_all():
    init_db()
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for chemical in CHEMICALS:
            data = await scrape_one(browser, chemical)
            if data:
                all_results.append(data)
                source_url = BASE_URL.format(id=chemical["id"])
                insert_rows(
                    chemical_id=data["chemical_id"],
                    chemical_name=data["chemical_name"],
                    rows=data["rows"],
                    source_url=source_url,
                )
            await asyncio.sleep(4)

        await browser.close()

    print(f"\nDone. Scraped {len(all_results)}/{len(CHEMICALS)} chemicals successfully.")


asyncio.run(scrape_all())
