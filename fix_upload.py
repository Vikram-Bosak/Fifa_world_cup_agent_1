import subprocess
from common.telegram import send_video, send_message

print("Compressing video to fit Telegram 50MB limit...")
subprocess.run([
    "ffmpeg", "-y", "-i", "temp/edited_2065121006038237667.mp4",
    "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-c:a", "aac", "-b:a", "128k",
    "temp/small_2065121006038237667.mp4"
], check=True)

print("Sending compressed video to Telegram...")
send_message("✅ **Manual Edit Successful**\nPOST ID: 20260612_052826_2065121006038237667\n(Compressed for Telegram)")
send_video("temp/small_2065121006038237667.mp4", caption="Here is the final edited video!")
