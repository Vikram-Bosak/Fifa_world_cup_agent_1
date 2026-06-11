import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

def generate_video_hook() -> str:
    """
    Stage 1: Generates a short, catchy hook line for the video editor.
    """
    client = _get_client()
    fallback_hooks = ["INCREDIBLE GOAL!", "MESSI MAGIC!", "WORLD CUP SHOCKER!", "EPIC FIFA MOMENT"]
    
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback hook.")
        return random.choice(fallback_hooks)
        
    prompt = """
    You are an expert sports video editor. I need a single, extremely catchy, short headline (1 to 4 words max) to overlay on a viral FIFA World Cup highlight video.
    Examples: "INCREDIBLE GOAL!", "MESSI MAGIC!", "LAST-MINUTE DRAMA!", "WORLD CUP SHOCKER!"
    Return strictly ONLY the headline text, with NO quotes, NO extra words, NO markdown. Just the uppercase text.
    """
    
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=20,
        )
        content = completion.choices[0].message.content.strip().replace('"', '').replace("'", "")
        if len(content.split()) > 6: # if AI hallucinates too long
            return random.choice(fallback_hooks)
        return content.upper()
    except Exception as e:
        print(f"Error calling NVIDIA LLM API for hook: {e}")
        return random.choice(fallback_hooks)

def generate_upload_metadata(hook_line: str = None) -> dict:
    """
    Stage 2: Generates SEO metadata (Title, Description, Tags, Hashtags) for uploading.
    """
    client = _get_client()
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return _get_fallback_metadata()
        
    topic = f"The video hook line is '{hook_line}'." if hook_line else "This is a crazy FIFA World Cup football moment."
    
    prompt = f"""
    You are an expert sports social media manager. I am uploading a viral FIFA World Cup highlight reel.
    {topic}
    Please generate the following details and return ONLY a valid JSON object without any markdown wrapping or extra text.
    The JSON must contain these exact keys:
    - "title": A catchy, viral SEO title (under 60 characters).
    - "description": An engaging, SEO-optimized YouTube Shorts description (3-4 sentences) targeting US audience.
    - "facebook_caption": A short, punchy caption for Facebook Reels with a call to action.
    - "hashtags": A string of 5-7 viral hashtags (e.g., "#FIFA #Soccer #Viral").
    - "tags": A list of 5-8 SEO tags (strings) for YouTube.
    """
    
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.95,
            max_tokens=1024,
        )
        
        content = completion.choices[0].message.content
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
            
        data = json.loads(content.strip())
        
        required_keys = ["title", "description", "facebook_caption", "hashtags", "tags"]
        for key in required_keys:
            if key not in data:
                data[key] = _get_fallback_metadata()[key]
                
        return data

    except Exception as e:
        print(f"Error calling NVIDIA LLM API for SEO: {e}")
        return _get_fallback_metadata()

def _get_fallback_metadata():
    return {
        "title": "CRAZIEST FIFA MOMENT! 😱",
        "description": "Check out this absolutely insane World Cup soccer highlight! If you love international soccer, you gotta see this. Don't forget to smash that like button and subscribe for daily viral sports content! 🇺🇸⚽🔥",
        "facebook_caption": "Wait for the end... you won't believe this World Cup moment! 🤯⚽ Comment your favorite team below! 👇",
        "hashtags": "#FIFA #WorldCup #Soccer #ViralSports #Highlights",
        "tags": ["Soccer", "World Cup", "Viral Sports", "Soccer Highlights", "Crazy Goals"]
    }

if __name__ == "__main__":
    hook = generate_video_hook()
    print("Generated Hook:", hook)
    print("Generated Metadata:")
    print(json.dumps(generate_upload_metadata(hook), indent=4))
