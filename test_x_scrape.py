import asyncio
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Going to X profile...")
        await page.goto("https://nitter.net/FIFAWorldCup", timeout=15000)
        # Testing if we can use Nitter because x.com is hard to scrape headless
        content = await page.content()
        if "FIFA" in content:
            print("Nitter works!")
        else:
            print("Nitter failed, trying x.com directly...")
            await page.goto("https://x.com/FIFAWorldCup", timeout=15000)
            await page.wait_for_selector("article", timeout=5000)
            print("Found articles on x.com!")
        await browser.close()

asyncio.run(scrape())
