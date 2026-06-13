import os
import sys
import time
import random
import shutil
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader.standalone_downloader import run_downloader
from editor.advanced_editor import process_video_dynamically
from uploader.uploader import run_upload_pipeline
from common.limits import can_download, can_edit, can_upload, increment_edit
from common.telegram import report_final_summary


def is_us_peak_time():
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    hour = est_time.hour
    return (8 <= hour < 10) or (12 <= hour < 14) or (17 <= hour < 20)

def cleanup_temp():
    try:
        shutil.rmtree("temp")
        os.makedirs("temp", exist_ok=True)
    except Exception as e:
        print(f"Cleanup error: {e}")

def run_sequential_pipeline():
    print("Starting Sequential Pipeline Monitor...")
    
    while True:
        # Wait an hour if limits reached
        if not can_download() or not can_upload():
            print("Daily upload limit reached (5/5). Sleeping for 1 hour...")
            time.sleep(3600)
            continue
        if not is_us_peak_time():
            print("Not currently US peak time. Waiting for 10 minutes...")
            time.sleep(600)
            continue
            
        run_single_sequence()
        
from common.telegram import report_final_summary, report_download_start, report_download_complete, report_edit_start, report_edit_complete, send_message

def run_single_sequence():
    print("\n--- STARTING SEQUENTIAL PIPELINE (SINGLE RUN) ---")
    
    # 1. Download
    report_download_start()
    video_data = run_downloader()
    if not video_data:
        print("No video found.")
        send_message("⚠️ <b>Download Skipped:</b> No new videos found in RSS Feed.")
        return False
        
    task_id = video_data['id']
    raw_path = video_data['local_path']
    print(f"Downloaded Video: {task_id}")
    report_download_complete(video_data['source_url'])
    send_message(f"🆔 <b>Unique ID generated:</b> {task_id}")
    
    # 2. Edit
    report_edit_start()
    edited_path = f"temp/edited_{task_id}.mp4"
    try:
        print(f"Editing Video {task_id}...")
        edited_path, hook_line = process_video_dynamically(raw_path, 'assets/custom_logo.png', edited_path, task=video_data)
        increment_edit()
        video_data['edited_path'] = edited_path
        video_data['hook_line'] = hook_line
        video_data['edit_time'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    except Exception as e:
        print(f"Editing failed: {e}")
        send_message(f"❌ <b>Editing Failed for {task_id}:</b>\n{e}")
        cleanup_temp()
        return False
        
    # 3. Upload
    if "--test" not in sys.argv:
        delay_minutes = random.randint(1, 15)
        print(f"Applying Human Delay! Sleeping for {delay_minutes} minutes before Upload...")
        time.sleep(delay_minutes * 60)
    else:
        print("Test mode active: Skipping human delay before Upload...")
    
    try:
        print(f"Starting Upload Process for {task_id}...")
        run_upload_pipeline(edited_path, task_id)
    except Exception as e:
        print(f"Upload failed: {e}")
        send_message(f"❌ <b>Upload Failed for {task_id}:</b>\n{e}")
        cleanup_temp()
        return False
    
    # 4. Cleanup
    print("Upload complete. Cleaning up temporary files...")
    cleanup_temp()
    return True

def run_action_mode():
    print("Starting Pipeline in GitHub Action Mode...")
    
    # Check upload limit first
    if not can_upload():
        print("Daily upload limit reached (5/5). Exiting...")
        return
        
    run_single_sequence()
    print("Pipeline run completed. Exiting.")

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    if "--test" in sys.argv:
        print("Running in TEST MODE. Bypassing delays for a single run...")
        run_single_sequence()
    elif "--production" in sys.argv:
        print("Running in PRODUCTION MODE. Starting continuous loop...")
        run_sequential_pipeline()
    else:
        run_action_mode()
