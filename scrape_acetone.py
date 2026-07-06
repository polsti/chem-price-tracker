import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.sci99.com/monitor-449-0.html"
TARGET = "listProductPagePrice"


async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # this will hold the response once we catch it
        result = None

        async def handle_response(response):
            nonlocal result
            if TARGET in response.url and "oldId=449" in response.url:
                try:
                    data = await response.json()
                    result = data
                except Exception as e:
                    print(f"Failed to parse response: {e}")

        page.on("response", handle_response)

        print("Opening page...")
        await page.goto(URL, timeout=30000)

        # wait for the response to be captured (up to 15 seconds)
        for _ in range(30):
            if result is not None:
                break
            await asyncio.sleep(0.5)

        await browser.close()

        if result is None:
            print("ERROR: price response never arrived")
            return

        if result.get("code") != 200:
            print(f"ERROR: unexpected response code: {result.get('code')}")
            return

        rows = result["data"]
        print(f"\nGot {len(rows)} rows\n")
        print(f"{'Date':<14} {'Price':>10} {'Change':>10} {'Change%':>10} {'7d Avg':>10}")
        print("-" * 58)
        for row in rows:
            print(
                f"{row['dateRange']:<14}"
                f"{row['mdataValue']:>10}"
                f"{row['change']:>10}"
                f"{row['changeRate']:>10}"
                f"{row['ndaysAvgPrice']:>10}"
            )


asyncio.run(scrape())
