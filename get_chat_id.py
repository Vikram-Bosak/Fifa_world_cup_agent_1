import requests
import time
import os

TOKEN = "8922110216:AAFqeB4q563_Q3118QGKo_FLmJZWHcaTf_s"
URL = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

print("Waiting for user to send a message to the bot...")
for _ in range(60): # 5 minutes
    try:
        response = requests.get(URL).json()
        if response.get("ok") and response.get("result"):
            chat_id = response["result"][0]["message"]["chat"]["id"]
            print(f"Got chat ID: {chat_id}")
            
            # Append to .env
            with open(".env", "a") as f:
                f.write(f"\nTELEGRAM_BOT_TOKEN={TOKEN}")
                f.write(f"\nTELEGRAM_CHAT_ID={chat_id}\n")
            print(".env updated successfully!")
            
            # Send confirmation
            send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(send_url, json={"chat_id": chat_id, "text": "✅ System connected! Reporting is now active."})
            break
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(5)
