import os
import json
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
HISTORY_FILE = os.path.join(TEMP_DIR, "downloaded_history.txt")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_to_history(video_id):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{video_id}\n")

async def search_and_download_latest_video():
    print("Searching Twitter (X) for new videos posted in the last 24 hours...")
    
    profiles_str = os.environ.get('X_PROFILES', 'https://x.com/FIFAWorldCup')
    profiles = [p.strip() for p in profiles_str.split(',') if p.strip()]
    if not profiles:
        profiles = ["https://x.com/FIFAWorldCup"]
        
    history = load_history()
    
    ydl_opts_download = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(TEMP_DIR, 'raw_video.mp4'),
        'quiet': False
    }
    
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)
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
                
                articles = await page.query_selector_all("article")
                for article in articles:
                    html = await article.inner_html()
                    
                    if "<video" in html or "playback" in html:
                        time_element = await article.query_selector("time")
                        is_within_limit = False
                        
                        if time_element:
                            datetime_str = await time_element.get_attribute("datetime")
                            if datetime_str:
                                try:
                                    post_time = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                                    if post_time >= time_limit:
                                        is_within_limit = True
                                        print(f"Found video post at {post_time.isoformat()}")
                                except ValueError:
                                    pass
                        
                        if not is_within_limit:
                            status_links = await article.query_selector_all("a[href*='/status/']")
                            for sl in status_links:
                                txt = await sl.inner_text()
                                txt = txt.strip()
                                if txt.endswith('m') and txt[:-1].isdigit():
                                    is_within_limit = True
                                    break
                                elif txt.endswith('h') and txt[:-1].isdigit():
                                    if int(txt[:-1]) <= 24:
                                        is_within_limit = True
                                        break
                                elif txt.endswith('s') and txt[:-1].isdigit():
                                    is_within_limit = True
                                    break
                                    
                        if not is_within_limit:
                            print("Post is too old or timestamp unknown. Skipping.")
                            continue
                            
                        links = await article.query_selector_all("a[href*='/status/']")
                        for link in links:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href and "photo" not in href:
                                tweet_url = f"https://x.com{href}" if href.startswith("/") else href
                                tweet_id = tweet_url.split("/status/")[1].split("/")[0].split("?")[0]
                                
                                if tweet_id in history:
                                    print(f"Video {tweet_id} already in history, skipping...")
                                    break
                                    
                                print(f"Selected valid video: {tweet_url}")
                                
                                try:
                                    os.makedirs(TEMP_DIR, exist_ok=True)
                                    filename = os.path.join(TEMP_DIR, "raw_video.mp4")
                                    if os.path.exists(filename):
                                        os.remove(filename)
                                        
                                    print(f"Downloading with yt-dlp...")
                                    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                                        info = ydl.extract_info(tweet_url, download=True)
                                        title = info.get('title', f"Twitter Video {tweet_id}")
                                        
                                    await browser.close()
                                    return filename, title, tweet_id, tweet_url
                                    
                                except Exception as e:
                                    print(f"Error downloading {tweet_url}: {e}")
                                    pass
            except Exception as e:
                print(f"Error checking profile {profile}: {e}")
                
        await browser.close()
        
    print("--------------------------------------------------")
    print("No new valid videos found.")
    return None, None, None, None

def run_downloader():
    print("Starting Agent 1: X (Twitter) Downloader (Hollywood Style)")
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Check if download limit is reached
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.limits import can_download, increment_download
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return None
    
    result = asyncio.run(search_and_download_latest_video())
    if result and len(result) == 4:
        video_path, title, tweet_id, source_url = result
    else:
        video_path, title, tweet_id, source_url = None, None, None, None
        
    if video_path and os.path.exists(video_path):
        save_to_history(tweet_id)
        video_data = {
            "id": tweet_id,
            "tweet_id": tweet_id,
            "title": title,
            "source_url": source_url,
            "local_path": video_path,
            "status": "DOWNLOADED",
            "download_time": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        increment_download()
        print("Agent 1 completed successfully.")
        return video_data
    
    print("No video downloaded.")
    return None

if __name__ == "__main__":
    run_downloader()
