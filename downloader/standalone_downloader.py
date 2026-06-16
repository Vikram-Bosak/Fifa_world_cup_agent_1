import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from the common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_message, update_queue_message
from common.limits import can_download, increment_download
from common.queue_manager import get_oldest_video_by_status, mark_video_status

load_dotenv()
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

def run_downloader():
    print("Starting Downloader Agent (Queue Mode)...")
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return None
        
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    print(">>> Checking Queue for pending videos...")
    best_video = get_oldest_video_by_status("pending")
            
    if not best_video:
        print("No pending videos found in the queue.")
        return None
        
    # Proceed to download the single best video from queue
    tweet_id = best_video.get('tweet_id')
    tweet_url = best_video.get('source_url')
    profile_url = best_video.get('profile')
    post_id = best_video.get('id')
    
    print(f"Found pending video in queue! ID: {tweet_id} at {tweet_url}")
    output_path = os.path.join(TEMP_DIR, f"{tweet_id}.mp4")
        
    # Download using yt-dlp (First 60 seconds only to avoid long downloads)
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", output_path,
        "--merge-output-format", "mp4",
        "--match-filter", "duration <= 180",
        "--download-sections", "*00:00:00-00:01:00",
        tweet_url
    ]
    
    try:
        print(f"Downloading {tweet_url} using yt-dlp...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download video {tweet_id}: {e}")
        print("Output:", e.stdout)
        print("Error:", e.stderr)
        mark_video_status(post_id, "failed")
        return None
        
    if not os.path.exists(output_path):
        print("Download failed, output file not found.")
        mark_video_status(post_id, "failed")
        return None
        
    # Extract real title using yt-dlp
    title_cmd = [sys.executable, "-m", "yt_dlp", "--print", "title", tweet_url]
    try:
        title_result = subprocess.run(title_cmd, capture_output=True, text=True, check=True)
        title_match = title_result.stdout.strip()
        if not title_match:
            title_match = f"Twitter Video from {profile_url.split('/')[-1] if profile_url else 'Unknown'}"
    except Exception:
        title_match = f"Twitter Video from {profile_url.split('/')[-1] if profile_url else 'Unknown'}"
        
    download_dt = datetime.utcnow()
    file_name = os.path.basename(output_path)
    
    message_text = (
        f"📥 **DOWNLOAD REPORT (From Queue)**\n\n"
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
        
    # Update video_data with new fields needed by the rest of the pipeline
    best_video["status"] = "downloaded"
    best_video["title"] = title_match
    best_video["download_time"] = download_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    best_video["local_path"] = output_path
    
    # Save the status back to queue.json and edit the Telegram queue message
    mark_video_status(post_id, "downloaded", title=title_match, download_time=best_video["download_time"], local_path=output_path)
    update_queue_message(best_video)
    
    increment_download()
    print("Successfully downloaded a video.")
    return best_video

if __name__ == "__main__":
    run_downloader()
