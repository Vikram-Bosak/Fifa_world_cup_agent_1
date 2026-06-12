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
    """Check if current time is within US EST peak social media hours"""
    # EST is UTC-5 (approximating without checking daylight savings for simplicity)
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    
    hour = est_time.hour
    # Peak US hours: 8-10 AM (Morning), 12-2 PM (Lunch), 5-8 PM (Evening)
    is_peak = (8 <= hour < 10) or (12 <= hour < 14) or (17 <= hour < 20)
    return is_peak

def upload_to_facebook(video_path, description):
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        raise Exception("Facebook credentials missing in .env")
        
    file_size = os.path.getsize(video_path)
    
    print("Initializing Facebook Reels upload session...")
    url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    payload = {"upload_phase": "start", "access_token": access_token, "file_size": file_size}
    try:
        res_raw = requests.post(url, data=payload)
        res_raw.raise_for_status()
        res = res_raw.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"FB Start HTTP Error: {e.response.text if e.response else str(e)}")
    except Exception as e:
        raise Exception(f"FB Start Request Error: {e}")
    
    if 'video_id' not in res:
        raise Exception(f"FB Start Logic Error: {res}")
        
    video_id = res['video_id']
    upload_url = res['upload_url']
    
    print("Uploading video bytes to Facebook...")
    headers = {
        "Authorization": f"OAuth {access_token}", 
        "offset": "0", 
        "file_size": str(file_size)
    }
    with open(video_path, 'rb') as f:
        video_data = f.read()
        try:
            upload_res_raw = requests.post(upload_url, headers=headers, data=video_data)
            upload_res_raw.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(f"FB Upload HTTP Error: {e.response.text if e.response else str(e)}")
        except Exception as e:
            raise Exception(f"FB Upload Request Error: {e}")
        
    print("Publishing Reel...")
    payload_finish = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "video_state": "PUBLISHED",
    try:
        finish_res_raw = requests.post(url, data=payload_finish)
        finish_res_raw.raise_for_status()
        finish_res = finish_res_raw.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"FB Finish HTTP Error: {e.response.text if e.response else str(e)}")
    except Exception as e:
        raise Exception(f"FB Finish Request Error: {e}")
    
    if not finish_res.get("success"):
        raise Exception(f"FB Finish Logic Error: {finish_res}")
        
    return f"https://www.facebook.com/reel/{video_id}"

def upload_to_youtube(video_path, title, description):
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
    except ImportError:
        raise Exception("Google API client not installed")
        
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
    
    # If running in GitHub Actions, create token.json from env var
    youtube_token_env = os.getenv("YOUTUBE_TOKEN_JSON")
    if youtube_token_env:
        with open(token_path, "w") as f:
            f.write(youtube_token_env)
            
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

def run_upload_pipeline(video_path: str, task_id: str = "default"):
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
    
    # Load full AI context state file if available
    original_file = video_path
    state_file = f"temp/state_upload_{task_id}.json"
    state_data = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state_data = json.load(f)
                original_file = state_data.get("source_url", video_path)
        except:
            pass
            
    # Generate Metadata via Context-Aware AI LLM Stage 2
    from common.seo_generator import generate_upload_metadata
    seo_data = generate_upload_metadata(state_data)
    title = seo_data["title"]
    base_description = seo_data["description"]
    facebook_caption = seo_data.get("facebook_caption", base_description)
    hashtags = seo_data.get("hashtags", "")
    
    fb_desc = f"{facebook_caption}\n\n{hashtags}"
    yt_desc = f"{base_description}\n\n{hashtags}"
    
    fb_url = "Failed"
    fb_err = "None"
    yt_url = "Failed"
    yt_err = "None"
    
    # 1. Facebook Upload
    try:
        fb_url = upload_to_facebook(video_path, fb_desc)
        print(f"Facebook upload successful: {fb_url}")
    except Exception as e:
        fb_err = str(e)
        print(f"Facebook upload failed: {fb_err}")
        
    # 2. YouTube Upload
    try:
        yt_url = upload_to_youtube(video_path, title, yt_desc)
        print(f"YouTube upload successful: {yt_url}")
    except Exception as e:
        yt_err = str(e)
        print(f"YouTube upload failed: {yt_err}")
        if "invalid_grant" in yt_err or "RefreshError" in yt_err or "expired" in yt_err.lower():
            print("Hint: YouTube token.json is likely expired. Please re-authenticate locally and update token.json.")
        
    # Increment quota if at least one succeeded
    if fb_url != "Failed" or yt_url != "Failed":
        increment_upload()
        
    job_status = 'SUCCESS' if (fb_url != 'Failed' or yt_url != 'Failed') else 'FAILED'
    return fb_url, yt_url, job_status, fb_err, yt_err

if __name__ == "__main__":
    # Test Upload with the edited dynamic video
    run_upload_pipeline("temp/dynamic_edit.mp4")
