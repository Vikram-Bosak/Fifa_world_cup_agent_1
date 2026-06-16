import os
import sys
import time
import subprocess
from datetime import datetime

def run_daemon():
    print("Starting 24x7 FIFA World Cup Production Daemon...")
    while True:
        start_time = datetime.now()
        print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Waking up and starting pipeline...")
        
        try:
            # Step 1: Run the Scanner to populate the queue
            print(">>> RUNNING SCANNER AGENT <<<")
            subprocess.run([sys.executable, "scanner_agent.py"], check=False)
            
            # Small delay to let queue sync
            time.sleep(5)
            
            # Step 2: Run the Main Agent to process the queue (runs once and exits)
            print(">>> RUNNING MAIN AGENT (Download -> Edit -> Upload) <<<")
            subprocess.run([sys.executable, "main_agent.py"], check=False)
        except Exception as e:
            print(f"Error running pipeline: {e}")
            
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline run completed.")
        
        # Sleep for 1 hour (3600 seconds)
        print("Sleeping for 1 hour before the next run...")
        time.sleep(3600)

if __name__ == "__main__":
    run_daemon()
