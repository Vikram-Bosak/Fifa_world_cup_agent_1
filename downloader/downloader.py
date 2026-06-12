import os
import sys
import time
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path so we can import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import report_download_start, report_download_complete

def download_video(source_url: str, output_path: str):
    report_download_start()
    
    print(f"Downloading video from {source_url} to {output_path}...")
    
    # Ensure temp directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        from x_scraper import download_x_video
        
        print(f"Targeting Twitter profile: {source_url}")
        
        success = download_x_video(source_url, output_path)
        
        if not success:
            print("Twitter scraper failed. Falling back to a LOCAL football video...")
            fallback_path = "assets/fallback.mp4"
            if os.path.exists(fallback_path):
                import shutil
                shutil.copy(fallback_path, output_path)
                print("Copied local fallback MP4 successfully.")
            else:
                print("Local fallback not found.")
                
    except Exception as e:
        print(f"Failed to run Twitter scraper: {e}")
        
    report_download_complete(source_url)
    
    # Save source url to state for cleanup agent to pick up
    with open("temp/state_source_url.txt", "w") as f:
        f.write(source_url)

import random

def get_random_query():
    queries = [
        'ytsearch1:"FIFA world cup best goals short"',
        'ytsearch1:"Messi world cup highlights short"',
        'ytsearch1:"Ronaldo world cup skills short"',
        'ytsearch1:"Neymar world cup goals short"',
        'ytsearch1:"Mbappe world cup speed short"',
        'ytsearch1:"FIFA world cup crazy moments short"',
        'ytsearch1:"World cup funny moments short"'
    ]
    return random.choice(queries)

if __name__ == "__main__":
    SOURCE_URL = os.environ.get("VIDEO_SOURCE_URL", "https://x.com/FIFAWorldCup")
    if SOURCE_URL == "RANDOM_YOUTUBE_SEARCH":
        SOURCE_URL = get_random_query()
        
    OUTPUT_FILE = "temp/raw_video.mp4"
    download_video(SOURCE_URL, OUTPUT_FILE)

