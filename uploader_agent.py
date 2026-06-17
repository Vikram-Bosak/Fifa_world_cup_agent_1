import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from uploader.uploader import run_upload_pipeline
from common.limits import can_upload, get_last_upload_time
from common.telegram import send_message

def is_smart_upload_time():
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    current_hour = est_time.hour
    
    # 5 fixed US EST peak slots
    peak_slots = [8, 12, 16, 19, 21]
    
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

def run_uploader_agent(video_data=None, force=False):
    print("Starting Uploader Agent...")
    
    if not video_data:
        print("No video data provided to uploader.")
        return None
        
    if not force and not can_upload():
        print("Daily Upload Limit Reached (5/5). Exiting uploader.")
        return None
        
    if not force:
        is_smart, reason = is_smart_upload_time()
        if not is_smart:
            print(f"Skipping upload: {reason}")
            return None
    else:
        print("Force upload flag is set. Bypassing upload limits and smart timing checks.")
        
    task_id = video_data['id']
    edited_path = video_data['edited_path']
    print(f"Uploading Video {task_id}...")
    
    import random
    import time
    
    if not force:
        delay_seconds = random.randint(60, 900) # 1 to 15 minutes
        print(f"Applying random human-like delay of {delay_seconds // 60} minutes and {delay_seconds % 60} seconds before upload...")
        time.sleep(delay_seconds)
    else:
        print("Force upload flag is set. Skipping random human-like delay...")
    
    try:
        run_upload_pipeline(edited_path, task_id)
        
        # Update video_data
        video_data["status"] = "uploaded"
        print("Successfully uploaded a video.")
        return video_data
        
    except Exception as e:
        print(f"Upload failed: {e}")
        send_message(f"❌ <b>Upload Failed for {task_id}:</b>\n{e}")
        video_data["status"] = "failed"
        return video_data

if __name__ == "__main__":
    pass
