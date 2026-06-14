from editor.advanced_editor import process_video_dynamically
from common.telegram import send_message

task = {
    "id": "20260612_052826_2065121006038237667",
    "title": "Five World Cups. Five unforgettable goals. Which one is y...",
    "source": "FIFA World Cup",
    "source_url": "https://x.com/FIFAWorldCup/status/2065121006038237667"
}

send_message(f"🔄 **Manual Edit Triggered**\nPOST ID: {task['id']}")

try:
    process_video_dynamically(
        input_path="temp/2065121006038237667.mp4",
        logo_path="assets/custom_logo.png",
        output_path="temp/edited_2065121006038237667.mp4",
        task=task
    )
    send_message(f"✅ **Manual Edit Successful**\nPOST ID: {task['id']}")
except Exception as e:
    print(f"Error: {e}")
    send_message(f"❌ **Manual Edit Failed**\nPOST ID: {task['id']}\nError: {e}")

