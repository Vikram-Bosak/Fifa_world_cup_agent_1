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

def edit_long_video_template(input_path: str, logo_path: str, output_path: str, hook_line: str = "CRAZIEST FIFA MOMENT!", overlay_text: str = "", source_credit: str = "", bgm_path: str = None):
    print("Applying Long Video (Horizontal) Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Escape single quotes in the hook line for FFmpeg
    safe_hook = hook_line.replace("'", "\\'")
    safe_overlay = overlay_text.replace("'", "\\'") if overlay_text else ""
    
    filter_complex = (
        "[0:v]hflip,setpts=PTS/1.05,scale=1188:1584:force_original_aspect_ratio=increase,crop=1080:1440,boxblur=luma_radius=min(h\\,w)/20:luma_power=1:chroma_radius=min(cw\\,ch)/20:chroma_power=1,colorchannelmixer=rr=0.7:gg=0.7:bb=0.7[bg];"
        "[0:v]hflip,setpts=PTS/1.05,scale=1188:1584:force_original_aspect_ratio=decrease[fg_zoomed];"
        "[fg_zoomed]crop=min(iw\\,1080):min(ih\\,1440)[fg];"
        "[1:v]scale=200:-1[logo];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        "[merged][logo]overlay=W-w-30:30[with_logo];"
        f"[with_logo]drawtext=text='{safe_hook}':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=70:x=(w-text_w)/2:y=h-250:box=1:boxcolor=black@0.8:boxborderw=15[with_hook]"
    )
    
    if source_credit:
        safe_credit = source_credit.replace("'", "\\'").replace(":", "\\:")
        filter_complex += f";[with_hook]drawtext=text='Credit\\: {safe_credit}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=40:x=w-text_w-20:y=20:box=1:boxcolor=black@0.6:boxborderw=10[outv_temp]"
    else:
        filter_complex = filter_complex.replace("[with_hook]", "[outv_temp]")
        
    filter_complex += ";[outv_temp]drawbox=x=0:y=0:w=iw:h=ih:color=yellow:thickness=20[outv]"
    
    has_audio = False
    try:
        out = subprocess.check_output(["ffprobe", "-i", input_path, "-show_streams", "-select_streams", "a", "-loglevel", "error"]).decode()
        if out.strip(): has_audio = True
    except: pass


    duration = None
    try:
        duration_str = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
        ).decode().strip()
        if duration_str: duration = float(duration_str)
    except:
        pass

    cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_path]

    
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        if has_audio:
            filter_complex += ";[0:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.2[a0];[2:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first:normalize=0[outa]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]"])
        else:
            filter_complex += ";[2:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.8[outa]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]", "-shortest"])
    else:
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]"])
        if has_audio:
            cmd.extend(["-map", "0:a"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "59",
        output_path
    ])
    subprocess.run(cmd, check=True)
    return "Long Video Template (News Style)"

def edit_short_video_template(input_path: str, logo_path: str, output_path: str, hook_line: str = "EPIC FIFA MOMENT", overlay_text: str = "MUST WATCH", source_credit: str = "", bgm_path: str = None):
    print("Applying Short Video (Vertical 3:4) Hollywood Style Template...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Escape single quotes in the hook line for FFmpeg
    safe_hook = hook_line.replace("'", "\\'")
    safe_overlay = overlay_text.replace("'", "\\'")
    
    filter_complex = (
        # Scale, crop, color grading (vibrant), focus effect (unsharp), and edge focus (vignette)
        "[0:v]hflip,setpts=PTS/1.05,scale=1188:1584:force_original_aspect_ratio=increase,crop=1080:1440,colorbalance=rs=0.2:gs=0.2:rm=0.2:gm=0.2,eq=contrast=1.2:brightness=0.05:saturation=1.6:gamma=1.05,unsharp=5:5:1.0,vignette=PI/4[scaled];"
        # Logo at top center
        "[1:v]scale=150:-1[logo];"
        "[scaled][logo]overlay=(W-w)/2:40[with_logo];"
        # Catchy Hindi Hook Line (Bottom Center)
        f"[with_logo]drawtext=text='{safe_hook}':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=60:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black:boxborderw=20[with_hook]"
    )
    
    if source_credit:
        safe_credit = source_credit.replace("'", "\\'").replace(":", "\\:")
        filter_complex += f";[with_hook]drawtext=text='Credit\\: {safe_credit}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=35:x=w-text_w-30:y=30:box=1:boxcolor=black@0.6:boxborderw=10[outv_temp]"
    else:
        filter_complex = filter_complex.replace("[with_hook]", "[outv_temp]")
        
    filter_complex += ";[outv_temp]drawbox=x=0:y=0:w=iw:h=ih:color=yellow:thickness=20[outv]"
    
    has_audio = False
    try:
        out = subprocess.check_output(["ffprobe", "-i", input_path, "-show_streams", "-select_streams", "a", "-loglevel", "error"]).decode()
        if out.strip(): has_audio = True
    except: pass


    duration = None
    try:
        duration_str = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
        ).decode().strip()
        if duration_str: duration = float(duration_str)
    except:
        pass

    cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_path]

    
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        if has_audio:
            filter_complex += ";[0:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.2[a0];[2:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first:normalize=0[outa]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]"])
        else:
            filter_complex += ";[2:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.8[outa]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]", "-shortest"])
    else:
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]"])
        if has_audio:
            cmd.extend(["-map", "0:a"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "59",
        output_path
    ])
    subprocess.run(cmd, check=True)
    return "Short Video Template (Hollywood Reels Style)"

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
        
    bgm_file = "assets/music/default_background_music.mp3"
    if width > height:
        template_used = edit_long_video_template(input_path, logo_path, output_path, hook_line, overlay_text, source_credit, bgm_path=bgm_file)
    else:
        template_used = edit_short_video_template(input_path, logo_path, output_path, hook_line, overlay_text, source_credit, bgm_path=bgm_file)
        
    print("Video editing completed!")
    
    edit_complete_time = datetime.datetime.utcnow()
    file_name = os.path.basename(output_path)
    template_name = "Long Horizontal" if width > height else "3:4 Short Vertical"
    
    message_text = (
        f"🎬 **EDITING REPORT**\n\n"
        f"**Workflow Name:** FIFA Auto Pipeline\n"
        f"**Edit Start Time:** {edit_start_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Edit Complete Time:** {edit_complete_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**File Name:** {file_name}\n"
        f"**Applied Template:** {template_name}\n"
        f"**Editing Status:** SUCCESS"
    )
    
    from common.telegram import send_message
    print("Sending Editing Status Report to Telegram...")
    send_message(message_text)
    
    print("Process finished. Returning local path for sequential processing.")
    
    return output_path, hook_line

if __name__ == "__main__":
    # Test on the horizontal video
    dummy_task = {"id": "test_123", "title": "Crazy test video", "source": "FIFA World Cup"}
    process_video_dynamically("assets/vertical_dummy.mp4", "assets/custom_logo.png", "temp/dynamic_edit.mp4", dummy_task)
