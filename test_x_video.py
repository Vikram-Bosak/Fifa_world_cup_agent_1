import asyncio
from playwright.async_api import async_playwright
import re

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Going to X profile...")
        await page.goto("https://x.com/FIFAWorldCup", timeout=15000)
        await page.wait_for_selector("article", timeout=10000)
        
        # Get all articles
        articles = await page.query_selector_all("article")
        for article in articles:
            # Check if it has a video player
            html = await article.inner_html()
            links = await article.query_selector_all("a[href*='/status/']")
            urls = set()
            for l in links:
                href = await l.get_attribute("href")
                if "/status/" in href and not "photo" in href and not "video" in href:
                    urls.add(href)
            
            # Twitter video elements usually have a specific structure, let's just check text for now or 'video' tag
            has_video = "<video" in html or "playback" in html
            print(f"URLs: {urls}, Has Video: {has_video}")

        await browser.close()

asyncio.run(scrape())
