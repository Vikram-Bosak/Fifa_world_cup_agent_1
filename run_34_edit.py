import subprocess
from common.telegram import send_message, send_video

post_id = "2065664111413731817"
input_path = f"temp/{post_id}.mp4"
logo_path = "assets/custom_logo.png"
bgm_path = "assets/music/default_background_music.mp3"
temp_output = f"temp/edited_34_{post_id}.mp4"

from common.seo_generator import analyze_video_for_editing

task = {
    "id": post_id,
    "title": "Five World Cups. Five unforgettable goals. Which one is y...",
    "source": "FIFA World Cup"
}

analysis = analyze_video_for_editing(task)
hook_line = analysis.get("hook_line", "Did you notice this historic moment?")
source_credit = "FIFA World Cup"

send_message(f"🎬 **Editing Video in 3:4 Ratio (1080x1440)...**\nPOST ID: {post_id}")

duration = None
try:
    duration_str = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
    ).decode().strip()
    if duration_str: duration = float(duration_str)
except:
    duration = 87.34

safe_hook = hook_line.replace("'", "\\'")

safe_credit = source_credit.replace("'", "\\'").replace(":", "\\:")

# 3:4 Filter Complex: 1080x1440
filter_complex = (
    f"[0:v]hflip,setpts=PTS/1.05,scale=1188:1584:force_original_aspect_ratio=increase,crop=1080:1440,colorbalance=rs=0.2:gs=0.2:rm=0.2:gm=0.2,eq=contrast=1.2:brightness=0.05:saturation=1.6:gamma=1.05,unsharp=5:5:1.0,vignette=PI/4[scaled];"
    f"[1:v]scale=150:-1[logo];"
    f"[scaled][logo]overlay=(W-w)/2:40[with_logo];"
    f"[with_logo]drawtext=text='{safe_hook}':fontcolor=yellow:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=60:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black:boxborderw=20[with_hook];"
    f"[with_hook]drawtext=text='Credit\\: {safe_credit}':fontcolor=white@0.8:fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontsize=35:x=w-text_w-30:y=30:box=1:boxcolor=black@0.6:boxborderw=10[outv_temp];"
    f"[outv_temp]drawbox=x=0:y=0:w=iw:h=ih:color=yellow:thickness=20[outv];"
    f"[0:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.2[a0];[2:a]asetrate=53878,aresample=48000,atempo=0.9354,volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first:normalize=0[outa]"
)

cmd = [
    "ffmpeg", "-y", "-i", input_path, "-i", logo_path,
    "-stream_loop", "-1", "-i", bgm_path,
    "-filter_complex", filter_complex,
    "-map", "[outv]", "-map", "[outa]"
]

if duration:
    cmd.extend(["-t", str(duration)])
else:
    cmd.extend(["-shortest"])

# Use CRF 28 to ensure <50MB size for Telegram
cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "28", "-c:a", "aac", "-b:a", "128k", "-t", "59", temp_output])

try:
    subprocess.run(cmd, check=True)
    send_message("✅ **3:4 Edit Successful! Sending video...**")
    send_video(temp_output, caption=f"Here is your video edited in 3:4 Aspect Ratio (1080x1440)!\nPOST ID: {post_id}")
    print("Done!")
except Exception as e:
    send_message(f"❌ Failed to edit 3:4 video: {e}")
    print(e)
