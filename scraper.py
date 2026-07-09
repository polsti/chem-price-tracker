import asyncio
import json
from playwright.async_api import async_playwright

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
            await page.goto(url, timeout=PAGE_TIMEOUT)
        except Exception as e:
            print(f"  [{chem_name}] page load failed: {e}")
            await page.close()
            if attempt < MAX_RETRIES:
                await asyncio.sleep(WAIT_AFTER_FAIL)
            continue

        # wait up to 20 seconds for the price response
        for _ in range(40):
            if result is not None:
                break
            await asyncio.sleep(0.5)

        await page.close()

        if result is None:
            print(f"  [{chem_name}] price response never arrived")
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
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for chemical in CHEMICALS:
            data = await scrape_one(browser, chemical)
            if data:
                all_results.append(data)
            # pause between chemicals — avoid triggering rate limiting
            await asyncio.sleep(4)

        await browser.close()

    # print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for result in all_results:
        print(f"\n{result['chemical_name']} (id={result['chemical_id']})")
        print(f"{'Date':<14} {'Price':>10} {'Change':>10} {'Change%':>10} {'7d Avg':>10}")
        print("-" * 58)
        for row in result["rows"]:
            print(
                f"{row['dateRange']:<14}"
                f"{row['mdataValue']:>10}"
                f"{row['change']:>10}"
                f"{row['changeRate']:>10}"
                f"{row['ndaysAvgPrice']:>10}"
            )

    print(f"\nDone. Scraped {len(all_results)}/{len(CHEMICALS)} chemicals successfully.")
    return all_results


asyncio.run(scrape_all())
