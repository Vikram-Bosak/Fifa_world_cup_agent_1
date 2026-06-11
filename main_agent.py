import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader.standalone_downloader import run_downloader
from editor.advanced_editor import process_video_dynamically
from uploader.uploader import run_upload_pipeline
from common.limits import can_edit, can_upload, increment_edit

PENDING_TASKS_FILE = "temp/pending_tasks.json"

def main():
    print("Starting Main Agent Pipeline...")
    
    # 1. Run Downloader
    try:
        run_downloader()
    except Exception as e:
        print(f"Downloader failed: {e}")
        
    if not os.path.exists(PENDING_TASKS_FILE):
        print("No pending tasks file found. Exiting.")
        return

    try:
        with open(PENDING_TASKS_FILE, "r") as f:
            tasks = json.load(f)
    except Exception as e:
        print(f"Error reading tasks file: {e}")
        return

    # 2. Run Editor
    for task in tasks:
        task_id = task.get("id")
        if task.get("status") == "DOWNLOADED":
            if not can_edit():
                print("Daily edit limit reached. Skipping remaining edits.")
                break
                
            print(f"Editing task {task_id}...")
            input_path = task.get('local_path')
            if not input_path or not os.path.exists(input_path):
                print(f"Input file {input_path} missing. Skipping edit.")
                continue
                
            output_path = f"temp/edited_{task_id}.mp4"
            
            try:
                # This will automatically generate the AI hook and save it to state_upload.json
                process_video_dynamically(input_path, 'assets/custom_logo.png', output_path)
                
                # Retrieve hook to save into tasks state
                hook_line = "EPIC FIFA MOMENT"
                if os.path.exists("temp/state_upload.json"):
                    with open("temp/state_upload.json", "r") as state_file:
                        state_data = json.load(state_file)
                        hook_line = state_data.get("hook_line", hook_line)
                        
                task['edited_path'] = output_path
                task['hook_line'] = hook_line
                task['status'] = "EDITED"
                increment_edit()
                
            except Exception as e:
                print(f"Editing failed for {task_id}: {e}")
                task['status'] = "EDIT_FAILED"

            with open(PENDING_TASKS_FILE, "w") as f:
                json.dump(tasks, f, indent=4)

    # 3. Run Uploader
    for task in tasks:
        task_id = task.get("id")
        if task.get("status") == "EDITED":
            if not can_upload():
                print("Daily upload limit reached. Skipping remaining uploads.")
                break
                
            print(f"Uploading task {task_id}...")
            edited_path = task.get('edited_path')
            if not edited_path or not os.path.exists(edited_path):
                print(f"Edited file {edited_path} missing. Skipping upload.")
                continue
                
            # Restore the hook for uploader to use
            hook_line = task.get('hook_line', '')
            os.makedirs("temp", exist_ok=True)
            with open("temp/state_upload.json", "w") as state_file:
                json.dump({"hook_line": hook_line, "original_file": task.get('source_url', task_id)}, state_file)
                
            try:
                run_upload_pipeline(edited_path)
                task['status'] = "UPLOADED"
            except Exception as e:
                print(f"Uploading failed for {task_id}: {e}")
                task['status'] = "UPLOAD_FAILED"
                
            with open(PENDING_TASKS_FILE, "w") as f:
                json.dump(tasks, f, indent=4)
                
    print("Main Agent Pipeline finished.")

if __name__ == "__main__":
    main()
