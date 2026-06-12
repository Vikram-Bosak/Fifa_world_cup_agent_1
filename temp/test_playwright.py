import asyncio
from playwright.async_api import async_playwright

async def get_latest_video_tweet():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to Twitter profile...")
        await page.goto("https://x.com/FIFAWorldCup", wait_until="networkidle", timeout=60000)
        
        print("Waiting for tweets to load...")
        # Wait for article elements
        try:
            await page.wait_for_selector("article", timeout=15000)
        except Exception as e:
            print("Failed to load articles. They might be blocking headless browsers or requires login.")
            print(e)
            await browser.close()
            return None

        # Find articles
        articles = await page.query_selector_all("article")
        print(f"Found {len(articles)} articles.")
        
        tweet_url = None
        for article in articles:
            # Check if article has a video or media
            # Looking for video tag or media block
            html = await article.inner_html()
            if "<video" in html or "data-testid=\"videoComponent\"" in html or "data-testid=\"tweetPhoto\"" in html:
                # Get the link to the tweet
                links = await article.query_selector_all("a[href*='/status/']")
                for link in links:
                    href = await link.get_attribute("href")
                    if "status" in href and "photo" not in href and "video" not in href:
                        tweet_url = f"https://x.com{href}"
                        print(f"Found media tweet: {tweet_url}")
                        break
            if tweet_url:
                break
                
        await browser.close()
        return tweet_url

if __name__ == "__main__":
    url = asyncio.run(get_latest_video_tweet())
    print(f"Final URL: {url}")
