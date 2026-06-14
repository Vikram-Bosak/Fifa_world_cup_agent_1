import os
import sys
import subprocess
import json
import textwrap
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

def edit_3_4_custom_layout_template(input_path: str, logo_path: str, output_path: str, hook_line: str = "VIRAL NEWS!", source_credit: str = ""):
    print("Applying Custom 3:4 Layout Template (Border & Black Box)...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 1080x1440 Canvas. Video takes top 1080x1050, leaving a 390px black box at the bottom.
    # We apply the original zoom, flip, speed, and color grading effects.
    filter_complex = (
        "color=c=#FFD700:s=1080x1440[bg];"
        "[0:v]hflip,setpts=PTS/1.05,scale=1080:1050:force_original_aspect_ratio=increase,crop=1080:1050,eq=contrast=1.05:brightness=0.02:saturation=1.15:gamma=1.0,unsharp=5:5:0.5[vid_processed];"
        "[bg][vid_processed]overlay=0:0[with_vid];"
        "[1:v]scale=150:-1[logo];"
        "[with_vid][logo]overlay=(W-w)/2:40[with_logo]"
    )
    
    from common.text_renderer import create_text_overlay
    overlay_path = "temp/hook_overlay.png"
    create_text_overlay(hook_line, overlay_path, max_width=1000, max_height=340)
    
    filter_complex += f";[2:v]scale=1000:340[hook_img];"
    filter_complex += f"[with_logo][hook_img]overlay=40:1075[with_hook]"
    
    if source_credit:
        credit_file = "temp/credit_line.txt"
        with open(credit_file, "w", encoding="utf-8") as f:
            f.write(f"Credit: {source_credit}")
        filter_complex += f";[with_hook]drawtext=textfile='{credit_file}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=35:x=w-text_w-30:y=1000:box=1:boxcolor=black@0.6:boxborderw=10[outv_temp]"
    else:
        filter_complex += ";[with_hook]copy[outv_temp]"
        
    # Apply reference image border: Thick yellow outer, thin black middle, thin yellow inner
    filter_complex += (
        ";[outv_temp]drawbox=x=0:y=0:w=1080:h=1440:color=yellow:thickness=5[border1];"
        "[border1]drawbox=x=5:y=5:w=1070:h=1430:color=black:thickness=4[border2];"
        "[border2]drawbox=x=9:y=9:w=1062:h=1422:color=yellow:thickness=3[outv]"
    )
    
    has_audio = False
    try:
        out = subprocess.check_output(["ffprobe", "-i", input_path, "-show_streams", "-select_streams", "a", "-loglevel", "error"]).decode()
        if out.strip(): has_audio = True
    except: pass

    cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_path, "-i", overlay_path]

    # Audio volume boost logic (no BGM)
    if has_audio:
        filter_complex += ";[0:a]volume=1.5,loudnorm=I=-16:TP=-1.5:LRA=11[outa]"
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]"])
    else:
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "59",
        output_path
    ])
    subprocess.run(cmd, check=True)
    return "3:4 Custom Layout Template"

def process_video_dynamically(input_path: str, logo_path: str, output_path: str, task: dict = None):
    from common.seo_generator import analyze_video_for_editing
    
    task = task or {}
    print(f"Analyzing {input_path}...")
    width, height = get_video_dimensions(input_path)
    print(f"Detected Dimensions: {width}x{height}")
    
    # Stage 1: AI Contextual Analysis
    import datetime
    edit_start_time = datetime.datetime.utcnow()
    
    print("Requesting metadata from Context-Aware LLM Stage 1...")
    analysis = analyze_video_for_editing(task)
    print(f"Analysis Output: {json.dumps(analysis)}")
    
    hook_line = analysis.get("hook_line", "VIRAL NEWS!")
    source_credit = task.get("source", "")
    
    # Save full analysis state for Uploader Phase
    os.makedirs("temp", exist_ok=True)
    task_id = task.get("id", "default")
    with open(f"temp/state_upload_{task_id}.json", "w") as f:
        full_context = dict(task)
        full_context.update(analysis)
        json.dump(full_context, f, indent=4)
        
    template_used = edit_3_4_custom_layout_template(input_path, logo_path, output_path, hook_line, source_credit)
        
    print("Video editing completed!")
    
    edit_complete_time = datetime.datetime.utcnow()
    file_name = os.path.basename(output_path)
    
    message_text = (
        f"🎬 **EDITING REPORT**\n\n"
        f"**Workflow Name:** FIFA Auto Pipeline\n"
        f"**Edit Start Time:** {edit_start_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Edit Complete Time:** {edit_complete_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**File Name:** {file_name}\n"
        f"**Applied Template:** {template_used}\n"
        f"**Editing Status:** SUCCESS"
    )
    
    from common.telegram import send_message
    print("Sending Editing Status Report to Telegram...")
    send_message(message_text)
    
    print("Process finished. Returning local path for sequential processing.")
    
    return output_path, hook_line

if __name__ == "__main__":
    dummy_task = {"id": "test_123", "title": "Crazy test video", "source": "FIFA World Cup"}
    process_video_dynamically("assets/vertical_dummy.mp4", "assets/custom_logo.png", "temp/dynamic_edit.mp4", dummy_task)
