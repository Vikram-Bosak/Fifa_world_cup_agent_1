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

def edit_long_video_template(input_path: str, logo_path: str, output_path: str, hook_line: str = "CRAZIEST FIFA MOMENT!", overlay_text: str = "", source_credit: str = ""):
    print("Applying Long Video (Horizontal) Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Escape single quotes in the hook line for FFmpeg
    safe_hook = hook_line.replace("'", "\\'")
    safe_overlay = overlay_text.replace("'", "\\'") if overlay_text else ""
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=min(h\\,w)/20:luma_power=1:chroma_radius=min(cw\\,ch)/20:chroma_power=1,colorchannelmixer=rr=0.7:gg=0.7:bb=0.7[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[1:v]scale=200:-1[logo];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        "[merged][logo]overlay=W-w-30:30[with_logo];"
        f"[with_logo]drawtext=text='{safe_hook}':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=200:bordercolor=black:borderw=5:box=1:boxcolor=red@0.8:boxborderw=20[with_hook]"
    )
    
    if safe_overlay:
        filter_complex += f";[with_hook]drawtext=text='{safe_overlay}':fontcolor=yellow:fontsize=60:x=(w-text_w)/2:y=h-250:box=1:boxcolor=black@0.8:boxborderw=15[with_overlay]"
    else:
        filter_complex = filter_complex.replace("[with_hook]", "[with_overlay]")
    
    if source_credit:
        safe_credit = source_credit.replace("'", "\\'")
        filter_complex += f";[with_overlay]drawtext=text='Credit\\: {safe_credit}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=40:x=20:y=h-text_h-20:box=1:boxcolor=black@0.6:boxborderw=10[outv]"
    else:
        filter_complex = filter_complex.replace("[with_overlay]", "[outv]")
    
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

def edit_short_video_template(input_path: str, logo_path: str, output_path: str, hook_line: str = "EPIC FIFA MOMENT", overlay_text: str = "MUST WATCH", source_credit: str = ""):
    print("Applying Short Video (Vertical) Hollywood Style Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Escape single quotes in the hook line for FFmpeg
    safe_hook = hook_line.replace("'", "\\'")
    safe_overlay = overlay_text.replace("'", "\\'")
    
    filter_complex = (
        # Scale, crop, color grading (vibrant), focus effect (unsharp), and edge focus (vignette)
        "[0:v]scale=1040:1880:force_original_aspect_ratio=increase,crop=1040:1880,eq=contrast=1.15:brightness=0.03:saturation=1.3,unsharp=5:5:1.0,vignette=PI/4[scaled];"
        # Pad with yellow border to make it 1080x1920
        "[scaled]pad=1080:1920:20:20:yellow[padded];"
        # Logo at top center
        "[1:v]scale=150:-1[logo];"
        "[padded][logo]overlay=(W-w)/2:40[with_logo];"
        # Branding Text (Top Center, below logo)
        "[with_logo]drawtext=text='FIFA WORLD CUP':fontcolor=white:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=50:x=(w-text_w)/2:y=200[with_brand];"
        # Catchy Headline (Top Center, below branding) - Yellow text on Black box
        f"[with_brand]drawtext=text='{safe_hook}':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=65:x=(w-text_w)/2:y=280:box=1:boxcolor=black:boxborderw=15[with_hook];"
        # Bottom Text (Dynamic Overlay) - Yellow text on Black box
        f"[with_hook]drawtext=text='{safe_overlay}':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=70:x=(w-text_w)/2:y=h-160:box=1:boxcolor=black:boxborderw=20[with_overlay]"
    )
    
    if source_credit:
        safe_credit = source_credit.replace("'", "\\'")
        filter_complex += f";[with_overlay]drawtext=text='Credit\\: {safe_credit}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=35:x=w-text_w-30:y=h-text_h-30:box=1:boxcolor=black@0.6:boxborderw=10[outv]"
    else:
        filter_complex = filter_complex.replace("[with_overlay]", "[outv]")
    
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

def process_video_dynamically(input_path: str, logo_path: str, output_path: str, task: dict = None):
    from common.seo_generator import analyze_video_for_editing
    
    task = task or {}
    print(f"Analyzing {input_path}...")
    width, height = get_video_dimensions(input_path)
    print(f"Detected Dimensions: {width}x{height}")
    
    # Stage 1: AI Contextual Analysis
    print("Generating Context-Aware AI Editing Instructions...")
    analysis = analyze_video_for_editing(task)
    print(f"Analysis Output: {json.dumps(analysis)}")
    
    hook_line = analysis.get("hook_line", "EPIC FIFA MOMENT")
    overlay_text = analysis.get("overlay_text", "MUST WATCH")
    source_credit = task.get("source", "")
    
    # Save full analysis state for Uploader Phase
    os.makedirs("temp", exist_ok=True)
    task_id = task.get("id", "default")
    with open(f"temp/state_upload_{task_id}.json", "w") as f:
        # Merge task data and analysis
        full_context = dict(task)
        full_context.update(analysis)
        json.dump(full_context, f, indent=4)
        
    if width > height:
        template_used = edit_long_video_template(input_path, logo_path, output_path, hook_line, overlay_text, source_credit)
    else:
        template_used = edit_short_video_template(input_path, logo_path, output_path, hook_line, overlay_text, source_credit)
        
    print("Video editing completed!")
    
    caption = f"💾 STORAGE: Edited Video for {task_id}"
    
    from common.telegram import send_video
    print("Sending to Telegram for cloud storage...")
    msg_id, file_id = send_video(output_path, caption=caption)
    
    print("Keeping local edited file for sequential processing...")
    
    print("Process finished!")
    return file_id, hook_line

if __name__ == "__main__":
    # Test on the horizontal video
    dummy_task = {"id": "test_123", "title": "Crazy test video", "source": "FIFA World Cup"}
    process_video_dynamically("assets/vertical_dummy.mp4", "assets/custom_logo.png", "temp/dynamic_edit.mp4", dummy_task)
