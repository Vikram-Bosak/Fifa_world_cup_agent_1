import sys
import os

from src.agent_2_editor import process_video

# Create a mock video data
video_data = {
    "id": "test_local_edit",
    "local_path": "assets/fallback.mp4",
    "title": "MESSI CRAZY GOAL WORLD CUP 2022"
}

# Ensure workspace dir exists
os.makedirs("workspace", exist_ok=True)

print("Running local test edit...")
result = process_video(video_data)
print("Edit result:", result)

if result.get("editing_status") == "Success":
    print(f"Video saved successfully to: {result.get('edited_path')}")
else:
    print("Editing failed.")
