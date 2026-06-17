import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def generate_ui_frame(output_path: str, source_name: str, headline: str, story: str, width=1080, height=1440):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    fb_blue = (59, 89, 152, 255)
    white = (255, 255, 255, 255)
    yellow = (255, 215, 0, 255)
    line_color = (255, 255, 255, 60)
    
    # 1. Outer yellow border (5px)
    draw.rectangle([0, 0, width, height], outline=yellow, width=5)
    
    # 2. Draw Top Banner (Using extracted exact asset)
    top_banner_path = os.path.join(os.path.dirname(__file__), "../assets/top_banner_extracted.png")
    top_bar_height = 90
    if os.path.exists(top_banner_path):
        top_banner_img = Image.open(top_banner_path).convert("RGBA")
        top_banner_resized = top_banner_img.resize((width - 10, top_bar_height), Image.LANCZOS)
        img.paste(top_banner_resized, (5, 5), top_banner_resized)
    else:
        draw.rectangle([5, 5, width-5, top_bar_height+5], fill=fb_blue)
        
    # 3. Draw Bottom Banner
    bottom_bar_height = 340
    draw.rectangle([5, height - bottom_bar_height - 5, width - 5, height - 5], fill=fb_blue)
    
    # Fonts
    font_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_reg = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    
    try:
        f_head = ImageFont.truetype(font_bold, 40)
        f_story = ImageFont.truetype(font_reg, 32)
        f_stats = ImageFont.truetype(font_bold, 35)
    except IOError:
        f_head = f_story = f_stats = ImageFont.load_default()
        
    with Pilmoji(img) as pilmoji:
        start_y = height - bottom_bar_height + 25
        
        # Main Headline
        try:
            f_sub = ImageFont.truetype(font_bold, 35)
        except IOError:
            f_sub = ImageFont.load_default()
            
        headline_text = headline.strip() if headline else ""
        pilmoji.text((30, start_y), headline_text, fill=white, font=f_sub)
        
        start_y += 55
        
        # User Avatar and Name
        avatar_y = start_y
        avatar_size = 50
        draw.ellipse([30, avatar_y, 30+avatar_size, avatar_y+avatar_size], fill=(30, 30, 30, 255))
        
        # Draw logo inside circle if exists
        if os.path.exists(top_banner_path):
            try:
                logo_img = Image.open(top_banner_path).convert("RGBA")
                # Crop a square from the left side of the banner (where the logo usually is)
                logo_square = logo_img.crop((0, 0, logo_img.height, logo_img.height))
                logo_resized = logo_square.resize((avatar_size, avatar_size), Image.LANCZOS)
                
                # Make circular mask
                mask = Image.new('L', (avatar_size, avatar_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                
                img.paste(logo_resized, (30, avatar_y), mask)
            except:
                pass
                
        try:
            f_user = ImageFont.truetype(font_bold, 25)
        except IOError:
            f_user = ImageFont.load_default()
            
        pilmoji.text((90, avatar_y + 10), "Hollywood Insider ⚙️", fill=white, font=f_user)
        
        start_y += 70
        
        # Story
        story_text = story if story else "History hides in the details. 👀 Did you spot this iconic World Cup moment? Drop a comment if you saw it! 🏆👇"
        story_lines = textwrap.wrap(story_text, width=70)
        
        try:
            f_story = ImageFont.truetype(font_reg, 26)
            f_story_bold = ImageFont.truetype(font_bold, 26)
        except IOError:
            f_story = ImageFont.load_default()
            f_story_bold = ImageFont.load_default()
            
        for line in story_lines[:2]: # Max 2 lines to fit space
            pilmoji.text((30, start_y), line, fill=white, font=f_story)
            start_y += 35
            
        # See more
        pilmoji.text((30, start_y), "#... See more", fill=white, font=f_story_bold)
            
        # Separator Line
        sep_y = height - 100
        draw.line([(25, sep_y), (width - 25, sep_y)], fill=line_color, width=2)
        
        # --- ENGAGEMENT BAR ---
        engage_y = height - 80
        
        # 'Tap or hold...' hint text
        try:
            f_hint = ImageFont.truetype(font_reg, 20)
        except IOError:
            f_hint = ImageFont.load_default()
        pilmoji.text((490, engage_y - 20), "Tap or hold to like and react with Love, Haha, Wow, or Sad!", fill=(200, 200, 200, 255), font=f_hint)
        
        # overlapping emojis
        draw.ellipse([30, engage_y, 30+40, engage_y+40], fill=(24,119,242,255))
        draw.ellipse([55, engage_y, 55+40, engage_y+40], fill=(240,40,73,255))
        draw.ellipse([80, engage_y, 80+40, engage_y+40], fill=(247,177,37,255))
        draw.ellipse([105, engage_y, 105+40, engage_y+40], fill=(247,177,37,255))
        
        pilmoji.text((35, engage_y+2), "👍", fill=white, font=f_stats)
        pilmoji.text((60, engage_y+2), "❤️", fill=white, font=f_stats)
        pilmoji.text((85, engage_y+2), "😂", fill=white, font=f_stats)
        pilmoji.text((110, engage_y+2), "😲", fill=white, font=f_stats)
        
        likes_num = random.randint(10000, 99999)
        formatted_likes = f"{likes_num:,} Likes"
        pilmoji.text((160, engage_y+2), formatted_likes, fill=white, font=f_stats)
        
        pilmoji.text((550, engage_y+2), "💬 Comment", fill=white, font=f_stats)
        pilmoji.text((820, engage_y+2), "↗️ Share", fill=white, font=f_stats)
        
        # --- VIDEO CREDIT OVERLAY ---
        # Draw on the transparent area so it overlays on the video
        credit_text = "Video Credit: Hollywood News"
        try:
            f_credit = ImageFont.truetype(font_bold, 35)
        except IOError:
            f_credit = ImageFont.load_default()
            
        credit_w = pilmoji.getsize(credit_text, font=f_credit)[0]
        # Position at bottom right of the video area (video ends at y=1100 - bottom_bar_height)
        # bottom_bar_height is 340. y_video_end = 1440 - 340 = 1100.
        credit_x = width - credit_w - 30
        credit_y = height - bottom_bar_height - 50
        
        # Draw stroke/shadow for visibility
        shadow_color = (0, 0, 0, 200)
        for offset in [(2,2), (-2,-2), (2,-2), (-2,2), (0,2), (2,0), (-2,0), (0,-2)]:
            pilmoji.text((credit_x + offset[0], credit_y + offset[1]), credit_text, fill=shadow_color, font=f_credit)
        pilmoji.text((credit_x, credit_y), credit_text, fill=white, font=f_credit)
        
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
