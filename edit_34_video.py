import os
import subprocess
from editor.advanced_editor import process_video_dynamically
from common.telegram import send_message, send_video

video_url = "https://www.youtube.com/shorts/0wRSwg9dU5E"
post_id = "youtube_0wRSwg9dU5E"
temp_input = f"temp/{post_id}.mp4"
temp_output = f"temp/edited_{post_id}.mp4"
temp_small = f"temp/small_{post_id}.mp4"

task = {
    "id": post_id,
    "title": "Amazing Football Skills",
    "source": "YouTube Shorts",
    "source_url": video_url
}

send_message(f"📥 **Downloading 3:4 Video...**\nURL: {video_url}")

# Download Video
import sys
try:
    subprocess.run([
        sys.executable, "-m", "yt_dlp", "-o", temp_input, "--merge-output-format", "mp4", video_url
    ], check=True)
except Exception as e:
    send_message(f"❌ Failed to download video: {e}")
    exit(1)

send_message(f"🎬 **Editing 3:4 Video (Converting to 9:16 with borders)...**")

# Process Video
try:
    process_video_dynamically(
        input_path=temp_input,
        logo_path="assets/custom_logo.png",
        output_path=temp_output,
        task=task
    )
except Exception as e:
    send_message(f"❌ Failed to edit video: {e}")
    exit(1)

send_message(f"📦 **Compressing for Telegram...**")

# Compress Video
try:
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_output,
        "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-c:a", "aac", "-b:a", "128k",
        temp_small
    ], check=True)
except Exception as e:
    send_message(f"❌ Failed to compress video: {e}")
    exit(1)

# Upload Video
send_message("✅ **Edit Successful! Sending video...**")
try:
    send_video(temp_small, caption=f"Here is how a 3:4 video looks after our 9:16 editing template!\nSource: {video_url}")
except Exception as e:
    send_message(f"❌ Failed to upload video: {e}")

print("Done!")
