import os
import sys
import time
import requests
import json
import re
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from the common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_message
from common.limits import can_download, increment_download
from downloader.x_scraper import get_latest_video_tweets

load_dotenv()

# We expect X_PROFILES in .env separated by comma
X_PROFILES_ENV = os.getenv("X_PROFILES", "")
X_PROFILES = [url.strip() for url in X_PROFILES_ENV.split(",") if url.strip()]

X_BACKUP_PROFILES_ENV = os.getenv("X_BACKUP_PROFILES", "")
X_BACKUP_PROFILES = [url.strip() for url in X_BACKUP_PROFILES_ENV.split(",") if url.strip()]

if not X_PROFILES and not X_BACKUP_PROFILES:
    print("Warning: No X_PROFILES or X_BACKUP_PROFILES found in .env. Downloader will not find any videos.")

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

def _find_best_video(profiles: list, archive: set) -> dict:
    if not profiles:
        return None
        
    print(f"Scanning profiles: {profiles}")
    # Get up to 3 videos per profile to ensure we have options to sort
    recent_videos = get_latest_video_tweets(profiles, max_per_profile=3)
    
    valid_candidates = []
    for v in recent_videos:
        if v['tweet_id'] not in archive and v.get('parsed_datetime'):
            valid_candidates.append(v)
            
    if not valid_candidates:
        return None
        
    # Sort by parsed_datetime descending (newest first)
    valid_candidates.sort(key=lambda x: x['parsed_datetime'], reverse=True)
    return valid_candidates[0]

def run_downloader():
    print("Starting standalone downloader with Direct X (Twitter) Scanning...")
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return None
        
    os.makedirs(TEMP_DIR, exist_ok=True)
    archive = load_archive()
    
    all_profiles = X_PROFILES + X_BACKUP_PROFILES
    best_video = None
    
    print(">>> Beginning Sequential Profile Scan...")
    for profile in all_profiles:
        print(f"--- Checking Profile: {profile} ---")
        best_video = _find_best_video([profile], archive)
        if best_video:
            print(f"✅ Found valid video in {profile}. Stopping scan.")
            break
        else:
            print(f"❌ No valid videos found in {profile} (within last 4 hours). Moving to next...")
            
    if not best_video:
        print("No new videos found in any of the provided profiles within the last 4 hours.")
        return None
        
    # Proceed to download the single best video
    tweet_id = best_video['tweet_id']
    tweet_url = best_video['tweet_url']
    profile_url = best_video['profile_url']
    post_time = best_video['timestamp']
    
    print(f"Found NEW video tweet! ID: {tweet_id} at {tweet_url}")
    output_path = os.path.join(TEMP_DIR, f"{tweet_id}.mp4")
        
    # Download using yt-dlp
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", output_path,
        "--merge-output-format", "mp4",
        tweet_url
    ]
    
    try:
        print(f"Downloading {tweet_url} using yt-dlp...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download video {tweet_id}: {e}")
        print("Output:", e.stdout)
        print("Error:", e.stderr)
        return None
        
    if not os.path.exists(output_path):
        print("Download failed, output file not found.")
        return None
        
    title_match = f"Twitter Video from {profile_url.split('/')[-1]}"
    download_dt = datetime.utcnow()
    post_id = f"{download_dt.strftime('%Y%m%d_%H%M%S')}_{tweet_id}"
    file_name = os.path.basename(output_path)
    
    message_text = (
        f"📥 **DOWNLOAD REPORT**\n\n"
        f"**Workflow Name:** FIFA Auto Pipeline\n"
        f"**Download Time:** {download_dt.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Video Title:** {title_match}\n"
        f"**Source URL:** {tweet_url}\n"
        f"**Download Status:** SUCCESS\n"
        f"**File Name:** {file_name}"
    )
    
    print(f"Sending Download Status Report to Telegram...")
    message_id = send_message(message_text)
    
    if message_id:
        print("Status report sent to Telegram. Kept local file for sequential processing.")
    else:
        print("Failed to send status report to Telegram. Proceeding anyway.")
        message_id = "FAILED"
        
    video_data = {
        "id": post_id,
        "tweet_id": tweet_id,
        "message_id": message_id,
        "status": "DOWNLOADED",
        "title": title_match,
        "source": profile_url,
        "source_url": tweet_url,
        "download_time": download_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "timestamp": datetime.utcnow().isoformat(),
        "local_path": output_path
    }
    
    append_to_archive(tweet_id)
    increment_download()
    print("Successfully downloaded a video.")
    return video_data

if __name__ == "__main__":
    run_downloader()
