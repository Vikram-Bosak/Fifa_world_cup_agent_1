import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_seo_metadata() -> dict:
    """
    Calls NVIDIA's LLM API (nemotron-3-ultra-550b-a55b) to generate viral SEO metadata.
    Returns a dictionary with title, description, facebook_caption, hashtags, and tags.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return get_fallback_metadata()
        
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )
    
    prompt = """
    You are an expert sports social media manager. I need viral content for a thrilling FIFA World Cup highlight reel.
    Please generate the following details and return ONLY a valid JSON object without any markdown wrapping or extra text.
    The JSON must contain these exact keys:
    - "title": A catchy, viral, 2-5 word title (e.g., "🔥 MESSI MAGIC", "CRAZIEST FIFA MOMENT! 😱").
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
        
        # The API returns the content in the choices
        content = completion.choices[0].message.content
        
        # Clean up in case the LLM returned markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        
        # Ensure all keys are present
        required_keys = ["title", "description", "facebook_caption", "hashtags", "tags"]
        for key in required_keys:
            if key not in data:
                data[key] = get_fallback_metadata()[key]
                
        return data

    except Exception as e:
        print(f"Error calling NVIDIA LLM API: {e}")
        return get_fallback_metadata()

def get_fallback_metadata():
    return {
        "title": "CRAZIEST FIFA MOMENT! 😱",
        "description": "Check out this absolutely insane World Cup soccer highlight! If you love international soccer, you gotta see this. Don't forget to smash that like button and subscribe for daily viral sports content! 🇺🇸⚽🔥",
        "facebook_caption": "Wait for the end... you won't believe this World Cup moment! 🤯⚽ Comment your favorite team below! 👇",
        "hashtags": "#FIFA #WorldCup #Soccer #ViralSports #Highlights",
        "tags": ["Soccer", "World Cup", "Viral Sports", "Soccer Highlights", "Crazy Goals"]
    }

if __name__ == "__main__":
    print(json.dumps(generate_seo_metadata(), indent=4))
