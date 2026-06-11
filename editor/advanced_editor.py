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
    print("Applying Short Video (Vertical) Hollywood Style Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    filter_complex = (
        # Scale to fit inside the 20px yellow border (1080-40=1040, 1920-40=1880)
        "[0:v]scale=1040:1880:force_original_aspect_ratio=increase,crop=1040:1880[scaled];"
        # Pad with yellow border to make it 1080x1920
        "[scaled]pad=1080:1920:20:20:yellow[padded];"
        # Small logo at top right
        "[1:v]scale=120:-1[logo];"
        "[padded][logo]overlay=W-w-30:30[with_logo];"
        # Catchy Headline (Top) - Yellow text on Black box
        "[with_logo]drawtext=text='EPIC FIFA MOMENT':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=65:x=(w-text_w)/2:y=120:box=1:boxcolor=black:boxborderw=15[with_hook];"
        # Bottom Text (NEWS) - Yellow text on Black box
        "[with_hook]drawtext=text='NEWS':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=80:x=(w-text_w)/2:y=h-160:box=1:boxcolor=black:boxborderw=20[outv]"
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
    return "Short Video Template (Hollywood Reels Style)"

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
