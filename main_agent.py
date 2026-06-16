import os
import sys
import time
import shutil
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader.standalone_downloader import run_downloader
from editor_agent import run_editor_agent
from uploader_agent import run_uploader_agent
from common.limits import can_download, can_edit, can_upload

def is_us_peak_time():
    utc_now = datetime.now(timezone.utc)
    est_time = utc_now - timedelta(hours=5)
    hour = est_time.hour
    return (8 <= hour < 10) or (12 <= hour < 14) or (17 <= hour < 20)

def cleanup_temp():
    try:
        shutil.rmtree("temp")
        os.makedirs("temp", exist_ok=True)
    except Exception as e:
        print(f"Cleanup error: {e}")

def run_decoupled_pipeline():
    print("\n--- STARTING DECOUPLED PIPELINE ---")
    
    # 1. Run Downloader if limit not reached
    if can_download():
        print("Checking Download Queue...")
        run_downloader()
    else:
        print("Daily Download Limit Reached.")
        
    # 2. Run Editor if limit not reached
    if can_edit():
        print("Checking Edit Queue...")
        run_editor_agent()
    else:
        print("Daily Edit Limit Reached.")
        
    # 3. Run Uploader if limit not reached
    if can_upload():
        print("Checking Upload Queue...")
        run_uploader_agent()
    else:
        print("Daily Upload Limit Reached.")
        
    print("Pipeline run completed.")

def run_continuous_mode():
    print("Starting Pipeline in Continuous Production Mode...")
    while True:
        run_decoupled_pipeline()
            
        print("Sleeping for 10 minutes before next check...")
        time.sleep(600)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    
    if "--test" in sys.argv:
        print("Running in TEST MODE. Bypassing US peak time check...")
        run_decoupled_pipeline()
    elif "--production" in sys.argv:
        run_continuous_mode()
    else:
        # Default action mode
        run_decoupled_pipeline()
