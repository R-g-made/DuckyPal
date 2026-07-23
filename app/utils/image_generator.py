from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def generate_health_card(text="99/100", output_path="temp_card.png"):
    # Путь к шаблону в корне проекта
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "Edited.png"
    
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return

    # 1. Open background
    base = Image.open(input_path).convert("RGBA")
    
    # 2. Setup font
    font_size = 93
    font = None
    
    # Приоритетный путь к твоему шрифту Inter в папке assets
    # Добавил поиск разных вариантов названия файла
    font_names = ["Inter_18pt-SemiBold.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf"]
    
    font_paths = []
    for name in font_names:
        font_paths.append(str(base_dir / "assets" / "fonts" / name))
    
    font_paths.extend([
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ])
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        except:
            continue
            
    if font is None:
        print("WARNING: Inter font not found in assets/fonts/! Using default small font.")
        font = ImageFont.load_default()

    # 3. Create a text image (как в твоем Example.py)
    txt_img = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_img)
    
    # Рисуем текст черным цветом
    d.text((10, 10), text, font=font, fill=(0, 0, 0, 255))
    
    # 4. Rotate
    rotated = txt_img.rotate(2.76, resample=Image.BICUBIC, expand=True)
    
    # 5. Paste onto base (координаты из твоего рабочего примера)
    base.paste(rotated, (1000, 460), rotated)
    
    # 6. Save
    base.convert("RGB").save(output_path)
    return output_path
