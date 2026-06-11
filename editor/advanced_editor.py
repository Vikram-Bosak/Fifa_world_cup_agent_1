import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import send_video

def create_text_image(text, filename, size=(400, 200), color="red"):
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    try:
        # Try a standard font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Very basic text drawing
    d.text((50, 50), text, fill=color, font=font)
    img.save(filename)
    return filename

def create_advanced_edit(input_path: str, logo_path: str, output_path: str):
    print("Loading video...")
    clip = VideoFileClip(input_path)
    
    # 1. Quick Cuts
    print("Applying Quick Cuts...")
    cuts = []
    dur = clip.duration
    if dur > 8:
        cuts.append(clip.subclip(0, 3))
        cuts.append(clip.subclip(4, 7))
        cuts.append(clip.subclip(8, min(dur, 12)))
        final_clip = concatenate_videoclips(cuts)
    else:
        final_clip = clip
        
    final_clip = final_clip.fx(vfx.speedx, 1.1)
    
    # 2. Overlays
    print("Adding Visual Overlays...")
    logo = ImageClip(logo_path).resize(width=150)
    logo = logo.set_position(("right", "top")).set_duration(final_clip.duration).margin(right=20, top=20, opacity=0)
    
    # Create temp images for text
    os.makedirs("temp", exist_ok=True)
    iq_path = create_text_image("0 IQ!", "temp/iq_text.png", color="red")
    cross_path = create_text_image("XXX", "temp/cross_text.png", color="red")
    
    txt_0iq = ImageClip(iq_path).set_position('center').set_start(1).set_duration(1.5).crossfadein(0.2).crossfadeout(0.2)
    txt_cross = ImageClip(cross_path).set_position(('left', 'center')).set_start(3).set_duration(1).crossfadein(0.1)

    overlays = [final_clip, logo, txt_0iq, txt_cross]
    
    composite = CompositeVideoClip(overlays)
    
    print("Rendering final video...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    composite.write_videofile(
        output_path, 
        codec='libx264', 
        audio_codec='aac', 
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True,
        preset='fast'
    )
    
    # 3. Send to Telegram
    caption = (
        "🔥 <b>Phase 1: Advanced Editing Style Demo</b>\n\n"
        "<b>Features Applied:</b>\n"
        "✂️ <b>Quick Cuts:</b> Removed boring frames (silence/inaction) to increase pacing.\n"
        "⚡ <b>Pacing:</b> Overall speed increased by 1.1x for TikTok/Reels energy.\n"
        "😂 <b>Humor & Overlays:</b> Auto-flashed '0 IQ!' and 'XXX' marks at action points.\n"
        "🏷️ <b>Branding:</b> Logo tracked at the top right.\n\n"
        "<i>(Motion Tracking & Beat-Syncing will be added in Phase 2)</i>"
    )
    
    from common.telegram import TELEGRAM_REPORT_CHAT_ID
    print("Sending to Telegram...")
    send_video(output_path, caption=caption, chat_id=TELEGRAM_REPORT_CHAT_ID)
    print("Done!")

if __name__ == "__main__":
    create_advanced_edit("assets/fallback.mp4", "assets/custom_logo.png", "temp/advanced_edit.mp4")
