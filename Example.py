from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def generate_card(text="99/100", input_path="Edited.png", output_path="result.png"):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return

    # 1. Open background
    base = Image.open(input_path).convert("RGBA")
    
    # 2. Setup font
    font_size = 93
    font = None
    
    # Путь к текущей директории проекта
    current_dir = Path(__file__).parent
    
    # Список возможных названий файла шрифта
    font_names = ["Inter_18pt-SemiBold.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf"]
    
    font_paths = []
    # Сначала ищем в assets/fonts
    for name in font_names:
        font_paths.append(str(current_dir / "assets" / "fonts" / name))
    
    # Потом ищем системные шрифты (для подстраховки)
    font_paths.extend([
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ])
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                print(f"Successfully loaded font: {path}")
                break
        except:
            continue
            
    if font is None:
        print("WARNING: Fonts not found! Using default small font.")
        font = ImageFont.load_default()

    # 3. Create a text image
    # Use a transparent background
    txt_img = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_img)
    
    # Draw text in BLACK
    d.text((10, 10), text, font=font, fill=(0, 0, 0, 255))
    
    # 4. Rotate
    rotated = txt_img.rotate(2.76, resample=Image.BICUBIC, expand=True)
    
    # 5. Paste onto base
    # Coordinates from your working example
    base.paste(rotated, (1000, 460), rotated)
    
    # 6. Save
    base.convert("RGB").save(output_path)
    print(f"Success! Saved to {output_path} with Inter font.")

if __name__ == "__main__":
    generate_card()
