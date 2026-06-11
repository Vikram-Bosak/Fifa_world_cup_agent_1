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
    msg = (
        f"🏁 <b>Workflow Final Summary</b>\n"
        f"<b>Download Source:</b> {summary_data.get('source_url', 'N/A')}\n"
        f"<b>FB Public URL:</b> {summary_data.get('fb_url', 'N/A')}\n"
        f"<b>YT Public URL:</b> {summary_data.get('yt_url', 'N/A')}\n"
        f"<b>Title:</b> {summary_data.get('title', 'N/A')}\n"
        f"<b>Description:</b> {summary_data.get('description', 'N/A')}\n"
        f"<b>Job Status:</b> {summary_data.get('job_status', 'Unknown')}\n"
        f"<b>Execution Time:</b> {summary_data.get('execution_time', 'Unknown')} seconds\n"
        f"{get_run_details()}"
    )
    send_message(msg)
