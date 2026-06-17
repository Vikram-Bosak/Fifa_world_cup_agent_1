import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from editor.advanced_editor import process_video_dynamically
from common.limits import can_edit, increment_edit
from common.telegram import send_message, report_edit_start

def run_editor_agent(video_data=None):
    print("Starting Editor Agent...")
    
    if not video_data:
        print("No video data provided to editor.")
        return None
        
    if not can_edit():
        print("Daily Edit Limit Reached (5/5). Exiting editor.")
        return None
        
    task_id = video_data['id']
    raw_path = video_data['local_path']
    print(f"Editing Video {task_id}...")
    
    report_edit_start()
    edited_path = f"temp/edited_{task_id}.mp4"
    
    try:
        edited_path, hook_line = process_video_dynamically(raw_path, 'assets/custom_logo.png', edited_path, task=video_data)
        
        # Update video_data
        video_data["status"] = "edited"
        video_data["edited_path"] = edited_path
        video_data["hook_line"] = hook_line
        video_data["edit_time"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        
        increment_edit()
        print("Successfully edited a video.")
        return video_data
        
    except Exception as e:
        print(f"Editing failed: {e}")
        send_message(f"❌ <b>Editing Failed for {task_id}:</b>\n{e}")
        video_data["status"] = "failed"
        return video_data

if __name__ == "__main__":
    pass
