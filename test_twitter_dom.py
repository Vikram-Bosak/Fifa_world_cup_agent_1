import asyncio
from playwright.async_api import async_playwright

async def test_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        await page.goto("https://x.com/FIFAWorldCup", timeout=20000)
        await page.wait_for_selector("article", timeout=15000)
        await page.wait_for_timeout(5000)
        articles = await page.query_selector_all("article")
        for i, article in enumerate(articles[:3]):
            html = await article.inner_html()
            with open(f"article_{i}.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Article {i} saved.")
        await browser.close()

asyncio.run(test_scraper())
