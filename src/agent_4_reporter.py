import os
import json
import requests
import shutil

def send_discord_message(message):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/1523550287313375409/Mp1Mlfgqd5bUcXbo0Z1iFkP-EgrLUxg8eQbFZTTCkCSZiWcKlHAtNnNeBBgQXUYaTnhN')
    
    if not webhook_url:
        print("Discord webhook URL is missing. Skipping Discord notification.")
        return False
        
    payload = {
        'content': message
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()
        print("Successfully sent unified Discord report.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Discord message: {e}")
        return False

def main():
    print("Starting Agent 4: Unified Reporter")
    report_path = "workspace/report.json"
    
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            try:
                report = json.load(f)
            except json.JSONDecodeError:
                report = {}
    else:
        report = {}
        
    # Default values in case keys are missing
    video_name = report.get('video_name', 'N/A')
    download_status = report.get('download_status', 'Failed / Unknown')
    editing_status = report.get('editing_status', 'N/A')
    upload_status = report.get('upload_status', 'N/A')
    seo_title = report.get('seo_title', 'N/A')
    description = report.get('description', 'N/A')
    fb_url = report.get('facebook_url', 'N/A')
    
    # Determine YouTube Status
    yt_url = report.get('youtube_url', 'N/A')
    yt_status = "Success" if "youtube.com" in yt_url or "youtu.be" in yt_url else "Failed / N/A"
    
    # GitHub Action Variables
    repo = os.environ.get('GITHUB_REPOSITORY', 'Vikram-Bosak/Facebook-Viral-Hollywood-Reels')
    run_id = os.environ.get('GITHUB_RUN_ID', 'UNKNOWN')
    repo_url = f"https://github.com/{repo}"
    run_url = f"{repo_url}/actions/runs/{run_id}"
    
    emoji_status = "✅" if upload_status == "Success" else "❌"
    
    message = (
        f"{emoji_status} **Pipeline Run Completed**\n\n"
        f"🎬 **Video Name:**\n{video_name}\n\n"
        f"📥 **Download Status:** {download_status}\n"
        f"✂️ **Editing Status:** {editing_status}\n"
        f"📤 **Facebook Upload Status:** {upload_status}\n"
        f"📤 **YouTube Upload Status:** {yt_status}\n\n"
        f"🏷️ **SEO Title:**\n{seo_title}\n\n"
        f"📝 **Description:**\n{description}\n\n"
        f"🔗 **Facebook Reel URL:**\n{fb_url}\n\n"
        f"▶️ **YouTube Video URL:**\n{yt_url}\n\n"
        f"📦 **GitHub Repository:**\n{repo_url}\n\n"
        f"📄 **Workflow Run:**\n{run_url}"
    )
    
    if "No new video" in download_status:
        print("No new video to process. Skipping Discord notification to avoid spam.")
    else:
        send_discord_message(message)
    
    # Cleanup workspace completely
    if os.path.exists("workspace"):
        shutil.rmtree("workspace")
        print("Cleaned up workspace directory.")

if __name__ == "__main__":
    main()
