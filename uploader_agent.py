import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from uploader.uploader import run_upload_pipeline
from common.limits import can_upload, get_last_upload_time
from common.queue_manager import get_oldest_video_by_status, mark_video_status
from common.telegram import send_message, update_queue_message

def is_smart_upload_time():
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    current_hour = est_time.hour
    
    # 5 fixed US EST peak slots + temp testing slots
    peak_slots = [3, 4, 8, 12, 16, 19, 21]
    
    if current_hour not in peak_slots:
        return False, f"Not a peak slot (Current EST hour: {current_hour})"
        
    last_upload_str = get_last_upload_time()
    if last_upload_str:
        try:
            # Handle standard string parsing
            last_upload = datetime.fromisoformat(last_upload_str)
            # Ensure timezone-aware comparison if last_upload_time doesn't have it explicitly
            if last_upload.tzinfo is None:
                last_upload = last_upload.replace(tzinfo=timezone.utc)
            # Check minimum 2 hours gap (7200 seconds)
            if (utc_now - last_upload).total_seconds() < 7200:
                return False, "Too soon since last upload (minimum 2 hours gap required)"
        except ValueError:
            pass
            
    return True, "Valid slot"


def run_uploader_agent():
    print("Starting Uploader Agent (Queue Mode)...")
    
    if not can_upload():
        print("Daily Upload Limit Reached (5/5). Exiting uploader.")
        return None
        
    is_smart, reason = is_smart_upload_time()
    if not is_smart:
        print(f"Skipping upload: {reason}")
        return None
        
    print(">>> Checking Queue for edited videos...")
    best_video = get_oldest_video_by_status("edited")
    
    if not best_video:
        print("No edited videos found in the queue.")
        return None
        
    task_id = best_video['id']
    edited_path = best_video['edited_path']
    print(f"Uploading Video {task_id}...")
    
    import random
    import time
    
    delay_seconds = random.randint(60, 900) # 1 to 15 minutes
    print(f"Applying random human-like delay of {delay_seconds // 60} minutes and {delay_seconds % 60} seconds before upload...")
    time.sleep(delay_seconds)
    
    try:
        run_upload_pipeline(edited_path, task_id)
        
        # Update video_data
        best_video["status"] = "uploaded"
        
        # Save the status back to queue.json and edit the Telegram queue message
        mark_video_status(task_id, "uploaded")
        update_queue_message(best_video)
        
        print("Successfully uploaded a video.")
        return best_video
        
    except Exception as e:
        print(f"Upload failed: {e}")
        send_message(f"❌ <b>Upload Failed for {task_id}:</b>\n{e}")
        mark_video_status(task_id, "failed")
        return None

if __name__ == "__main__":
    run_uploader_agent()
