from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def generate_health_card(score: int, output_path: str = "temp_card.png"):
    """
    Generates a card with the health score (e.g. "56/100") using the Edited.png template.
    """
    # Base path for the project
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "Edited.png"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Template image not found at {input_path}")

    # 1. Open background
    base = Image.open(input_path).convert("RGBA")
    
    # 2. Setup font
    font_size = 95
    # Try multiple common font paths on Windows
    font_paths = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        str(base_dir / "Inter-SemiBold.ttf")
    ]
    
    font = None
    for path in font_paths:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        except:
            continue
            
    if font is None:
        font = ImageFont.load_default()

    # 3. Create a transparent layer for the text
    text = f"{score}/100"
    txt_layer = Image.new("RGBA", (600, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_layer)
    
    # Draw text (White color as requested/implied)
    d.text((10, 10), text, font=font, fill=(255, 255, 255, 255))
    
    # 4. Rotate (Figma 2.76 deg clockwise = Pillow -2.76 deg)
    rotated_txt = txt_layer.rotate(2.76, resample=Image.BICUBIC, expand=True)
    
    # 5. Paste onto base at x: 1020, y: 502
    base.paste(rotated_txt, (1020, 465), rotated_txt)
    
    # 6. Save
    base.convert("RGB").save(output_path)
    return output_path
