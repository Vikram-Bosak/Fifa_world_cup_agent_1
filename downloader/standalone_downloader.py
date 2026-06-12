import os
import sys
import glob
import time
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import feedparser

# Ensure we can import from the common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_video
from common.limits import can_download, increment_download

load_dotenv()

# We expect RSS_FEED_URLS in .env separated by comma
RSS_FEED_URLS_ENV = os.getenv("RSS_FEED_URLS", "")
RSS_FEED_URLS = [url.strip() for url in RSS_FEED_URLS_ENV.split(",") if url.strip()]

# Fallback for testing if no URL is provided
if not RSS_FEED_URLS:
    print("Warning: No RSS_FEED_URLS found in .env. Downloader will not find any videos.")

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "download_archive.txt")
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

def load_archive():
    if not os.path.exists(ARCHIVE_FILE):
        return set()
    with open(ARCHIVE_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def append_to_archive(video_id):
    with open(ARCHIVE_FILE, "a") as f:
        f.write(f"{video_id}\n")

def run_downloader():
    print("Starting standalone downloader with RSS Feed Scanning...")
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return
        
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    archive = load_archive()
    
    archive = load_archive()

    for feed_url in RSS_FEED_URLS:
        print(f"\n--- Scanning RSS Feed: {feed_url} ---")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"Failed to fetch RSS feed {feed_url}: {e}")
            continue

        video_downloaded = False

        for entry in feed.entries:
            tweet_id = entry.get('id', entry.get('link', ''))
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', tweet_id)[-20:]
            
            if safe_id in archive:
                continue

            video_url = None
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if media.get('type', '').startswith('video/'):
                        video_url = media.get('url')
                        break
            if not video_url and hasattr(entry, 'enclosures'):
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('video/'):
                        video_url = enc.get('href')
                        break
            
            if not video_url:
                link = entry.get('link')
                if link and ('x.com' in link or 'twitter.com' in link):
                    import yt_dlp
                    ydl_opts = {'format': 'best', 'quiet': True, 'get_url': True}
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(link, download=False)
                            video_url = info.get('url')
                    except Exception:
                        pass
                        
            if not video_url:
                continue
                
            print(f"Found new video! ID: {safe_id}")
            
            output_path = os.path.join(TEMP_DIR, f"{safe_id}.mp4")
            try:
                print(f"Downloading {video_url}...")
                video_req = requests.get(video_url, stream=True, timeout=30)
                video_req.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in video_req.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception as e:
                print(f"Failed to download video {safe_id}: {e}")
                continue

            title_match = entry.get('title', 'FIFA World Cup Highlight')
            if len(title_match) > 60:
                title_match = title_match[:57] + "..."
                
            download_dt = datetime.utcnow()
            
            post_time = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            post_id = f"{post_time}_{safe_id}"
            
            source_url = entry.get('link', feed_url)
            
            file_name = os.path.basename(output_path)
            message_text = (
                f"POST_ID: {post_id}\n\n"
                f"STATUS: DOWNLOADED\n\n"
                f"TITLE: {title_match}\n\n"
                f"SOURCE: RSS_FEED\n\n"
                f"SOURCE_URL: {source_url}\n\n"
                f"DOWNLOAD_TIME: {download_dt.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"FILE_NAME: {file_name}"
            )
            
            print(f"Sending RAW video to Download Channel (Queue)...")
            message_id, file_id = send_video(output_path, caption=message_text)
            
            if message_id and file_id:
                print("Video successfully stored in Telegram cloud. Kept local file for sequential processing.")
                video_data = {
                    "id": post_id,
                    "tweet_id": safe_id,
                    "raw_file_id": file_id,
                    "message_id": message_id,
                    "status": "DOWNLOADED",
                    "title": title_match,
                    "source": "RSS_FEED",
                    "source_url": source_url,
                    "download_time": download_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "timestamp": datetime.utcnow().isoformat(),
                    "local_path": output_path
                }
            
            append_to_archive(safe_id)
            increment_download()
            print("Successfully downloaded a video.")
            return video_data

    print("No new videos found in RSS feeds.")
    return None

if __name__ == "__main__":
    run_downloader()
