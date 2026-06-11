import os
import sys
import glob
import time
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from the common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_video

load_dotenv()

TARGET_PROFILES = [
    {"name": "FIFA World Cup", "username": "FIFAWorldCup"},
    {"name": "Cristiano Ronaldo", "username": "Cristiano"}
]

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
    print("Starting standalone downloader with Priority-Based Profile Scanning...")
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Clear temp dir before starting
    for f in glob.glob(os.path.join(TEMP_DIR, "*.mp4")):
        try:
            os.remove(f)
        except Exception as e:
            pass

    archive = load_archive()
    today_utc = datetime.utcnow().date()
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    for profile in TARGET_PROFILES:
        profile_name = profile["name"]
        username = profile["username"]
        
        print(f"\n--- Scanning Profile: {profile_name} (@{username}) ---")
        syndication_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
        
        try:
            response = requests.get(syndication_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch syndication timeline for {username}: {e}")
            continue

        # Extract JSON data from HTML
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', response.text)
        if not match:
            print(f"Could not find timeline data for {username}.")
            continue

        try:
            data = json.loads(match.group(1))
            tweets = data['props']['pageProps']['timeline']['entries']
        except Exception as e:
            print(f"Failed to parse timeline JSON for {username}: {e}")
            continue

        video_downloaded = False

        for t in tweets:
            tweet = t.get('content', {}).get('tweet')
            if not tweet:
                continue
                
            tweet_id = tweet.get('id_str')
            
            # Check if already processed
            if f"twitter {tweet_id}" in archive or tweet_id in archive:
                continue

            # Check date (e.g., "Wed Jun 10 17:28:00 +0000 2026")
            created_at_str = tweet.get('created_at')
            if not created_at_str:
                continue
                
            try:
                tweet_date = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S +0000 %Y").date()
            except ValueError:
                continue
                
            # Only process TODAY's posts
            if tweet_date != today_utc:
                continue

            # Check if it has a video
            ext_entities = tweet.get('extended_entities', {})
            media_list = ext_entities.get('media', [])
            if not media_list:
                continue
                
            media = media_list[0]
            if 'video_info' not in media:
                continue
                
            variants = media['video_info'].get('variants', [])
            # Find highest quality mp4
            mp4s = [v for v in variants if v.get('content_type') == 'video/mp4']
            if not mp4s:
                continue
                
            best_mp4 = max(mp4s, key=lambda x: x.get('bitrate', 0))
            video_url = best_mp4.get('url')
            if not video_url:
                continue

            print(f"Found new video for today! Tweet ID: {tweet_id}")
            
            # Download the video
            output_path = os.path.join(TEMP_DIR, f"{tweet_id}.mp4")
            try:
                print(f"Downloading {video_url}...")
                video_req = requests.get(video_url, stream=True, timeout=30)
                video_req.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in video_req.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception as e:
                print(f"Failed to download video {tweet_id}: {e}")
                continue

            # Extract metadata
            tweet_text = tweet.get('full_text', tweet.get('text', 'FIFA World Cup Highlight'))
            title_match = re.sub(r'https?://\S+', '', tweet_text).strip()
            if not title_match:
                title_match = "FIFA World Cup Highlight"
            elif len(title_match) > 60:
                title_match = title_match[:57] + "..."
                
            try:
                upload_dt = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S +0000 %Y")
                upload_date_str = upload_dt.strftime("%d %B %Y").lstrip("0")
                upload_time_str = upload_dt.strftime("%I:%M %p UTC")
            except:
                upload_date_str = "Unknown"
                upload_time_str = "Unknown"
                
            download_dt = datetime.utcnow()
            download_time_str = download_dt.strftime("%I:%M %p UTC")
            
            duration_ms = media['video_info'].get('duration_millis', 0)
            video_type = "Short Video" if duration_ms and duration_ms < 60000 else "Long Video"
            
            source_url = f"https://x.com/{username}/status/{tweet_id}"
            
            caption = (
                "✅ New FIFA Video Downloaded\n\n"
                f"Video Title: {title_match}\n\n"
                f"Source Profile Name: {profile_name}\n\n"
                f"Source Username: @{username}\n\n"
                f"Original Twitter/X URL:\n{source_url}\n\n"
                f"Upload Date: {upload_date_str}\n\n"
                f"Upload Time: {upload_time_str}\n\n"
                f"Download Time: {download_time_str}\n\n"
                f"Video Type: {video_type}\n\n"
                "Download Status: Successfully Downloaded and Sent to Telegram Channel"
            )
            
            print(f"Sending {output_path} to Telegram...")
            send_video(output_path, caption=caption)
            
            # Mark as done
            append_to_archive(tweet_id)
            append_to_archive(f"twitter {tweet_id}")
            
            # Cleanup
            try:
                os.remove(output_path)
            except:
                pass
                
            video_downloaded = True
            break # Stop processing other tweets for this profile since we only want 1 video

        if video_downloaded:
            print("Successfully downloaded a video. Stopping the scanning process to respect priority order.")
            return # Stop scanning any other profiles entirely
            
    print("No new videos found in any of the targeted profiles.")

if __name__ == "__main__":
    run_downloader()
