import os
import json
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "queue.json")

def _load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading queue: {e}")
        return []

def _save_queue(data):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    try:
        with open(QUEUE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving queue: {e}")

def add_to_queue(video_data):
    """Add a new video to the queue if it doesn't already exist."""
    queue = _load_queue()
    
    # Check if already in queue
    for item in queue:
        if item.get("tweet_id") == video_data.get("tweet_id"):
            return False # Duplicate
            
    # Add to queue
    video_data["status"] = "pending"
    video_data["added_at"] = datetime.utcnow().isoformat()
    queue.append(video_data)
    _save_queue(queue)
    return True

def get_oldest_video_by_status(status):
    """Retrieve the oldest video with the given status and mark it as processing_{status}."""
    queue = _load_queue()
    
    # Sort by added_at to ensure FIFO (oldest first)
    items = [item for item in queue if item.get("status") == status]
    if not items:
        return None
        
    items.sort(key=lambda x: x.get("added_at", ""))
    oldest_video = items[0]
    
    # Mark as processing to prevent other workers from grabbing it
    for item in queue:
        if item.get("id") == oldest_video.get("id"):
            item["status"] = f"processing_{status}"
            break
            
    _save_queue(queue)
    return oldest_video

def mark_video_status(video_id, status, **kwargs):
    """Mark a video as a specific status and update additional fields."""
    queue = _load_queue()
    updated = False
    for item in queue:
        if item.get("id") == video_id:
            item["status"] = status
            for k, v in kwargs.items():
                item[k] = v
            updated = True
            break
            
    if updated:
        _save_queue(queue)
    return updated

def is_duplicate(tweet_id):
    """Check if the video is already in the queue or has been processed."""
    queue = _load_queue()
    for item in queue:
        if item.get("tweet_id") == tweet_id:
            return True
            
    # Also check legacy archive
    archive_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloader", "download_history.json")
    if os.path.exists(archive_file):
        try:
            with open(archive_file, "r") as f:
                archive = json.load(f)
                if tweet_id in archive:
                    return True
        except:
            pass
            
    return False
