import os
import sys
import json
import shutil
import time
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path so we can import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.telegram import report_final_summary

def cleanup_and_report():
    print("Starting cleanup and final reporting...")
    
    summary_data = {}
    
    # Read source url
    try:
        with open("temp/state_source_url.txt", "r") as f:
            summary_data["source_url"] = f.read().strip()
    except FileNotFoundError:
        pass
        
    # Read upload details
    try:
        with open("temp/state_upload.json", "r") as f:
            upload_data = json.load(f)
            summary_data.update(upload_data)
    except FileNotFoundError:
        pass
        
    # Job status can be passed via env var
    summary_data["job_status"] = os.environ.get("JOB_STATUS", "Success")
    summary_data["execution_time"] = os.environ.get("EXECUTION_TIME_SECONDS", "N/A")
    
    # Send final summary
    report_final_summary(summary_data)
    
    # Perform strict cleanup
    temp_dir = "temp"
    if os.path.exists(temp_dir):
        print(f"Cleaning up {temp_dir} directory...")
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                print(f"Deleted: {item_path}")
            except Exception as e:
                print(f"Failed to delete {item_path}. Reason: {e}")
    
    print("Cleanup finished successfully.")

if __name__ == "__main__":
    cleanup_and_report()
