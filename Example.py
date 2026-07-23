from PIL import Image, ImageDraw, ImageFont
import os

def generate_card(text="39/100", input_path="Edited.png", output_path="result.png"):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return

    # 1. Open background
    base = Image.open(input_path).convert("RGBA")
    
    # 2. Setup font
    font_size = 95 # Slightly larger
    font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # 3. Create a text image
    # Use a colored background temporarily for the text layer to see it
    txt_img = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_img)
    
    # Draw text in BLACK for visibility test
    d.text((10, 10), text, font=font, fill=(0, 0, 0, 255))
    
    # 4. Rotate
    rotated = txt_img.rotate(2.76, resample=Image.BICUBIC, expand=True)
    
    # 5. Paste onto base
    # Paste at 1020, 502
    base.paste(rotated, (1020, 465), rotated)
    
    # 6. Save
    base.convert("RGB").save(output_path)
    print(f"Success! Saved to {output_path}. TEST: TEXT IS BLACK.")

if __name__ == "__main__":
    generate_card()
