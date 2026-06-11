import random

def generate_seo_metadata() -> dict:
    """
    Generates dynamic, highly optimized American English SEO metadata.
    Focuses on the US audience using terminology like 'Soccer' and 'USMNT'.
    """
    # Hooks that appeal to an American audience
    hooks = [
        "Craziest Soccer Moments in World Cup History! 🤯🇺🇸",
        "Top 10 Insane Soccer Goals You Won't Believe! 🎯",
        "0 IQ Soccer Moments Caught On Camera 😂💀",
        "The Greatest Soccer Highlights Ever Recorded 🏆",
        "Unbelievable World Cup Soccer Skills! 🔥",
        "Is This The Best Soccer Goal Ever? 😱",
        "Soccer Players Losing Their Minds! 😤",
        "Absolute Magic On The Soccer Pitch! ✨",
        "When Soccer Becomes Art 🎨⚽",
        "Most Savage Moments in World Cup Soccer 🥶"
    ]
    
    # American English specific descriptions
    descriptions = [
        "Check out this absolutely insane World Cup soccer highlight! If you love the USMNT and international soccer, you gotta see this. Don't forget to smash that like button and subscribe for daily viral sports content! 🇺🇸⚽🔥",
        "This is what peak soccer looks like! From crazy bicycle kicks to legendary goalkeeper saves, the World Cup never disappoints. Hit subscribe for more amazing soccer highlights and let us know your favorite team down in the comments! 👇",
        "You've never seen soccer skills like this before! We're breaking down the craziest, funniest, and most unbelievable moments from the world's biggest tournament. Follow us for your daily dose of viral sports action! 🏆⚡",
        "0 IQ plays or absolute genius? You decide! Watch this legendary soccer moment and tell us if you could have made that shot. Make sure to follow the channel for the best US soccer and international highlights! 🎯🇺🇸",
        "When the pressure is on, legends are born! Take a look at this jaw-dropping soccer highlight from the World Cup. Whether you're rooting for Team USA or just love the game, this clip is wild! Subscribe for more! 🔥"
    ]
    
    # US-centric Tags
    tags_pool = [
        "Soccer", "USMNT", "World Cup", "Viral Sports", "Soccer Highlights", 
        "Football", "Funny Soccer", "Crazy Goals", "Team USA", "MLS", 
        "Sports Edits", "Soccer Skills", "Goal", "Fifa World Cup"
    ]
    
    # Select random items
    title = random.choice(hooks)
    description = random.choice(descriptions)
    
    # Pick 5-8 random tags
    num_tags = random.randint(5, 8)
    selected_tags = random.sample(tags_pool, num_tags)
    
    # Append hashtags to description for Facebook/YouTube
    hashtags = " ".join([f"#{t.replace(' ', '')}" for t in selected_tags])
    full_description = f"{description}\n\n{hashtags}"
    
    return {
        "title": title,
        "description": full_description,
        "tags": selected_tags
    }
