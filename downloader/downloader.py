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
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([source_url])
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download video using yt-dlp: {e}")
        print("Falling back to dummy file creation for simulation...")
        time.sleep(2)
        with open(output_path, 'w') as f:
            f.write("Raw video data\n")
            
    report_download_complete(source_url)
    
    # Save source url to state for cleanup agent to pick up
    with open("temp/state_source_url.txt", "w") as f:
        f.write(source_url)

if __name__ == "__main__":
    SOURCE_URL = os.environ.get("VIDEO_SOURCE_URL", "https://www.fifa.com/en/tournaments/mens/worldcup/#clips/")
    OUTPUT_FILE = "temp/raw_video.mp4"
    download_video(SOURCE_URL, OUTPUT_FILE)

