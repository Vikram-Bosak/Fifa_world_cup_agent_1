import os
import sys
from datetime import datetime

# Add parent directory to path so we can import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common.telegram import send_video

output_path = "assets/fallback.mp4"
title_match = "TEST VIDEO: FIFA World Cup Highlights"
profile_name = "FIFA World Cup"
username = "FIFAWorldCup"
upload_date_str = "11 June 2026"
upload_time_str = "07:25 PM UTC"
download_time_str = datetime.utcnow().strftime("%I:%M %p UTC")
video_type = "Short Video"
source_url = "https://x.com/FIFAWorldCup/status/0000000000000"

caption = (
    "✅ New FIFA Video Downloaded\n\n"
    f"Video Title: {title_match}\n\n"
    f"Source Profile Name: {profile_name}\n\n"
    f"Source Username: @{username}\n\n"
    f"Original Twitter/X URL:\n{source_url}\n\n"
    f"Upload Date: {upload_date_str}\n\n"
    f"Upload Time: {upload_time_str}\n\n"
    f"Download Time: {download_time_str}\n\n"
    f"Video Type: {video_type}\n\n"
    "Download Status: Successfully Downloaded and Sent to Telegram Channel"
)

print("Sending test report to Telegram...")
send_video(output_path, caption=caption)
