import asyncio
from playwright.async_api import async_playwright
import time
import os
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

async def extract_latest_video_tweets(profile_urls: List[str], max_per_profile: int = 3) -> List[Dict]:
    """
    Scrapes the given X profiles using Playwright to find the latest tweets containing a video.
    Returns a list of dictionaries with tweet_url, tweet_id, and profile_url.
    """
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Using a realistic user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for profile in profile_urls:
            print(f"--- Scanning Profile: {profile} ---")
            try:
                await page.goto(profile, timeout=20000)
                # Wait for the timeline articles to load
                await page.wait_for_selector("article", timeout=15000)
                
                # Small wait to let images/videos initialize
                await page.wait_for_timeout(2000)
                
                articles = await page.query_selector_all("article")
                found_count = 0
                
                for article in articles:
                    if found_count >= max_per_profile:
                        break
                        
                    html = await article.inner_html()
                    
                    # Look for status links to get the tweet ID
                    links = await article.query_selector_all("a[href*='/status/']")
                    tweet_url = None
                    for l in links:
                        href = await l.get_attribute("href")
                        if "/status/" in href and "photo" not in href and "video" not in href:
                            if href.startswith("http"):
                                tweet_url = href
                            else:
                                tweet_url = f"https://x.com{href}"
                            break
                            
                    if not tweet_url:
                        continue
                        
                    # Extract ID from URL (e.g. https://x.com/FIFAWorldCup/status/123456789)
                    tweet_id = tweet_url.split("/status/")[1].split("/")[0] if "/status/" in tweet_url else None
                    
                    time_elem = await article.query_selector("time")
                    parsed_datetime = None
                    if time_elem:
                        dt_str = await time_elem.get_attribute("datetime")
                        if dt_str:
                            try:
                                # Example: 2023-11-20T14:30:00.000Z
                                dt_str_clean = dt_str.replace('Z', '+00:00')
                                tweet_time = datetime.fromisoformat(dt_str_clean)
                                now_utc = datetime.now(timezone.utc)
                                
                                if now_utc - tweet_time > timedelta(hours=4):
                                    print(f"Tweet {tweet_id} is older than 4 hours ({tweet_time.strftime('%Y-%m-%d %H:%M')}). Skipping.")
                                    continue
                                parsed_datetime = tweet_time
                            except Exception as e:
                                print(f"Error parsing date {dt_str}: {e}")
                                
                    if not parsed_datetime:
                        print(f"Could not parse <time> for tweet {tweet_id}. Assuming it is NEW (current time) for prioritization.")
                        parsed_datetime = datetime.now(timezone.utc)
                    
                    # Check if it has a video
                    has_video = "<video" in html or "playback" in html
                    
                    if has_video and tweet_id:
                        print(f"Found video tweet: {tweet_url}")
                        results.append({
                            "tweet_url": tweet_url,
                            "tweet_id": tweet_id,
                            "profile_url": profile,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                            "parsed_datetime": parsed_datetime
                        })
                        found_count += 1
                        
            except Exception as e:
                print(f"Failed to scan profile {profile}: {e}")
                
        await browser.close()
        
    return results

def get_latest_video_tweets(profile_urls: List[str], max_per_profile: int = 1) -> List[Dict]:
    """Synchronous wrapper for the async playwright scraper"""
    return asyncio.run(extract_latest_video_tweets(profile_urls, max_per_profile))

if __name__ == "__main__":
    # Test script
    profiles = ["https://x.com/FIFAWorldCup"]
    videos = get_latest_video_tweets(profiles)
    for v in videos:
        print(v)
