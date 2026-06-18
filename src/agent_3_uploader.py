import os
import requests
import random
import time
from dotenv import load_dotenv

# Ensure we can import existing modules
try:
    from src.facebook_uploader import upload_reel
    from src.youtube_uploader import upload_to_youtube
except ImportError:
    from facebook_uploader import upload_reel
    from youtube_uploader import upload_to_youtube

load_dotenv()

def run_upload(video_data):
    print("Starting Agent 3: Facebook Uploader")
    
    edited_video_path = video_data.get('edited_path')
    title = video_data.get('title', 'Unknown Video')
    headline = video_data.get('seo_title', '')
    source_url = video_data.get('source_url', '')
    
    if not edited_video_path or not os.path.exists(edited_video_path):
        print("No edited video found to upload.")
        return video_data
        
    if video_data.get("editing_status") != "Success":
        print(f"Editing did not succeed (Status: {video_data.get('editing_status')}). Skipping upload.")
        if os.path.exists(edited_video_path):
            os.remove(edited_video_path)
        return video_data
        
    # Construct Facebook Caption dynamically
    try:
        from src.common.seo_generator import generate_upload_metadata
        task_id = video_data.get("id", "default")
        state_file = f"temp/state_upload_{task_id}.json"
        
        if os.path.exists(state_file):
            import json
            with open(state_file, "r") as f:
                context = json.load(f)
        else:
            context = video_data
            
        metadata = generate_upload_metadata(context)
        fb_caption = f"{metadata.get('facebook_caption', headline)}\n\n{metadata.get('hashtags', '#FIFAWorldCup #Football')}\n\nSource: {source_url}"
    except Exception as e:
        print(f"Error generating dynamic SEO metadata: {e}")
        fb_caption = f"{headline}\n\n#FIFAWorldCup #Football #Soccer\n\nSource: {source_url}"
        
    video_data["description"] = fb_caption

    delay_seconds = random.randint(0, 900) # 0 to 15 minutes
    print(f"Waiting for {delay_seconds} seconds ({delay_seconds/60:.1f} minutes) before uploading to appear human...")
    time.sleep(delay_seconds)

    # Facebook Upload
    try:
        print(f"Uploading to Facebook with caption: {fb_caption}")
        fb_url = upload_reel(edited_video_path, fb_caption)
        print(f"Successfully uploaded to Facebook: {fb_url}")
        video_data["fb_url"] = fb_url
    except Exception as e:
        print(f"Failed to upload to Facebook: {e}")
        video_data["fb_err"] = str(e)
        
    # YouTube Upload (runs independently of Facebook)
    try:
        print("Waiting 2 seconds before uploading to YouTube Shorts...")
        time.sleep(2)
        
        yt_title = title[:100] # YouTube title limit is 100 chars
        yt_desc = f"{fb_caption}\n#shorts"
        
        yt_url = upload_to_youtube(edited_video_path, yt_title, yt_desc)
        video_data["yt_url"] = yt_url
    except Exception as e:
        print(f"Failed to upload to YouTube: {e}")
        video_data["yt_err"] = str(e)
        
    # Set overall status based on whether at least one upload succeeded
    if video_data.get("fb_url") or video_data.get("yt_url"):
        video_data["upload_status"] = "Success"
    else:
        video_data["upload_status"] = "Failed"
        
    # Cleanup
    if os.path.exists(edited_video_path):
        os.remove(edited_video_path)
        
    return video_data

if __name__ == "__main__":
    pass
