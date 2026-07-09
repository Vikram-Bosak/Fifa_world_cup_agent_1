import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_1_downloader import run_downloader, save_to_history
from src.agent_2_editor import process_video
from src.agent_3_uploader import run_upload
from src.common.limits import can_download, can_upload, increment_download, increment_edit, increment_upload
from src.common.discord import (
    report_download_start, 
    report_download_complete, 
    report_edit_start, 
    report_edit_complete, 
    send_discord_message
)

def run_single_sequence():
    print("\n--- STARTING SEQUENTIAL PIPELINE (SINGLE RUN) ---")
    
    if not can_download() or not can_upload():
        print("Daily upload limit reached. Exiting.")
        return False

    # 1. Download
    report_download_start()
    video_data, stats = run_downloader()
    if not video_data:
        print("No video found.")
        return False
        
    task_id = video_data['id']
    title = video_data.get('title', '')
    source_url = video_data.get('source_url', '')
    
    # Pre-screening text metadata safety check
    from src.common.safety_filter import check_metadata_safety
    safety_check = check_metadata_safety(title, source_url)
    if not safety_check["is_safe"]:
        reasons = ", ".join(safety_check["reasons"])
        print(f"Video {task_id} rejected by safety filter: {reasons}")
        send_discord_message(f"⚠️ **Video {task_id} Rejected by Safety Filter:**\n{reasons}")
        # Save to history to prevent picking this unsafe video again
        save_to_history(task_id)
        return False
        
    print(f"Downloaded Video: {task_id}")
    report_download_complete(source_url)
    send_discord_message(f"🆔 **Unique ID generated:** {task_id}")
    increment_download()
    
    # Save to history immediately to prevent infinite retry loops if edit/upload fails
    save_to_history(task_id)
    
    # IMMEDIATELY push to GitHub so if the user triggers another run during the 15-minute sleep, it won't duplicate!
    print("Pushing history to GitHub immediately to prevent race conditions...")
    try:
        import subprocess
        subprocess.run("git config --global user.name 'github-actions[bot]'", shell=True)
        subprocess.run("git config --global user.email 'github-actions[bot]@users.noreply.github.com'", shell=True)
        subprocess.run("git add downloaded_history.txt", shell=True)
        subprocess.run("git add temp/daily_limits.json", shell=True)
        subprocess.run("git commit -m 'Update history (mid-run)'", shell=True)
        subprocess.run("git pull origin main --rebase --strategy-option=ours", shell=True)
        subprocess.run("git push origin HEAD:main", shell=True)
        print("History pushed successfully.")
    except Exception as e:
        print(f"Warning: Mid-run history push failed: {e}")
    
    # 2. Edit
    report_edit_start()
    try:
        print(f"Editing Video {task_id}...")
        video_data = process_video(video_data)
        if video_data.get('editing_status') == 'Success':
            report_edit_complete()
            increment_edit()
            stats["videos_edited"] = 1
        else:
            send_discord_message(f"❌ **Editing Failed for {task_id}**")
            stats["errors"].append(f"Editing Failed for {task_id}")
            return False
    except Exception as e:
        print(f"Editing failed: {e}")
        send_discord_message(f"❌ **Editing Failed for {task_id}:**\n{e}")
        stats["errors"].append(f"Editing Exception: {str(e)}")
        return False
        
    # 3. Upload
    print(f"Uploading Video {task_id}...")
    video_data = run_upload(video_data)
    
    if video_data.get('upload_status') == 'Success':
        increment_upload()
        stats["videos_uploaded"] = 1
    
    print("Pipeline run completed.")
    return True

if __name__ == "__main__":
    run_single_sequence()
