import os
import sys
import subprocess
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_video

def create_reels_edit(input_path: str, logo_path: str, output_path: str):
    print("Starting 9:16 Reels/Shorts Editing Process...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # We use FFmpeg to do:
    # 1. Background: scale to fill 1080x1920, crop, and heavily blur.
    # 2. Foreground: scale to fit within 1080x1920 without cropping.
    # 3. Logo: scale to width 180, place at top-right.
    # 4. Text: Draw text "CRAZIEST FIFA MOMENT!" at the top center.
    
    # We will use the built-in drawtext filter. Note that emojis might not render 
    # depending on the font, so we use a safe bold text.
    
    filter_complex = (
        # Background: Scale to cover 1080x1920, crop center, blur, and darken slightly
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=min(h\\,w)/20:luma_power=1:chroma_radius=min(cw\\,ch)/20:chroma_power=1,colorchannelmixer=rr=0.7:gg=0.7:bb=0.7[bg];"
        
        # Foreground: Scale to fit inside 1080x1920
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        
        # Logo: Scale to width 200
        "[1:v]scale=200:-1[logo];"
        
        # Combine Background and Foreground
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        
        # Add Logo to Top-Right
        "[merged][logo]overlay=W-w-30:30[with_logo];"
        
        # Add Text (Headline) at the top center
        "[with_logo]drawtext=text='CRAZIEST FIFA MOMENT!':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=200:bordercolor=black:borderw=5:box=1:boxcolor=red@0.8:boxborderw=20[outv]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", logo_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?", # Map original audio if it exists
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    
    print("Running FFmpeg for 9:16 rendering...")
    subprocess.run(cmd, check=True)
    print("Video editing completed!")
    
    # Send to Telegram
    caption = (
        "📱 <b>Reels/Shorts 9:16 Format Demo</b>\n\n"
        "<b>Applied Edits:</b>\n"
        "✅ <b>Format:</b> 1080x1920 (9:16 Vertical)\n"
        "✅ <b>Background:</b> Blurred Padding (No action cropped!)\n"
        "✅ <b>Foreground:</b> Original video perfectly centered\n"
        "✅ <b>Branding:</b> Logo at Top-Right Corner\n"
        "✅ <b>Headline:</b> Custom Hook Title added at the top\n\n"
        "This output is 100% ready for Instagram, Facebook, and YouTube Shorts."
    )
    
    from common.telegram import TELEGRAM_REPORT_CHAT_ID
    print("Sending to Telegram...")
    send_video(output_path, caption=caption, chat_id=TELEGRAM_REPORT_CHAT_ID)
    print("Process finished!")

if __name__ == "__main__":
    create_reels_edit("assets/fallback.mp4", "assets/custom_logo.png", "temp/reels_edit.mp4")
