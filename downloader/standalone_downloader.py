import os
import sys
import json
from datetime import datetime
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

def run_downloader():
    print("Starting Agent 1: Telegram Downloader (Sequential Mode)")
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Check if download limit is reached
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.limits import can_download, increment_download
    from common.telegram import get_latest_telegram_videos, download_video_from_telegram
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return None
        
    print("Fetching videos from Telegram...")
    videos = get_latest_telegram_videos(limit=50)
    history = load_history()
    
    selected_video = None
    for vid in videos:
        file_id = str(vid["file_id"])
        # We can use message_id or file_id for history tracking. Let's use file_id.
        if file_id not in history:
            selected_video = vid
            break
            
    if not selected_video:
        print("No new valid videos found in Telegram.")
        return None
        
    file_id = selected_video["file_id"]
    title = selected_video.get("caption", f"Telegram Video {file_id}")
    if not title:
        title = f"Telegram Video {file_id}"
        
    video_path = os.path.join(TEMP_DIR, "raw_video.mp4")
    
    print(f"Selected valid video: {file_id}")
    success = download_video_from_telegram(file_id, video_path)
    
    if success and os.path.exists(video_path):
        save_to_history(file_id)
        video_data = {
            "id": file_id,
            "tweet_id": file_id, # for compatibility with old names
            "title": title,
            "source_url": "Telegram",
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
