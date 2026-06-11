import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_message(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration is missing. Cannot send message:", message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def send_video(video_path: str, caption: str = "") -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration is missing. Cannot send video.")
        return
        
    if not os.path.exists(video_path):
        print(f"Video file {video_path} not found.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            response = requests.post(url, data=data, files=files, timeout=60)
            response.raise_for_status()
            print("Video sent to Telegram successfully!")
    except Exception as e:
        print(f"Failed to send Telegram video: {e}")

def get_run_details() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID", "Unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Unknown")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"<b>Run ID:</b> {run_id}\n<b>Workflow:</b> {workflow}\n<b>Time:</b> {current_time}"

def report_download_start():
    msg = f"🟢 <b>Video Download Started</b>\n{get_run_details()}"
    send_message(msg)

def report_download_complete(source_url: str):
    msg = f"✅ <b>Video Download Completed</b>\n<b>Source:</b> {source_url}\n{get_run_details()}"
    send_message(msg)

def report_edit_start():
    msg = f"🟡 <b>Video Editing Started</b>\n{get_run_details()}"
    send_message(msg)

def report_edit_complete():
    msg = f"✅ <b>Video Editing Completed</b>\n{get_run_details()}"
    send_message(msg)

def report_upload_complete(platform: str, url: str, title: str, description: str):
    msg = (
        f"🚀 <b>{platform} Upload Completed</b>\n"
        f"<b>URL:</b> {url}\n"
        f"<b>Title:</b> {title}\n"
        f"<b>Description:</b> {description}\n"
        f"{get_run_details()}"
    )
    send_message(msg)

def report_final_summary(summary_data: dict):
    # Determine success status
    job_status = summary_data.get('job_status', 'Success')
    fb_url = summary_data.get('fb_url', 'N/A')
    yt_url = summary_data.get('yt_url', 'N/A')
    
    fb_status = "Success" if fb_url != "N/A" else "Failed/Skipped"
    yt_status = "Success" if yt_url != "N/A" else "Failed/Skipped"
    
    title = summary_data.get('title', 'Automated FIFA Short')
    description = summary_data.get('description', '')
    original_file = summary_data.get('original_file', 'downloaded_video.mp4')
    
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "Vikram-Bosak/Fifa_world_cup_agent_1")
    workflow_url = f"https://github.com/{repo_name}/actions/runs/{run_id}" if run_id else f"https://github.com/{repo_name}/actions"
    repo_url = f"https://github.com/{repo_name}"
    
    msg = (
        f"✅ <b>Upload Successfully Completed</b>\n\n"
        f"🎬 <b>Video Name:</b>\n"
        f"{title}\n\n"
        f"📤 <b>Facebook Upload Status:</b> {fb_status}\n"
        f"📤 <b>YouTube Upload Status:</b> {yt_status}\n\n"
        f"🏷️ <b>SEO Title:</b>\n"
        f"{title}\n\n"
        f"📝 <b>Description:</b>\n"
        f"{description}\n\n"
        f"Original File: {original_file}\n\n"
        f"🔗 <b>Facebook Reel URL:</b>\n"
        f"{fb_url}\n\n"
        f"▶️ <b>YouTube Video URL:</b>\n"
        f"{yt_url}\n\n"
        f"📦 <b>GitHub Repository:</b>\n"
        f"{repo_url}\n\n"
        f"📄 <b>Workflow Run:</b>\n"
        f"{workflow_url}"
    )
    send_message(msg)
