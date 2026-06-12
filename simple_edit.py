import os
import sys
import subprocess
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from common.telegram import send_video, send_message

load_dotenv()

input_video = "assets/fallback.mp4"
logo_image = "assets/custom_logo.png"
output_video = "temp/edited_sample.mp4"

def run_edit():
    os.makedirs("temp", exist_ok=True)
    
    # FFmpeg complex filter
    # 1. Video: eq for color grading. 
    # 2. Logo: scale to 150px wide, keeping aspect ratio.
    # 3. Overlay: Top-Right corner (W-w-20, 20).
    # 4. Audio: asetrate and atempo for pitch shift.
    
    filter_complex = (
        "[0:v]eq=saturation=1.3:contrast=1.1[color_graded];"
        "[1:v]scale=150:-1[logo];"
        "[color_graded][logo]overlay=W-w-20:20[v_out];"
        "[0:a]asetrate=44100*1.05,atempo=1/1.05[a_out]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", logo_image,
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "[a_out]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        output_video
    ]
    
    print("Starting video edit...")
    subprocess.run(cmd, check=True)
    print("Video editing completed!")
    
    # Send report and video
    caption = (
        "🎬 <b>Sample Video Edit Completed</b>\n\n"
        "<b>Applied Edits:</b>\n"
        "✅ <b>Color Grading:</b> Saturation (+30%), Contrast (+10%)\n"
        "✅ <b>Audio/Pitch:</b> Pitch Shift (+5%)\n"
        "✅ <b>Branding:</b> Logo Overlay (Top-Right Corner)\n"
        "✅ <b>Quality & Aspect Ratio:</b> Preserved (1280x720)\n\n"
        "This is a demonstration of the Editing Agent."
    )
    
    from common.telegram import TELEGRAM_REPORT_CHAT_ID
    print("Sending edited video to Telegram Report Channel...")
    send_video(output_video, caption=caption, chat_id=TELEGRAM_REPORT_CHAT_ID)
    print("Process finished!")

if __name__ == "__main__":
    run_edit()
