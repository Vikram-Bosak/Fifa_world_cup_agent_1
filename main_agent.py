import os
import sys

from downloader.standalone_downloader import run_downloader
from editor_agent import run_editor_agent
from uploader_agent import run_uploader_agent
from common.telegram import report_final_summary

def run_single_sequence():
    print("\n--- STARTING SEQUENTIAL PIPELINE (SINGLE RUN) ---")
    
    # 1. Download
    video_data = run_downloader()
    if not video_data:
        print("Pipeline stopped: No video downloaded.")
        return False
        
    task_id = video_data.get('id')
    print(f"Downloaded Video: {task_id}")
    
    # 2. Edit
    video_data = run_editor_agent(video_data)
    if not video_data or video_data.get("status") == "failed":
        print(f"Pipeline stopped: Editing failed for {task_id}")
        return False
        
    # 3. Upload
    video_data = run_uploader_agent(video_data)
    
    # Final Report
    report_final_summary(video_data)
    
    print("Pipeline run completed.")
    return True

if __name__ == "__main__":
    run_single_sequence()
