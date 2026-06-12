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

def analyze_video_for_editing(context: dict) -> dict:
    """
    Stage 1: Analyzes video context and generates Hook Line, Short Headline, Overlay Text, and Category.
    """
    client = _get_client()
    
    fallback = {
        "category": "Highlight",
        "hook_line": "INCREDIBLE MOMENT!",
        "short_headline": "MUST WATCH",
        "overlay_text": "EPIC FOOTBALL SKILLS"
    }
    
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback analysis.")
        return fallback
        
    prompt = f"""
    You are an expert sports video editor. Analyze the following video information:
    Title/Text: {context.get('title', 'Unknown')}
    Source Profile: {context.get('source', 'Unknown')}
    Source URL: {context.get('source_url', 'Unknown')}
    
    Based on this, generate the following details for the video overlay:
    - "category": The video category (e.g., Goal Highlight, Celebration, Transfer News, Interview).
    - "hook_line": A single, extremely catchy, short headline (1 to 4 words max) including 1-2 relevant emojis like "MESSI MAGIC! 🐐🔥".
    - "short_headline": A brief contextual headline (2-5 words).
    - "overlay_text": A descriptive text for the bottom banner (2-5 words) including 1 relevant emoji like "INCREDIBLE FREE KICK ⚽".
    
    Return strictly ONLY a valid JSON object without any markdown wrapping or extra text.
    """
    
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        content = completion.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        data = json.loads(content.strip())
        
        for key in fallback.keys():
            if key not in data:
                data[key] = fallback[key]
                
        return data
    except Exception as e:
        print(f"Error calling NVIDIA LLM API for editing analysis: {e}")
        return fallback

def generate_upload_metadata(context: dict) -> dict:
    """
    Stage 2: Generates SEO metadata based on the full editing context.
    """
    client = _get_client()
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return _get_fallback_metadata()
        
    prompt = f"""
    You are an expert sports social media manager. I am uploading a viral FIFA World Cup highlight reel.
    Here is the video information and editing analysis:
    Original Title/Text: {context.get('title', 'Unknown')}
    Source Profile: {context.get('source', 'Unknown')}
    Category: {context.get('category', 'Highlight')}
    Hook Line Used: {context.get('hook_line', '')}
    Overlay Text Used: {context.get('overlay_text', '')}
    
    Please generate the following details and return ONLY a valid JSON object without any markdown wrapping.
    The JSON must contain these exact keys:
    - "title": A catchy, viral SEO title (under 60 characters).
    - "description": An engaging, SEO-optimized YouTube Shorts description (3-4 sentences) targeting US audience.
    - "facebook_caption": A short, punchy caption for Facebook Reels with a call to action.
    - "hashtags": A string of 5-7 viral hashtags (e.g., "#FIFA #Soccer #Viral"). Include the category if applicable.
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
    dummy_context = {
        "title": "Messi Scores Stunning Free Kick against France",
        "source": "FIFA World Cup",
        "source_url": "https://x.com/FIFAWorldCup/status/1234567890"
    }
    analysis = analyze_video_for_editing(dummy_context)
    print("Editing Analysis:")
    print(json.dumps(analysis, indent=4))
    
    # Merge for Stage 2
    dummy_context.update(analysis)
    
    print("\nGenerated Metadata:")
    print(json.dumps(generate_upload_metadata(dummy_context), indent=4))
