import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_message(message: str) -> bool:
    if not DISCORD_WEBHOOK_URL:
        print("Discord configuration is missing. Cannot send message:", message)
        return False

    payload = {
        "content": message
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Discord message: {e}")
        return False

def send_video(video_path: str, caption: str = ""):
    if not DISCORD_WEBHOOK_URL:
        print("Discord configuration is missing. Cannot send video.")
        return None, None
        
    if not os.path.exists(video_path):
        print(f"Video file {video_path} not found.")
        return None, None

    # Check file size (Discord free tier limit is 25MB)
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    if file_size_mb > 25:
        print(f"Video {video_path} is {file_size_mb:.2f}MB, which exceeds Discord's 25MB limit. Sending text only.")
        send_message(f"{caption}\n\n*Video too large for Discord webhook ({file_size_mb:.2f}MB)*")
        return None, None

    try:
        with open(video_path, 'rb') as video_file:
            files = {'file': (os.path.basename(video_path), video_file, 'video/mp4')}
            data = {'content': caption}
            response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=60)
            response.raise_for_status()
            print("Video sent to Discord successfully!")
            return True, None
    except Exception as e:
        print(f"Failed to send Discord video: {e}")
    return None, None

def get_run_details() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID", "Unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Unknown")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"**Run ID:** {run_id}\n**Workflow:** {workflow}\n**Time:** {current_time}"

def report_download_start():
    msg = f"🟢 **FIFA World Cup Download Started**\n{get_run_details()}"
    send_message(msg)

def report_download_complete(source_url: str):
    msg = f"✅ **FIFA World Cup Download Completed**\n**Source:** {source_url}\n{get_run_details()}"
    send_message(msg)

def report_edit_start():
    msg = f"🟡 **Video Editing Started**\n{get_run_details()}"
    send_message(msg)

def report_edit_complete():
    msg = f"✅ **Video Editing Completed**\n{get_run_details()}"
    send_message(msg)

def report_upload_delay(delay_minutes: float):
    msg = f"⏳ **Waiting for {delay_minutes:.1f} minutes** before uploading to simulate human behavior...\n{get_run_details()}"
    send_message(msg)

def report_upload_complete(platform: str, url: str, title: str, description: str):
    msg = (
        f"🚀 **{platform} Upload Completed**\n"
        f"**URL:** {url}\n"
        f"**Title:** {title}\n"
        f"**Description:** {description}\n"
        f"{get_run_details()}"
    )
    send_message(msg)

def report_final_summary(summary_data: dict, stats: dict = None):
    stats = stats or {}
    profiles_scanned = stats.get('profiles_scanned', 0)
    new_videos = stats.get('new_videos_found', 0)
    skipped = stats.get('videos_skipped', 0)
    downloaded = stats.get('videos_downloaded', 0)
    edited = stats.get('videos_edited', 0)
    uploaded = stats.get('videos_uploaded', 0)
    errors = stats.get('errors', [])
    
    error_text = "\n".join([f"❌ {e}" for e in errors]) if errors else "None"
    
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "Vikram-Bosak/Fifa_world_cup_agent_1")
    workflow_url = f"https://github.com/{repo_name}/actions/runs/{run_id}" if run_id else f"https://github.com/{repo_name}/actions"
    
    if not summary_data:
        # Just send the stats report if no video was fully processed
        msg = (
            f"ℹ️ **Pipeline Scan Report**\n\n"
            f"🔍 **Profiles Scanned:** {profiles_scanned}\n"
            f"🆕 **New Videos Found (Last 3 hours):** {new_videos}\n"
            f"⏭️ **Videos Skipped (Already Processed):** {skipped}\n"
            f"📥 **Videos Downloaded:** {downloaded}\n\n"
            f"⚠️ **Errors:**\n{error_text}\n\n"
            f"📄 **Workflow Run:**\n{workflow_url}"
        )
        send_message(msg)
        return

    # Determine success status
    job_status = str(summary_data.get('job_status', 'Success'))
    fb_url = str(summary_data.get('fb_url', 'N/A'))
    yt_url = str(summary_data.get('yt_url', 'N/A'))
    
    fb_err = str(summary_data.get('fb_err', 'Unknown Error'))
    yt_err = str(summary_data.get('yt_err', 'Unknown Error'))
    
    fb_status = "Success" if fb_url not in ["Failed", "N/A", "None", None] else f"Failed ({fb_err})"
    yt_status = "Success" if yt_url not in ["Failed", "N/A", "None", None] else f"Failed ({yt_err})"
    
    title = str(summary_data.get('title', 'Automated FIFA World Cup Reel'))
    
    msg = (
        f"✅ **Upload Successfully Completed**\n\n"
        f"📊 **Session Statistics:**\n"
        f"🔍 Profiles Scanned: {profiles_scanned}\n"
        f"🆕 New Videos (2h): {new_videos}\n"
        f"⏭️ Videos Skipped: {skipped}\n"
        f"📥 Downloaded: {downloaded}\n"
        f"✏️ Edited: {edited}\n"
        f"🚀 Uploaded: {uploaded}\n\n"
        f"⚠️ **Errors:**\n{error_text}\n\n"
        f"📤 **Facebook Status:** {fb_status}\n"
        f"📤 **YouTube Status:** {yt_status}\n\n"
        f"🏷️ **SEO Title:**\n{title}\n\n"
        f"🔗 **Facebook Reel URL:**\n{fb_url}\n\n"
        f"▶️ **YouTube Video URL:**\n{yt_url}\n\n"
        f"📄 **Workflow Run:**\n{workflow_url}"
    )
    send_message(msg)

def report_success(message: str):
    send_message(f"✅ **Success:** {message}")

def report_failure(message: str):
    send_message(f"❌ **Failure:** {message}")
