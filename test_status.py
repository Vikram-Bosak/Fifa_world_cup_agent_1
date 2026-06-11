import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common.telegram import send_video, edit_message_caption

output_path = "assets/fallback.mp4"
tweet_id = "TEST_001"

print("1. Sending DOWNLOADED status...")
message_id = send_video(output_path, caption=f"STATUS: 🔴 DOWNLOADED | ID: {tweet_id}")

if message_id:
    print(f"Got message_id: {message_id}. Waiting 5 seconds...")
    time.sleep(5)
    
    print("2. Editing to EDITING status...")
    edit_message_caption(message_id, f"STATUS: 🟡 EDITING | ID: {tweet_id}")
    
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    print("3. Editing to EDITED status...")
    edit_message_caption(message_id, f"STATUS: 🟢 EDITED | ID: {tweet_id}")
    print("Test Complete!")
else:
    print("Failed to get message_id. Is TELEGRAM_CHAT_ID set properly?")
