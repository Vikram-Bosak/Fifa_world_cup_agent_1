import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path so we can import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import report_upload_complete

def upload_video(input_path: str):
    if not os.path.exists(input_path):
        print(f"Error: Edited video file {input_path} not found.")
        sys.exit(1)
        
    print(f"Uploading video {input_path}...")
    
    from common.seo_generator import generate_seo_metadata
    seo_data = generate_seo_metadata()
    title = seo_data["title"]
    description = seo_data["description"]
    tags = seo_data["tags"]
    
    # Facebook Upload using Graph API
    print("Uploading to Facebook Reels...")
    fb_url = "N/A"
    
    print("UPLOADS DISABLED FOR TESTING. Skipping Facebook upload.")
    time.sleep(1)
    
    report_upload_complete("Facebook (Disabled)", fb_url, title, description)
    
    # YouTube Upload using Google API
    print("Uploading to YouTube Shorts...")
    yt_url = "N/A"
    
    print("UPLOADS DISABLED FOR TESTING. Skipping YouTube upload.")
    time.sleep(1)
        
    report_upload_complete("YouTube (Disabled)", yt_url, title, description)
    
    # Save upload details for cleanup agent summary
    upload_state = {
        "fb_url": fb_url,
        "yt_url": yt_url,
        "title": title,
        "description": description
    }
    with open("temp/state_upload.json", "w") as f:
        json.dump(upload_state, f)
        
    print("Uploads complete.")

if __name__ == "__main__":
    INPUT_FILE = "temp/edited_video.mp4"
    upload_video(INPUT_FILE)
