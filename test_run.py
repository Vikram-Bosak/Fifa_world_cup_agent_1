import sys
import os
sys.path.append(os.path.abspath("."))
from editor.advanced_editor import process_video_dynamically
from common.telegram import send_video

task = {
    "id": "20260614_111302_2066113425474986232",
    "tweet_id": "2066113425474986232",
    "source_url": "https://x.com/FIFAWorldCup/status/2066113425474986232",
    "profile": "https://x.com/FIFAWorldCup",
    "title": "When Zlatan made his #FIFAWorldCup debut 🇸🇪🤩",
    "local_path": "temp/2066113425474986232.mp4",
    "source": "FIFA World Cup"
}

output_path = "temp/edited_FINAL_LAYOUT_2066113425474986232.mp4"
logo_path = "assets/custom_logo.png"

print("Starting dynamic processing...")
final_path, hook = process_video_dynamically("temp/2066113425474986232.mp4", logo_path, output_path, task)
print("Finished processing. Sending to telegram...")
send_video(final_path, caption=f"Here is your final video! \n\nHook generated:\n{hook}")
print("Done.")
