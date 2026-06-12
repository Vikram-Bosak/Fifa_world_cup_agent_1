import os
import subprocess

def download_x_video(profile_url: str, output_path: str) -> bool:
    """
    Downloads the latest video from a Twitter (X) profile using yt-dlp.
    """
    print(f"Fetching latest video from {profile_url} using yt-dlp...")
    
    # Ensure temp directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if file exists and remove it to avoid yt-dlp skipping or appending issues
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # We use --playlist-items 1 to get only the most recent video
    # --no-playlist is NOT used because we WANT it to treat the profile as a playlist
    # We output directly to the desired path
    command = [
        "yt-dlp",
        "--playlist-items", "1",
        "-o", output_path,
        "--merge-output-format", "mp4",
        profile_url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Successfully downloaded latest Twitter video.")
        # Print a snippet of the output for debugging
        print(result.stdout[-500:])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading Twitter video with yt-dlp: {e}")
        print("Output:", e.stdout)
        print("Error:", e.stderr)
        return False

if __name__ == "__main__":
    # Test script
    profile = "https://x.com/FIFAWorldCup"
    output = "temp/test_x_video.mp4"
    success = download_x_video(profile, output)
    if success:
        print(f"Video saved to {output}")
