from google_auth_oauthlib.flow import InstalledAppFlow
import threading
import time
import sys

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("="*50)
    print("Starting YouTube Authentication Flow...")
    print("="*50)
    print("Please click the link below to authorize the application:")
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    
    # Run the server in a separate thread
    creds_container = []
    
    def run_server():
        try:
            creds = flow.run_local_server(port=0, open_browser=False)
            creds_container.append(creds)
        except Exception as e:
            print(f"Error: {e}")
            
    t = threading.Thread(target=run_server)
    t.start()
    
    # Keep the main thread alive and print dots every 5 seconds to prevent timeout
    print("Waiting for you to paste the URL back (Server will stay alive for 10 minutes)...")
    for _ in range(120): # 120 * 5 = 600 seconds = 10 minutes
        if not t.is_alive():
            break
        print(".", end="", flush=True)
        time.sleep(5)
        
    if creds_container:
        creds = creds_container[0]
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("\n" + "="*50)
        print("Authentication successful! 'token.json' has been created.")
        print("="*50)
    else:
        print("\nAuthentication timed out or failed.")

if __name__ == '__main__':
    main()
