import os
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def create_text_overlay(text: str, output_path: str, max_width: int = 1000, max_height: int = 340):
    """
    Renders multiline text (with emojis) to a transparent PNG.
    The text is centered both horizontally and vertically.
    """
    # Create a transparent image
    img = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.exists(font_path):
        # Fallback to standard if missing
        font_path = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
        
    font_size = 55
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size and positioning
    # Pillow's textbbox handles newlines if multiline is used, but pilmoji might have issues with multiline centering.
    # It's safer to draw line by line to guarantee perfect centering.
    
    lines = text.strip().split('\n')
    
    # Calculate total height
    line_heights = []
    for line in lines:
        bbox = font.getbbox(line)
        if bbox:
            line_heights.append(bbox[3] - bbox[1])
        else:
            line_heights.append(font_size)
            
    line_spacing = 20
    total_height = sum(line_heights) + (len(lines) - 1) * line_spacing
    
    y_text = (max_height - total_height) / 2
    
    with Pilmoji(img) as pilmoji:
        for i, line in enumerate(lines):
            line = line.strip()
            # Get width of current line
            bbox = font.getbbox(line)
            if bbox:
                line_width = bbox[2] - bbox[0]
            else:
                line_width = 0
                
            x_text = (max_width - line_width) / 2
            
            # Draw the text with Pilmoji to support emojis
            pilmoji.text((x_text, y_text), line, fill=(255, 255, 0, 255), font=font)
            
            y_text += line_heights[i] + line_spacing
            
    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    # Test execution
    test_text = "🔥 38 साल की शादी का ऐसा राज...\n😲 सच्चाई जानकर आप भी हैरान रह जाएंगे!"
    create_text_overlay(test_text, "temp/test_overlay.png")
