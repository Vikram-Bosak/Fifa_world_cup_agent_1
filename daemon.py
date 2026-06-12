import os
import sys
import time
import subprocess
from datetime import datetime

def run_daemon():
    print("Starting 24x7 FIFA World Cup Automation Daemon...")
    while True:
        start_time = datetime.now()
        print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Waking up and starting main_agent.py...")
        
        try:
            # Run the main agent using the current python environment
            subprocess.run([sys.executable, "main_agent.py"], check=False)
        except Exception as e:
            print(f"Error running agent: {e}")
            
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent run completed.")
        
        # Sleep for 2 hours (7200 seconds)
        print("Sleeping for 2 hours before the next run...")
        time.sleep(7200)

if __name__ == "__main__":
    run_daemon()
