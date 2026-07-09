import os
import json
import requests
import shutil

def send_discord_report(embed):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Discord Webhook URL is missing. Skipping Discord notification.")
        return False
        
    payload = {
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
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
    
    is_success = upload_status == "Success"
    color = 3066993 if is_success else 15158332
    
    embed = {
        "title": "✅ Pipeline Run Completed Successfully" if is_success else "❌ Pipeline Run Failed",
        "color": color,
        "fields": [
            {"name": "🎬 Video Name", "value": video_name, "inline": False},
            {"name": "📥 Download Status", "value": download_status, "inline": True},
            {"name": "✂️ Editing Status", "value": editing_status, "inline": True},
            {"name": "📤 Facebook Upload", "value": upload_status, "inline": True},
            {"name": "📤 YouTube Upload", "value": yt_status, "inline": True},
            {"name": "🏷️ SEO Title", "value": seo_title, "inline": False},
            {"name": "🔗 Facebook Reel URL", "value": fb_url, "inline": False},
            {"name": "▶️ YouTube Video URL", "value": yt_url, "inline": False},
            {"name": "📄 Workflow Run", "value": f"[View Run]({run_url})", "inline": False}
        ],
        "footer": {
            "text": f"Repository: {repo} | Run ID: {run_id}"
        }
    }
    
    if "No new video" in download_status:
        print("No new video to process. Skipping Discord notification to avoid spam.")
    else:
        send_discord_report(embed)
    
    # Cleanup workspace completely
    if os.path.exists("workspace"):
        shutil.rmtree("workspace")
        print("Cleaned up workspace directory.")

if __name__ == "__main__":
    main()
