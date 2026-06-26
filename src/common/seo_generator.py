import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

# Try to import Google GenAI
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Trending Football/Soccer Keywords for SEO
# ──────────────────────────────────────────────────────────────────────────────
FOOTBALL_KEYWORDS = {
    "players": [
        "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappé", "Erling Haaland",
        "Jude Bellingham", "Vinicius Jr", "Bukayo Saka", "Rodri",
        "Federico Valverde", "Florian Wirtz", "Lamine Yamal", "Phil Foden",
        "Ousmane Dembélé", "Neymar", "Kevin De Bruyne", "Marcus Rashford",
    ],
    "teams": [
        "Real Madrid", "FC Barcelona", "Manchester City", "Bayern Munich",
        "Paris Saint-Germain", "Liverpool", "Arsenal", "Inter Milan",
        "Atletico Madrid", "Napoli", "Borussia Dortmund", "Juventus",
    ],
    "competitions": [
        "FIFA World Cup", "UEFA Champions League", "Premier League",
        "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Copa America",
        "UEFA Euro 2026", "Club World Cup", "AFCON", "FA Cup",
    ],
    "football_terms": [
        "football highlights", "soccer goals", "world class goal",
        "skill move", "nutmeg", "free kick", "bicycle kick",
        "solo goal", "team goal", "counter attack", "tiki taka",
        "pressing", "tactical masterclass", "instant classic",
    ],
    "emotional_hooks": [
        "unbelievable", "insane", "world class", "must watch",
        "viral football", "football magic", "pure class",
        "this is why we love football", "goosebumps",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Trending Football Hashtags
# ──────────────────────────────────────────────────────────────────────────────
FOOTBALL_HASHTAGS = [
    "#FIFAWorldCup", "#Football", "#Soccer", "#WorldCup2026",
    "#ChampionsLeague", "#PremierLeague", "#LaLiga", "#FootballHighlights",
    "#SoccerGoals", "#ViralFootball", "#FootballDaily", "#BeautifulGame",
    "#MatchDay", "#FootballFans", "#TopBins", "#CleanSheet",
    "#FootballMoments", "#SoccerViral", "#GoalOfTheSeason",
    "#Messi", "#Ronaldo", "#Haaland", "#Mbappe",
    "#RealMadrid", "#Barcelona", "#ManCity", "#Arsenal",
    "#ElClasico", "#FootballEdit", "#FootballMemes", "#GOAT",
]


# ──────────────────────────────────────────────────────────────────────────────
# Client & Gemini helpers (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def _get_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

def _extract_gemini_video_context(video_path: str) -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not HAS_GEMINI or not gemini_key or not video_path or not os.path.exists(video_path):
        return ""
        
    print(f"Deep Video Analysis: Uploading {video_path} to Gemini 1.5 Flash...")
    try:
        client = genai.Client(api_key=gemini_key)
        video_file = client.files.upload(file=video_path)
        
        # Wait for video processing
        while video_file.state.name == "PROCESSING":
            print("Waiting for video processing...")
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            print("Gemini Video processing failed.")
            return ""
            
        prompt = "Analyze this video completely. 1) Describe exactly what is happening visually. 2) If it is a meme, edit, or specific historical event (e.g., a war edit masked as a football video), explicitly state what the true hidden subject is. 3) Read any on-screen text (OCR). 4) Transcribe any spoken words. Be extremely accurate."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, prompt]
        )
        
        # Cleanup file from Gemini servers
        client.files.delete(name=video_file.name)
        
        print("Gemini Context Extraction Successful.")
        return response.text
    except Exception as e:
        print(f"Error extracting deep video context: {e}")
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 – Analyze video for editing (improved prompts)
# ──────────────────────────────────────────────────────────────────────────────
def analyze_video_for_editing(context: dict) -> dict:
    """
    Stage 1: Analyzes video context and generates Hook Line, Short Headline, Overlay Text, and Category.
    """
    client = _get_client()
    
    original_title = context.get('title', '')
    fallback = {
        "category": "Highlight",
        "short_headline": (
            original_title[:35] + "..."
            if len(original_title) > 35
            else (original_title if original_title else "UNMISSABLE MOMENT ⚽🔥")
        ),
        "story": (
            original_title
            if original_title
            else "Did you just see that?! This is the kind of moment that makes football the greatest sport on Earth. Watch till the end! 😱"
        ),
        "overlay_text": "⚽ MUST-SEE FOOTBALL MOMENT"
    }
    
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback analysis.")
        return fallback
        
    # Check if we should extract deep context via Gemini
    deep_context = ""
    local_path = context.get('local_path')
    if local_path and os.getenv("GEMINI_API_KEY"):
        deep_context = _extract_gemini_video_context(local_path)
        if deep_context:
            context['deep_context'] = deep_context  # Save for stage 2
            
    # Build context snippet for trending keywords injection
    trending_snippet = (
        f"\nTrending keyword pools to weave in naturally: "
        f"Players: {', '.join(FOOTBALL_KEYWORDS['players'][:6])}; "
        f"Terms: {', '.join(FOOTBALL_KEYWORDS['football_terms'][:6])}; "
        f"Hooks: {', '.join(FOOTBALL_KEYWORDS['emotional_hooks'][:5])}."
    )

    prompt = f"""You are a world-class FIFA World Cup and global football social media strategist who crafts viral short-form content (YouTube Shorts, TikTok, Facebook Reels).

=== SOURCE OF TRUTH ===
Original Title/Text: {context.get('title', 'Unknown')}
Source Profile: {context.get('source', 'Unknown')}
{f"Deep AI Video Context: {context.get('deep_context', '')[:800]}" if context.get('deep_context') else ""}
{trending_snippet}

=== YOUR TASK ===
Analyze the "Original Title/Text" deeply. Identify:
• The exact football players, clubs, national teams, or competition mentioned.
• The emotional hook (e.g., rage, disbelief, joy, heartbreak).
• The type of football moment (goal, save, tackle, celebration,VAR controversy, press conference drama, transfer news, etc.).

Then generate:

1. **short_headline** – 3-6 words max, ALL CAPS, punchy, in ENGLISH. Include 1 relevant emoji. 
   Examples: "RONALDO'S INSANE HEADER 🤯", "GOALKEEPER GOES BEAST MODE 🧤", "VAR DECIDES THE WORLD CUP 🏆"

2. **story** – A 2-3 sentence paragraph that builds suspense and drives the viewer to watch. Use a conversational, excited tone. Include 2-3 emojis. Must feel like a football fan hyping their friend.
   Example: "This free kick from 35 yards left the entire stadium speechless. The goalkeeper didn't even move. Is this the goal of the tournament? 👇⚽🔥"

3. **category** – One of: "Highlight", "Skill Move", "Goal", "Save", "Drama", "News/Transfer", "Fun/Meme", "Documentary".

=== RULES ===
• Write ONLY in English.
• Stay strictly within football/soccer context. NEVER reference movies, music, or non-football topics.
• Use trending football keywords naturally in your output.
• Make it feel like a fan, not a corporate account.
• No clickbait promises that the video can't deliver.

Return ONLY a valid JSON object with these exact keys:
{{
  "category": "...",
  "short_headline": "...",
  "story": "..."
}}"""
    
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
            timeout=45,
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


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 – Generate upload metadata (improved, platform-specific)
# ──────────────────────────────────────────────────────────────────────────────
def generate_upload_metadata(context: dict) -> dict:
    """
    Stage 2: Generates SEO metadata based on the full editing context.
    Platform-specific: YouTube (title <60 chars, description, tags) + Facebook (caption, hashtags).
    """
    client = _get_client()
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return _get_fallback_metadata(context)
    
    # Build a compact keyword reference for the prompt
    sample_keywords = ', '.join(
        FOOTBALL_KEYWORDS['players'][:4]
        + FOOTBALL_KEYWORDS['teams'][:4]
        + FOOTBALL_KEYWORDS['competitions'][:3]
    )
    sample_hashtags = ' '.join(FOOTBALL_HASHTAGS[:15])

    prompt = f"""You are a top-tier football/soccer social media SEO specialist. Generate platform-specific upload metadata for a viral football video.

=== FULL VIDEO CONTEXT ===
Original Title/Text: {context.get('title', 'Unknown')}
Source Profile: {context.get('source', 'Unknown')}
Determined Category: {context.get('category', 'Highlight')}
Headline Used in Video: {context.get('short_headline', '')}
Story Used in Video: {context.get('story', '')}

=== TRENDING FOOTBALL REFERENCE DATA ===
Keyword pool (use naturally): {sample_keywords}
Trending hashtag pool: {sample_hashtags}

=== YOUR TASK ===
Generate SEO metadata tailored for YouTube AND Facebook. Each platform has different best practices.

**1. "title" (YouTube SEO Title)**
• STRICTLY under 60 characters.
• Include the most relevant player/team/competition name.
• Use a power word (UNBELIEVABLE, INSANE, CLASS, GOAL, EPIC).
• Example: "Mbappé's Insane Solo Goal ⚽ World Cup 2026"

**2. "description" (YouTube Description)**
• 2-3 sentences. First sentence must hook the viewer.
• Naturally include 3-5 football keywords (player names, teams, competition).
• End with a call to action (Like, Subscribe, Comment).
• Include relevant hashtags at the end.

**3. "facebook_caption" (Facebook Reels Caption)**
• Short, punchy, MAX 2 sentences. Do NOT include hashtags here.
• Must include a clear call-to-action (e.g., "Tag a football friend!", "Who did this better?", "Drop a ⚽ if you watched till the end").
• Conversational tone, like texting a friend.

**4. "hashtags" (Facebook Hashtags – string)**
• A single string of 7-8 highly relevant hashtags.
• MUST include at least 2 player/team-specific hashtags from the context.
• Mix broad (#Football, #Soccer) with specific (#PremierLeague, #ChampionsLeague).
• Never use non-football hashtags.

**5. "tags" (YouTube Tags – list of strings)**
• A list of 8-10 SEO tags for YouTube.
• Include: player names (2-3), team names (1-2), competition names (1-2), generic football terms (2-3).
• Tags should be what fans would actually search on YouTube.

=== RULES ===
• Everything must be strictly football/soccer. No entertainment, no general sports.
• Write only in English.
• Match the emotional tone of the video (epic goal → excited, controversy → dramatic, skill → amazed).
• If you can identify the specific players/teams from the title, USE their exact names.

Return ONLY a valid JSON object with these exact keys:
{{
  "title": "...",
  "description": "...",
  "facebook_caption": "...",
  "hashtags": "...",
  "tags": ["...", "...", "..."]
}}"""
    
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
        
        # Enforce YouTube title length
        if "title" in data and len(data["title"]) > 60:
            data["title"] = data["title"][:57] + "..."
        
        required_keys = ["title", "description", "facebook_caption", "hashtags", "tags"]
        for key in required_keys:
            if key not in data:
                data[key] = _get_fallback_metadata(context)[key]
                
        return data

    except Exception as e:
        print(f"Error calling NVIDIA LLM API for SEO: {e}")
        return _get_fallback_metadata(context)


