import os
import sys
import subprocess
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_video

def get_video_dimensions(file_path):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        stream = data['streams'][0]
        return int(stream['width']), int(stream['height'])
    except Exception as e:
        print(f"Error getting video dimensions: {e}")
        return 1920, 1080 # fallback to horizontal

def edit_long_video_template(input_path: str, logo_path: str, output_path: str):
    print("Applying Long Video (Horizontal) Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=min(h\\,w)/20:luma_power=1:chroma_radius=min(cw\\,ch)/20:chroma_power=1,colorchannelmixer=rr=0.7:gg=0.7:bb=0.7[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[1:v]scale=200:-1[logo];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        "[merged][logo]overlay=W-w-30:30[with_logo];"
        "[with_logo]drawtext=text='CRAZIEST FIFA MOMENT!':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=200:bordercolor=black:borderw=5:box=1:boxcolor=red@0.8:boxborderw=20[outv]"
    )
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path, "-i", logo_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return "Long Video Template (News Style)"

def edit_short_video_template(input_path: str, logo_path: str, output_path: str):
    print("Applying Short Video (Vertical) Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    filter_complex = (
        # Ensure it's 1080x1920 by scaling and cropping to maintain aspect ratio
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[fg];"
        # Small logo
        "[1:v]scale=120:-1[logo];"
        # Overlay logo
        "[fg][logo]overlay=W-w-30:30[with_logo];"
        # Catchy Headline in center-top
        "[with_logo]drawtext=text='🔥 MESSI MAGIC':fontcolor=white:fontsize=90:x=(w-text_w)/2:y=300:bordercolor=black:borderw=6:shadowcolor=black:shadowx=5:shadowy=5[outv]"
    )
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path, "-i", logo_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return "Short Video Template (Viral Reel)"

def process_video_dynamically(input_path: str, logo_path: str, output_path: str):
    print(f"Analyzing {input_path}...")
    width, height = get_video_dimensions(input_path)
    print(f"Detected Dimensions: {width}x{height}")
    
    if width > height:
        template_used = edit_long_video_template(input_path, logo_path, output_path)
    else:
        template_used = edit_short_video_template(input_path, logo_path, output_path)
        
    print("Video editing completed!")
    
    caption = (
        f"🤖 <b>Dynamic Template Editor Demo</b>\n\n"
        f"<b>Detected Format:</b> {width}x{height}\n"
        f"<b>Template Applied:</b> {template_used}\n\n"
        f"✅ <b>Branding:</b> Logo Applied\n"
        f"✅ <b>Hook:</b> Catchy Text Added\n"
        f"✅ <b>Resolution:</b> 1080x1920 (9:16)"
    )
    
    from common.telegram import TELEGRAM_REPORT_CHAT_ID
    print("Sending to Telegram...")
    send_video(output_path, caption=caption, chat_id=TELEGRAM_REPORT_CHAT_ID)
    print("Process finished!")

if __name__ == "__main__":
    # Test on the horizontal video
    process_video_dynamically("assets/vertical_dummy.mp4", "assets/custom_logo.png", "temp/dynamic_edit.mp4")
