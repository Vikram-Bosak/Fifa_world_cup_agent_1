import os

with open('uploader/uploader.py', 'r') as f:
    code = f.read()

# Replace custom report with report_final_summary
old_report_code = """
    # Send Telegram Report
    report = (
        f"🚀 <b>Final Upload Report</b>\\n\\n"
        f"<b>Title:</b> {title}\\n"
        f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\\n\\n"
        f"🔵 <b>Facebook Status:</b> {'✅ Success' if fb_url != 'Failed' else '❌ Failed'}\\n"
        f"🔗 URL: {fb_url}\\n"
        f"⚠️ Error: {fb_err if fb_url == 'Failed' else 'None'}\\n\\n"
        f"🔴 <b>YouTube Status:</b> {'✅ Success' if yt_url != 'Failed' else '❌ Failed'}\\n"
        f"🔗 URL: {yt_url}\\n"
        f"⚠️ Error: {yt_err if yt_url == 'Failed' else 'None'}\\n"
    )
    
    from common.telegram import TELEGRAM_REPORT_CHAT_ID
    send_message(report, TELEGRAM_REPORT_CHAT_ID)
"""

new_report_code = """
    # Send Final Telegram Report
    from common.telegram import report_final_summary
    summary_data = {
        'title': title,
        'description': description,
        'fb_url': fb_url if fb_url != 'Failed' else 'N/A',
        'yt_url': yt_url if yt_url != 'Failed' else 'N/A',
        'original_file': video_path,
        'job_status': 'Success' if fb_url != 'Failed' or yt_url != 'Failed' else 'Failed'
    }
    report_final_summary(summary_data)
"""

if old_report_code in code:
    code = code.replace(old_report_code, new_report_code)
    with open('uploader/uploader.py', 'w') as f:
        f.write(code)
    print("Fixed uploader.py")
else:
    print("Could not find the old report code snippet")
