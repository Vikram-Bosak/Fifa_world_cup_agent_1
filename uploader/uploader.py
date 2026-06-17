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

def get_page_access_token(user_token, page_id):
    """
    Queries /me/accounts to find the Page Access Token for the target Page ID.
    If not found or query fails, returns the user_token back as a fallback.
    """
    url = f"https://graph.facebook.com/v19.0/me/accounts?limit=100&access_token={user_token}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get('data', [])
            for page in data:
                if str(page.get('id')) == str(page_id):
                    print(f"Successfully resolved Page Access Token for page: {page.get('name')} ({page_id})")
                    return page.get('access_token')
            print(f"Target Page ID {page_id} not found in user accounts. Falling back to provided token.")
        else:
            print(f"Failed to query /me/accounts (status {response.status_code}). Falling back to provided token.")
    except Exception as e:
        print(f"Error resolving Page Access Token: {e}. Falling back to provided token.")
    return user_token

def _handle_api_error(response, step_name):
    if response.status_code >= 400:
        try:
            err_data = response.json()
            error_info = err_data.get('error', {})
            err_msg = error_info.get('message')
            if err_msg:
                raise Exception(f"Facebook API Error ({step_name}): {err_msg}")
        except Exception as e:
            if "Facebook API Error" in str(e):
                raise
        response.raise_for_status()

def upload_to_facebook(video_path, description):
    page_id = os.getenv("FB_PAGE_ID")
    user_token = os.getenv("FB_ACCESS_TOKEN")
    
    if not page_id or not user_token:
        raise Exception("Facebook credentials missing in .env")
        
    # Resolve Page Access Token (The Hollywood way)
    access_token = get_page_access_token(user_token, page_id)
        
    file_size = os.path.getsize(video_path)
    
    print("Initializing Facebook Reels upload session...")
    init_url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    init_payload = {"upload_phase": "start", "access_token": access_token, "file_size": file_size}
    
    init_response = requests.post(init_url, data=init_payload)
    _handle_api_error(init_response, "Initialize Upload")
    res = init_response.json()
    
    if 'video_id' not in res or 'upload_url' not in res:
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
        
    upload_response = requests.post(upload_url, headers=headers, data=video_data)
    _handle_api_error(upload_response, "Upload Video Data")
        
    print("Publishing Reel...")
    payload_finish = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": description
    }
    
    finish_response = requests.post(init_url, data=payload_finish)
    _handle_api_error(finish_response, "Publish Video")
    finish_res = finish_response.json()
    
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
        raise FileNotFoundError(f"Video file {video_path} not found.")
        
    if not can_upload():
        print("Daily upload limit (5) reached. Aborting.")
        return
        
    start_time = datetime.now(timezone.utc)
        
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
        
    end_time = datetime.now(timezone.utc)
    duration_secs = (end_time - start_time).total_seconds()
    
    # Send Final Telegram Report
    file_name = os.path.basename(video_path)
    
    # Get GitHub Actions context if available
    github_repo = os.getenv("GITHUB_REPOSITORY", "Vikram-Bosak/Fifa_world_cup_agent_1")
    github_run_id = os.getenv("GITHUB_RUN_ID", "local-run")
    repo_url = f"https://github.com/{github_repo}"
    run_url = f"{repo_url}/actions/runs/{github_run_id}" if github_run_id != "local-run" else "Local execution"
    
    fb_status = "Success" if fb_url != "Failed" else "Failed"
    yt_status = "Success" if yt_url != "Failed" else "Failed"
    
    report_msg = (
        f"✅ Pipeline Run Completed\n\n"
        f"🎬 Video Name:\n"
        f"{title}\n\n"
        f"📤 Facebook Upload Status: {fb_status}\n"
        f"📤 YouTube Upload Status: {yt_status}\n\n"
        f"🏷️ SEO Title:\n"
        f"{title}\n\n"
        f"📝 Description:\n"
        f"{yt_desc}\n\n"
        f"Original File: {file_name}\n\n"
        f"🔗 Facebook Reel URL:\n"
        f"{fb_url}\n\n"
        f"▶️ YouTube Video URL:\n"
        f"{yt_url}\n\n"
        f"📦 GitHub Repository:\n"
        f"{repo_url}\n\n"
        f"📄 Workflow Run:\n"
        f"{run_url}"
    )
    
    send_message(report_msg)
    
    job_status = "Success" if fb_status == "Success" or yt_status == "Success" else "Failed"
    return fb_url, yt_url, job_status, fb_err, yt_err

if __name__ == "__main__":
    # Test Upload with the edited dynamic video
    run_upload_pipeline("temp/dynamic_edit.mp4")
