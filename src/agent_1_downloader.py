import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
import yt_dlp
from dotenv import load_dotenv

load_dotenv()
HISTORY_FILE = 'downloaded_history.txt'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_to_history(video_id):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{video_id}\n")

async def search_and_download_latest_video():
    print("Searching Twitter (X) for new videos posted in the last 22 hours...")
    
    profiles_str = os.getenv("X_PROFILES", "")
    if profiles_str:
        profiles = [p.strip() for p in profiles_str.split(',') if p.strip()]
    else:
        profiles = [
            "https://x.com/WorldCupMedia",
            "https://x.com/Waleedahmdd",
            "https://x.com/FIFAWC26Updates",
            "https://x.com/FIFAcom",
            "https://x.com/SkyFootball",
            "https://x.com/TheSunFootball",
            "https://x.com/footballontnt",
            "https://x.com/TrollFootball",
            "https://x.com/Footballtweet",
            "https://x.com/FBAwayDays"
        ]
    
    history = load_history()
    
    ydl_opts_download = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'workspace/raw_video.mp4',
        'quiet': False
    }
    
    time_limit = datetime.now(timezone.utc) - timedelta(hours=2)
    print(f"Time limit is set to: {time_limit.isoformat()}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        for profile in profiles:
            print(f"--------------------------------------------------")
            print(f"Checking profile: {profile}")
            try:
                await page.goto(profile, timeout=30000)
                await page.wait_for_selector("article", timeout=15000)
                await page.wait_for_timeout(3000) # Wait for videos to load
                
                # Fetch articles
                articles = await page.query_selector_all("article")
                for article in articles:
                    html = await article.inner_html()
                    
                    # 1. Check if it's a video
                    if "<video" in html or "playback" in html:
                        # 2. Extract link and exact timestamp via Snowflake ID
                        links = await article.query_selector_all("a[href*='/status/']")
                        tweet_url = None
                        tweet_id = None
                        
                        for link in links:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href and "photo" not in href:
                                tweet_url = f"https://x.com{href}" if href.startswith("/") else href
                                tweet_id = tweet_url.split("/status/")[1].split("/")[0].split("?")[0]
                                break
                                
                        if not tweet_id or not tweet_url:
                            continue
                            
                        if tweet_id in history:
                            print(f"Video {tweet_id} already in history, skipping...")
                            continue
                            
                        # Calculate exact post time using Twitter Snowflake ID formula
                        try:
                            # Formula: (tweet_id >> 22) + 1288834974657 = timestamp in ms
                            timestamp_ms = (int(tweet_id) >> 22) + 1288834974657
                            post_time = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
                            print(f"Tweet {tweet_id} posted at: {post_time.isoformat()}")
                            
                            if post_time < time_limit:
                                print(f"Post is older than 2 hours. Skipping.")
                                continue
                                
                            print(f"Selected valid NEW video within 2 hours: {tweet_url}")
                        except ValueError:
                            print("Invalid tweet ID format. Skipping.")
                            continue
                                
                                # Use yt-dlp to download it
                                try:
                                    os.makedirs('workspace', exist_ok=True)
                                    filename = "workspace/raw_video.mp4"
                                    if os.path.exists(filename):
                                        os.remove(filename)
                                        
                                    print(f"Downloading with yt-dlp...")
                                    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                                        info = ydl.extract_info(tweet_url, download=True)
                                        title = info.get('title', f"Twitter Video {tweet_id}")
                                        
                                    meta = {
                                        "title": title,
                                        "source_url": tweet_url,
                                        "video_id": tweet_id
                                    }
                                    with open("workspace/meta.json", "w") as f:
                                        json.dump(meta, f)
                                        
                                    await browser.close()
                                    return filename, title, tweet_id, tweet_url, tweet_url
                                    
                                except Exception as e:
                                    print(f"Error downloading {tweet_url}: {e}")
                                    # Try next article
                                    pass
            except Exception as e:
                print(f"Error checking profile {profile}: {e}")
                
        await browser.close()
        
    print("--------------------------------------------------")
    print("No new valid videos found across all profiles within the last 22 hours.")
    return None, None, None, None, None

def run_downloader():
    print("Starting Agent 1: X (Twitter) Downloader")
    os.makedirs('workspace', exist_ok=True)
    
    result = asyncio.run(search_and_download_latest_video())
    if result and len(result) == 5:
        video_path, title, tweet_id, source_url, video_url = result
    else:
        video_path, title, tweet_id, source_url, video_url = None, None, None, None, None
        
    if video_path and os.path.exists(video_path):
        save_to_history(tweet_id)
        video_data = {
            "id": tweet_id,
            "tweet_id": tweet_id,
            "title": title,
            "source_url": source_url,
            "local_path": video_path,
            "status": "DOWNLOADED"
        }
        print("Agent 1 completed successfully.")
        return video_data
    
    print("No video downloaded.")
    return None

if __name__ == "__main__":
    run_downloader()
