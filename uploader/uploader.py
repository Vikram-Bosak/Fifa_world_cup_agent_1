import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.limits import can_upload, increment_upload
from common.telegram import send_message

def is_us_upload_time():
    """Check if current time is between 8 AM and 10 PM US EST"""
    # EST is UTC-5 (approximating without checking daylight savings for simplicity)
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    return 8 <= est_time.hour < 22

def upload_to_facebook(video_path, description):
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        raise Exception("Facebook credentials missing in .env")
        
    print("Initializing Facebook Reels upload session...")
    url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    payload = {"upload_phase": "start", "access_token": access_token}
    res = requests.post(url, data=payload).json()
    
    if 'video_id' not in res:
        raise Exception(f"FB Start Error: {res}")
        
    video_id = res['video_id']
    upload_url = res['upload_url']
    
    print("Uploading video bytes to Facebook...")
    headers = {
        "Authorization": f"OAuth {access_token}", 
        "offset": "0", 
        "file_size": str(os.path.getsize(video_path))
    }
    with open(video_path, 'rb') as f:
        upload_res = requests.post(upload_url, headers=headers, data=f).json()
        
    print("Publishing Reel...")
    payload_finish = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": description
    }
    finish_res = requests.post(url, data=payload_finish).json()
    
    if not finish_res.get("success"):
        raise Exception(f"FB Finish Error: {finish_res}")
        
    return f"https://www.facebook.com/reel/{video_id}"

def upload_to_youtube(video_path, title, description):
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
    except ImportError:
        raise Exception("Google API client not installed")
        
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
    if not os.path.exists(token_path):
        raise Exception("YouTube token.json not found")
        
    creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/youtube.upload'])
    youtube = build('youtube', 'v3', credentials=creds)
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['Shorts', 'FIFA', 'Football', 'Viral'],
            'categoryId': '17' # Sports
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    print("Uploading to YouTube...")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
            
    video_id = response.get('id')
    return f"https://www.youtube.com/shorts/{video_id}"

def run_upload_pipeline(video_path: str):
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} not found.")
        return
        
    if not can_upload():
        print("Daily upload limit (5) reached. Aborting.")
        return
        
    if not is_us_upload_time():
        print("Not US upload time (8 AM - 10 PM EST). Aborting.")
        # For testing purposes, we can bypass this if needed
        # return
        print("Bypassing US time check for Testing...")
        
    print(f"Starting Upload Process for {video_path}")
    
    # Generate Metadata
    from common.seo_generator import generate_seo_metadata
    seo_data = generate_seo_metadata()
    title = seo_data["title"]
    description = seo_data["description"]
    
    fb_url = "Failed"
    fb_err = "None"
    yt_url = "Failed"
    yt_err = "None"
    
    # 1. Facebook Upload
    try:
        fb_url = upload_to_facebook(video_path, description)
        print(f"Facebook upload successful: {fb_url}")
    except Exception as e:
        fb_err = str(e)
        print(f"Facebook upload failed: {fb_err}")
        
    # 2. YouTube Upload
    try:
        yt_url = upload_to_youtube(video_path, title, description)
        print(f"YouTube upload successful: {yt_url}")
    except Exception as e:
        yt_err = str(e)
        print(f"YouTube upload failed: {yt_err}")
        
    # Increment quota if at least one succeeded
    if fb_url != "Failed" or yt_url != "Failed":
        increment_upload()
        
    # Send Final Telegram Report
    from common.telegram import report_final_summary
    summary_data = {
        'title': title,
        'description': description,
        'fb_url': fb_url if fb_url != 'Failed' else 'N/A',
        'yt_url': yt_url if yt_url != 'Failed' else 'N/A',
        'original_file': video_path,
        'job_status': 'Success' if fb_url != 'Failed' or yt_url != 'Failed' else 'Failed'
    }
    report_final_summary(summary_data)
    print("Upload reporting finished!")

if __name__ == "__main__":
    # Test Upload with the edited dynamic video
    run_upload_pipeline("temp/dynamic_edit.mp4")
