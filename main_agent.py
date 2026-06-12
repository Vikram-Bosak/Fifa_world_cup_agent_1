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
        # Check upload limit first
        if not can_upload():
            print("Daily upload limit reached (5/5). Sleeping for 1 hour...")
            time.sleep(3600)
            continue
            
        if not is_us_peak_time():
            print("Not currently US peak time. Waiting for 10 minutes...")
            time.sleep(600)
            continue
            
        # If it IS peak time and we can upload, add human-like random delay
        delay_minutes = random.randint(1, 15)
        print(f"US Peak Time active! Sleeping for {delay_minutes} minutes to simulate human behavior...")
        time.sleep(delay_minutes * 60)
        
        # Double check limit after waking up just in case
        if not can_upload():
            continue
            
        print("\n--- STARTING SEQUENTIAL PIPELINE ---")
        
        # 1. Download
        video_data = run_downloader()
        if not video_data:
            print("No video found. Will try again later.")
            time.sleep(600)
            continue
            
        task_id = video_data['id']
        raw_path = video_data['local_path']
        print(f"Downloaded Video: {task_id}")
        
        # 2. Edit
        edited_path = f"temp/edited_{task_id}.mp4"
        try:
            print(f"Editing Video {task_id}...")
            edited_file_id, hook_line = process_video_dynamically(raw_path, 'assets/custom_logo.png', edited_path, task=video_data)
            increment_edit()
            video_data['edited_file_id'] = edited_file_id
            video_data['hook_line'] = hook_line
            video_data['edit_time'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        except Exception as e:
            print(f"Editing failed: {e}")
            cleanup_temp()
            continue
            
        # 3. Upload
        try:
            print(f"Uploading Video {task_id}...")
            fb_url, yt_url, job_status, fb_err, yt_err = run_upload_pipeline(edited_path, task_id)
            
            video_data['fb_url'] = fb_url
            video_data['yt_url'] = yt_url
            video_data['fb_err'] = fb_err
            video_data['yt_err'] = yt_err
            video_data['upload_time'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            video_data['job_status'] = job_status
            video_data['original_file'] = f"raw_video_{video_data['tweet_id']}.mp4"
            
            # Send Report
            report_final_summary(video_data)
            
        except Exception as e:
            print(f"Uploading failed: {e}")
            
        # 4. Cleanup
        cleanup_temp()
        print("Sequence complete. Waiting 1 hour before next attempt to spread out posts...")
        time.sleep(3600)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    run_sequential_pipeline()
