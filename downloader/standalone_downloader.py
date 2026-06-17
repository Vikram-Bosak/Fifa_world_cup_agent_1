import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from the common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_message, update_queue_message, get_latest_telegram_videos, download_video_from_telegram
from common.limits import can_download, increment_download
from common.queue_manager import get_oldest_video_by_status, mark_video_status, load_queue

load_dotenv()
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

def run_downloader():
    print("Starting Telegram-First Downloader Agent...")
    
    if not can_download():
        print("Daily Download Limit Reached (5/5). Exiting downloader.")
        return None
        
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    print(">>> Fetching latest videos from Telegram chat...")
    videos = get_latest_telegram_videos(limit=100)
    
    if not videos:
        print("No videos found in Telegram chat.")
        return None
        
    queue = load_queue()
    # Find a video that hasn't been downloaded yet
    # We will identify Telegram videos by ID: tg_messageId
    processed_msg_ids = [v.get("message_id") for v in queue if str(v.get("id", "")).startswith("tg_")]
    
    selected_video = None
    for v in videos:
        if v["message_id"] not in processed_msg_ids:
            selected_video = v
            break
            
    if not selected_video:
        print("All recent Telegram videos have already been processed.")
        return None
        
    msg_id = selected_video["message_id"]
    file_id = selected_video["file_id"]
    caption = selected_video["caption"]
    
    post_id = f"tg_{msg_id}"
    print(f"Found unprocessed Telegram video! Message ID: {msg_id}")
    output_path = os.path.join(TEMP_DIR, f"{post_id}.mp4")
    
    print(f"Downloading Telegram video file_id: {file_id}...")
    success = download_video_from_telegram(file_id, output_path)
    
    if not success or not os.path.exists(output_path):
        print("Failed to download video from Telegram.")
        return None
        
    title_match = caption if caption else "Viral Football Video"
    # Keep it short if it's too long
    if len(title_match) > 100:
        title_match = title_match[:97] + "..."
        
    download_dt = datetime.utcnow()
    file_name = os.path.basename(output_path)
    
    message_text = (
        f"📥 **DOWNLOAD REPORT (From Telegram)**\n\n"
        f"**Workflow Name:** FIFA Auto Pipeline\n"
        f"**Download Time:** {download_dt.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Video Title:** {title_match}\n"
        f"**Download Status:** SUCCESS\n"
        f"**File Name:** {file_name}"
    )
    
    print(f"Sending Download Status Report to Telegram...")
    report_msg_id = send_message(message_text)
    
    # Create the queue entry for the rest of the pipeline
    video_data = {
        "id": post_id,
        "tweet_id": f"telegram_{msg_id}",
        "source_url": "From Telegram",
        "profile": "Telegram Channel",
        "timestamp": download_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "title": title_match,
        "message_id": msg_id,
        "status": "downloaded",
        "download_time": download_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "local_path": output_path
    }
    
    # Save the status back to queue.json
    from common.queue_manager import add_to_queue
    add_to_queue(video_data)
    
    increment_download()
    print("Successfully downloaded a video from Telegram.")
    return video_data

if __name__ == "__main__":
    run_downloader()