# ──────────────────────────────────────────────────────────────────────────────
# Football-specific fallbacks
# ──────────────────────────────────────────────────────────────────────────────
def _get_fallback_metadata(context=None):
    if not context:
        context = {}
    original_title = context.get('title', 'Unbelievable Football Moment! ⚽🔥')
    category = context.get('category', 'Highlight')

    # Smart truncation for YouTube title
    yt_title = original_title[:57] + "..." if len(original_title) > 57 else original_title

    # Build description with trending keywords
    kw = FOOTBALL_KEYWORDS
    player_hint = ""
    if any(p.lower() in original_title.lower() for p in kw["players"]):
        matched = [p for p in kw["players"] if p.lower() in original_title.lower()][0]
        player_hint = f" featuring {matched}"

    description = (
        f"{original_title}\n\n"
        f"This is football at its finest! From the beautiful game to the biggest stages in the world, "
        f"moments like these remind us why we love the sport.{' Featuring ' + player_hint.strip() + '.' if player_hint else ''}\n"
        f"👉 LIKE this video, SUBSCRIBE for daily football highlights, and COMMENT who your GOAT is! 🐐⚽"
    )

    # Pick the most relevant hashtags from the trending list
    context_lower = original_title.lower()
    specific_hashtags = []
    for ht in FOOTBALL_HASHTAGS:
        name = ht[1:].lower()  # strip #
        if name in context_lower or any(name in p.lower() for p in kw["players"]) or any(name in t.lower() for t in kw["teams"]):
            specific_hashtags.append(ht)
    # Always include broad ones
    base_hashtags = ["#Football", "#Soccer", "#FootballHighlights", "#ViralFootball"]
    all_hashtags = list(dict.fromkeys(specific_hashtags + base_hashtags))[:8]
    hashtag_string = " ".join(all_hashtags)

    # Build tags
    tags = []
    # Add matched players
    for p in kw["players"]:
        if p.lower() in context_lower:
            tags.append(p)
    # Add matched teams
    for t in kw["teams"]:
        if t.lower() in context_lower:
            tags.append(t)
    # Add matched competitions
    for c in kw["competitions"]:
        if c.lower() in context_lower:
            tags.append(c)
    # Fill with generic football tags
    generic = ["Football", "Soccer", "Football Highlights", "World Cup", "GOAT", "Best Goals"]
    for g in generic:
        if len(tags) < 10 and g not in tags:
            tags.append(g)
    tags = tags[:10]

    return {
        "title": yt_title,
        "description": description,
        "facebook_caption": (
            f"{original_title}\n\n"
            f"{'⚽ This is why football is the greatest sport on Earth!' if 'goal' in context_lower or 'highlight' in category.lower() else '🔥 Football never disappoints!'}"
            f" Drop a comment and tag a friend who needs to see this! 👇"
        ),
        "hashtags": hashtag_string,
        "tags": tags,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Self-test
# ──────────────────────────────────────────────────────────────────────────────
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
