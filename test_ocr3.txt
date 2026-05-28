import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GLYPH_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"

# Strategy: upscale glyphs to 256x256 with thick borders and padding
# Use bilinear for smoother edges

def prepare_mega(img_path, target_size=256, padding=64):
    img = Image.open(img_path).convert("L")
    # Upscale with LANCZOS for smooth edges
    img = img.resize((target_size, target_size), Image.LANCZOS)
    # Threshold to pure B/W
    arr = np.array(img)
    arr = np.where(arr < 200, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "L")
    padded = Image.new("L", (target_size + padding*2, target_size + padding*2), 255)
    padded.paste(img, (padding, padding))
    return np.array(padded)

import easyocr
reader = easyocr.Reader(["ja", "en"], gpu=False)
print("EasyOCR loaded.")

# Try with paragraph=True and larger images
print("Testing with 256px + LANCZOS + threshold...")
for gi in [37, 38, 39, 40, 41, 69, 70, 71, 100, 150, 200, 300, 400, 500, 600, 700]:
    gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")
    if not os.path.exists(gpath):
        continue
    img_arr = prepare_mega(gpath)
    t0 = time.time()
    ocr_out = reader.readtext(img_arr, detail=1, paragraph=False, min_size=5, text_threshold=0.3, low_text=0.2)
    dt = time.time() - t0
    if ocr_out:
        text = ocr_out[0][1]
        conf = ocr_out[0][2]
        print(f"  Glyph {gi}: '{text}' conf={conf:.4f} ({dt:.2f}s)")
    else:
        print(f"  Glyph {gi}: no result ({dt:.2f}s)")

# Try full page approach: 10x upscale of grid sections
print("\nTesting full grid section at 10x scale...")
grid = Image.open(os.path.join(GLYPH_DIR, "_grid_composite.png")).convert("L")
# Get rows 0-5 (first 6 rows = ASCII area)
section = grid.crop((0, 0, grid.width, 6 * 12 * 4))
# Upscale 3x more
section_big = section.resize((section.width * 3, section.height * 3), Image.LANCZOS)
# Threshold
arr = np.array(section_big)
arr = np.where(arr < 200, 0, 255).astype(np.uint8)
result = reader.readtext(arr, detail=1, paragraph=False, min_size=5, text_threshold=0.3, low_text=0.2)
print(f"Grid section OCR: {len(result)} detections")
for r in result:
    print(f"  '{r[1]}' conf={r[2]:.4f}")

print("Done.")
