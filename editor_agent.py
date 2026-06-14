import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from editor.advanced_editor import process_video_dynamically
from common.limits import can_edit, increment_edit
from common.queue_manager import get_oldest_video_by_status, mark_video_status
from common.telegram import send_message, update_queue_message, report_edit_start

def run_editor_agent():
    print("Starting Editor Agent (Queue Mode)...")
    
    if not can_edit():
        print("Daily Edit Limit Reached (5/5). Exiting editor.")
        return None
        
    print(">>> Checking Queue for downloaded videos...")
    best_video = get_oldest_video_by_status("downloaded")
    
    if not best_video:
        print("No downloaded videos found in the queue.")
        return None
        
    task_id = best_video['id']
    raw_path = best_video['local_path']
    print(f"Editing Video {task_id}...")
    
    report_edit_start()
    edited_path = f"temp/edited_{task_id}.mp4"
    
    try:
        edited_path, hook_line = process_video_dynamically(raw_path, 'assets/custom_logo.png', edited_path, task=best_video)
        
        # Update video_data
        best_video["status"] = "edited"
        best_video["edited_path"] = edited_path
        best_video["hook_line"] = hook_line
        best_video["edit_time"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        
        # Save the status back to queue.json and edit the Telegram queue message
        mark_video_status(task_id, "edited", edited_path=edited_path, hook_line=hook_line, edit_time=best_video["edit_time"])
        update_queue_message(best_video)
        
        increment_edit()
        print("Successfully edited a video.")
        return best_video
        
    except Exception as e:
        print(f"Editing failed: {e}")
        send_message(f"❌ <b>Editing Failed for {task_id}:</b>\n{e}")
        mark_video_status(task_id, "failed")
        return None

if __name__ == "__main__":
    run_editor_agent()
