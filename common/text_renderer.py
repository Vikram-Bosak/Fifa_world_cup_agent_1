import os
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def create_text_overlay(text: str, output_path: str, max_width: int = 1000, max_height: int = 340):
    """
    Renders the new 3-part layout (Title -> Icons -> Line -> Story) to a transparent PNG.
    Colors are #000000 (Black).
    """
    img = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.exists(font_path):
        font_path = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
        
    try:
        font_title = ImageFont.truetype(font_path, 65)
        font_story = ImageFont.truetype(font_path, 40)
    except IOError:
        font_title = ImageFont.load_default()
        font_story = ImageFont.load_default()

    lines = text.strip().split('\n')
    title = lines[0].strip() if len(lines) > 0 else ""
    story = " ".join(lines[1:]).strip() if len(lines) > 1 else ""

    # Calculate Y positions to center everything vertically
    # Title height
    bbox_t = font_title.getbbox(title) if title else (0,0,0,0)
    h_title = bbox_t[3] - bbox_t[1] if title else 0
    
    # Icons height (3 rectangles)
    h_icons = 30
    
    # Line height
    h_line = 4
    
    # Story height (we might need to wrap it if it's too long)
    import textwrap
    # Roughly 50 characters per line for 1000px width at font size 40
    story_lines = textwrap.wrap(story, width=45) if story else []
    
    h_story_total = 0
    story_bboxes = []
    for s_line in story_lines:
        bbox_s = font_story.getbbox(s_line)
        h_s = bbox_s[3] - bbox_s[1]
        story_bboxes.append((s_line, h_s, bbox_s[2] - bbox_s[0]))
        h_story_total += h_s + 10 # 10px spacing between story lines
        
    if story_bboxes:
        h_story_total -= 10 # remove last spacing
        
    # Total heights and gaps
    gap1 = 20 # between title and icons
    gap2 = 20 # between icons and line
    gap3 = 20 # between line and story
    
    total_height = h_title + gap1 + h_icons + gap2 + h_line + gap3 + h_story_total
    
    # Start Y to center vertically
    current_y = (max_height - total_height) / 2
    
    text_color = (0, 0, 0, 255) # Black
    
    with Pilmoji(img) as pilmoji:
        # 1. Draw Title
        if title:
            w_title = bbox_t[2] - bbox_t[0]
            x_title = (max_width - w_title) / 2
            pilmoji.text((x_title, current_y), title, fill=text_color, font=font_title)
            current_y += h_title + gap1
            
        # 2. Draw Icons (3 vertical rectangles)
        icon_w, icon_h = 10, h_icons
        icon_spacing = 15
        total_icon_w = (icon_w * 3) + (icon_spacing * 2)
        start_icon_x = (max_width - total_icon_w) / 2
        
        for i in range(3):
            ix = start_icon_x + i * (icon_w + icon_spacing)
            draw.rectangle([ix, current_y, ix + icon_w, current_y + icon_h], fill=text_color)
            
        current_y += h_icons + gap2
        
        # 3. Draw Horizontal Line
        line_width = max_width - 100 # 50px padding on each side
        x_line_start = 50
        draw.line([(x_line_start, current_y), (max_width - 50, current_y)], fill=text_color, width=h_line)
        
        current_y += h_line + gap3
        
        # 4. Draw Story
        if story_lines:
            for s_line, h_s, w_s in story_bboxes:
                x_story = (max_width - w_s) / 2
                pilmoji.text((x_story, current_y), s_line, fill=text_color, font=font_story)
                current_y += h_s + 10
                
    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    test_text = "ZLATAN'S WORLD CUP DEBUT 🌟\nA fearless 18-year-old stepped onto the world stage. The legend had just begun. 🔥"
    create_text_overlay(test_text, "temp/test_overlay.png")
