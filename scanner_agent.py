import os
import sys
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure we can import from the common and downloader modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from downloader.x_scraper import get_latest_video_tweets
from common.queue_manager import add_to_queue, is_duplicate
from common.telegram import send_message

load_dotenv()

# We expect X_PROFILES in .env separated by comma
X_PROFILES_ENV = os.getenv("X_PROFILES", "")
X_PROFILES = [url.strip() for url in X_PROFILES_ENV.split(",") if url.strip()]

X_BACKUP_PROFILES_ENV = os.getenv("X_BACKUP_PROFILES", "")
X_BACKUP_PROFILES = [url.strip() for url in X_BACKUP_PROFILES_ENV.split(",") if url.strip()]

def check_video_metadata(url: str):
    import subprocess
    import json
    try:
        print(f"Checking metadata for {url}...")
        cmd = [sys.executable, "-m", "yt_dlp", "--dump-json", url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        timestamp = info.get("timestamp")
        title = info.get("title", "")
        return timestamp, title
    except Exception as e:
        print(f"Failed to check metadata: {e}")
        return None, ""

def run_scanner():
    print("Starting Twitter Scanner Agent...")
    
    all_profiles = X_PROFILES + X_BACKUP_PROFILES
    if not all_profiles:
        print("Warning: No X_PROFILES or X_BACKUP_PROFILES found in .env.")
        return
        
    print(f"Scanning {len(all_profiles)} profiles for new short videos...")
    
    # Get up to 10 latest videos from each profile to avoid missing them due to pinned tweets
    recent_videos = get_latest_video_tweets(all_profiles, max_per_profile=10)
    
    new_videos_added = 0
    
    for v in recent_videos:
        tweet_id = v['tweet_id']
        tweet_url = v['tweet_url']
        profile_url = v['profile_url']
        
        # Check if already in queue or processed (legacy archive or new queue)
        if is_duplicate(tweet_id):
            print(f"Video {tweet_id} from {profile_url} is already in the queue or processed. Skipping.")
            continue
            
        # Fetch real age and title
        real_timestamp, real_title = check_video_metadata(tweet_url)
        
        if not real_timestamp:
            print(f"Video {tweet_id}: Could not verify the exact post time. Rejecting to enforce strict time rules.")
            continue
            
        from datetime import timedelta
        tweet_time = datetime.fromtimestamp(real_timestamp, tz=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        
        # Calculate time difference
        time_diff = now_utc - tweet_time
        if time_diff > timedelta(hours=2):
            print(f"Video {tweet_id} is strictly older than 2 hours (Age: {time_diff}). Skipping old video.")
            continue
            
        # Parse timestamp
        dt = v.get('parsed_datetime', datetime.now(timezone.utc))
        timestamp_str = dt.strftime('%Y-%m-%d %I:%M %p')
        
        # Generate Unique ID
        download_dt = datetime.utcnow()
        post_id = f"{download_dt.strftime('%Y%m%d_%H%M%S')}_{tweet_id}"
        
        profile_name = profile_url.split('/')[-1] if '/' in profile_url else profile_url
        
        # Format Telegram Notification exactly as requested
        message_text = (
            f"<b>Unique ID:</b> {post_id}\n\n"
            f"<b>Source Account:</b>\n@{profile_name}\n\n"
            f"<b>Title/Description:</b>\n{real_title}\n\n"
            f"<b>Tweet URL:</b>\n{tweet_url}\n\n"
            f"<b>Timestamp:</b>\n{timestamp_str} UTC\n\n"
            f"<b>Status:</b> Pending"
        )
        
        try:
            message_id = send_message(message_text)
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            message_id = None
            
        video_data = {
            "id": post_id,
            "tweet_id": tweet_id,
            "source_url": tweet_url,
            "profile": profile_url,
            "timestamp": timestamp_str,
            "title": real_title,
            "message_id": message_id
        }
        
        # Add to Queue
        if add_to_queue(video_data):
            new_videos_added += 1
            print(f"✅ Added NEW video to Queue: {tweet_url} with msg_id: {message_id}")
                
    if new_videos_added == 0:
        print("No new videos found in this scan.")
    else:
        print(f"Scanner completed. {new_videos_added} new videos added to the queue.")

if __name__ == "__main__":
    run_scanner()
