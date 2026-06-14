import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from uploader.uploader import run_upload_pipeline
from common.limits import can_upload
from common.queue_manager import get_oldest_video_by_status, mark_video_status
from common.telegram import send_message, update_queue_message

def run_uploader_agent():
    print("Starting Uploader Agent (Queue Mode)...")
    
    if not can_upload():
        print("Daily Upload Limit Reached (5/5). Exiting uploader.")
        return None
        
    print(">>> Checking Queue for edited videos...")
    best_video = get_oldest_video_by_status("edited")
    
    if not best_video:
        print("No edited videos found in the queue.")
        return None
        
    task_id = best_video['id']
    edited_path = best_video['edited_path']
    print(f"Uploading Video {task_id}...")
    
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
