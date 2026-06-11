import re
import urllib.request
import os

def download_fifa_video(url: str, output_path: str) -> bool:
    print(f"Initializing Headless Playwright to analyze DOM and Network for: {url}")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed.")
        return False
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            video_url = None
            
            # Listen to network responses to sniff for .mp4 URLs directly from the CDN
            def handle_response(response):
                nonlocal video_url
                if video_url: return
                
                req_url = response.url
                # Look for FIFA's CDN or any generic .mp4 pattern in media requests
                if ".mp4" in req_url and ("usestoryteller" in req_url or "fifa" in req_url):
                    video_url = req_url
                    print(f"Network Sniffer caught an MP4: {video_url}")
                    
            page.on("response", handle_response)
            
            print("Navigating to page and executing JavaScript...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Fallback 1: Scan the fully loaded DOM
            if not video_url:
                print("Scanning DOM for video links...")
                content = page.content()
                
                # Use regex to find hidden mp4 links
                mp4_links = re.findall(r'https://[^\s\"\'<>]*?\.mp4[^\s\"\'<>]*', content)
                for link in mp4_links:
                    if "usestoryteller" in link or "cdn" in link:
                        video_url = link
                        print(f"DOM Scanner found an MP4: {video_url}")
                        break
            
            browser.close()
            
            if video_url:
                print(f"Successfully extracted direct video link: {video_url}")
                print(f"Downloading to {output_path}...")
                
                req = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(output_path, 'wb') as out_file:
                    out_file.write(response.read())
                print("Download completed via python urllib.")
                return True
            else:
                print("No valid MP4 link could be extracted from the page.")
                return False
                
    except Exception as e:
        print(f"Playwright scraper encountered an error: {e}")
        return False
