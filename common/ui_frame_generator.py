import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def generate_ui_frame(output_path: str, source_name: str, headline: str, story: str, width=1080, height=1440):
    """
    Generates a Facebook-style UI frame with transparent center for video placement.
    """
    # Create a fully transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    fb_blue = (59, 89, 152, 255)
    white = (255, 255, 255, 255)
    light_blue = (139, 157, 195, 255)
    yellow = (255, 215, 0, 255)
    black = (0, 0, 0, 255)
    
    # Layout dimensions
    top_bar_height = 120
    bottom_bar_height = 380
    
    # 1. Draw Top Banner
    draw.rectangle([0, 0, width, top_bar_height], fill=fb_blue)
    
    # 2. Draw Bottom Banner
    draw.rectangle([0, height - bottom_bar_height, width, height], fill=fb_blue)
    
    # 3. Draw Borders (Yellow outer, black inner, yellow innermost)
    border_thickness = 8
    
    # Outer border around the whole image
    draw.rectangle([0, 0, width, height], outline=yellow, width=5)
    draw.rectangle([5, 5, width-5, height-5], outline=black, width=3)
    draw.rectangle([8, 8, width-8, height-8], outline=yellow, width=2)
    
    # Fonts
    font_path_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_path_regular = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    
    try:
        font_source = ImageFont.truetype(font_path_bold, 45)
        font_headline = ImageFont.truetype(font_path_bold, 55)
        font_story = ImageFont.truetype(font_path_regular, 38)
        font_stats = ImageFont.truetype(font_path_bold, 40)
    except IOError:
        font_source = ImageFont.load_default()
        font_headline = ImageFont.load_default()
        font_story = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        
    with Pilmoji(img) as pilmoji:
        # --- Top Banner Content ---
        # Profile Icon (Emoji) + Source Name
        top_y = 35
        pilmoji.text((40, top_y), "👤", fill=white, font=font_headline) # Profile icon
        
        display_name = source_name.upper() if source_name else "GLOBAL FOOTBALL NEWS"
        pilmoji.text((120, top_y + 5), display_name, fill=white, font=font_source)
        
        # --- Bottom Banner Content ---
        start_y = height - bottom_bar_height + 30
        
        # Headline
        headline_text = headline.strip().upper()
        if not headline_text:
            headline_text = "HISTORIC MOMENT FOR FOOTBALL! ⚽"
            
        pilmoji.text((40, start_y), headline_text, fill=white, font=font_headline)
        
        # Story (Wrapped)
        start_y += 80
        if not story:
            story = "The national team arrives to a massive crowd ahead of their crucial match! Can they go all the way? #Fifa #WorldCup #FootballNews #Sports"
            
        story_lines = textwrap.wrap(story, width=55)
        for line in story_lines:
            pilmoji.text((40, start_y), line, fill=white, font=font_story)
            start_y += 50
            
        # Draw a thin separator line above engagement bar
        sep_y = height - 90
        draw.line([(30, sep_y), (width - 30, sep_y)], fill=(255,255,255,100), width=2)
        
        # Engagement Bar (Like, Comment, Share)
        engage_y = height - 70
        
        # Random Likes (e.g. 15.2K Likes)
        likes_num = round(random.uniform(10.0, 99.9), 1)
        likes_text = f"👍❤️ {likes_num}K Likes"
        pilmoji.text((40, engage_y), likes_text, fill=white, font=font_stats)
        
        # Comment
        comment_text = "💬 Comment"
        pilmoji.text((500, engage_y), comment_text, fill=white, font=font_stats)
        
        # Share
        share_text = "↗️ Share"
        pilmoji.text((800, engage_y), share_text, fill=white, font=font_stats)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    generate_ui_frame(
        "temp/test_ui_frame.png", 
        "GLOBAL FOOTBALL NEWS", 
        "HISTORIC MOMENT FOR SPANISH FOOTBALL! 🇪🇸", 
        "The Espana national arrives to a massive crowd ahead of their crucial match! Can they go all the way? #España #Fifa #WorldCup #FootballNews"
    )
