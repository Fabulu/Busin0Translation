import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image, ImageOps

GLYPH_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"

def prepare_large(img_path, target_size=192, padding=48):
    """Much larger upscale with more padding"""
    img = Image.open(img_path).convert("L")
    # Invert so we have white text on black? No, keep black on white for OCR
    img = img.resize((target_size, target_size), Image.NEAREST)
    padded = Image.new("L", (target_size + padding*2, target_size + padding*2), 255)
    padded.paste(img, (padding, padding))
    return np.array(padded)

# Try feeding a row of the grid to EasyOCR
print("Testing EasyOCR on grid row...")
import easyocr
reader = easyocr.Reader(["ja", "en"], gpu=False)

# Test: read a row from the composite grid
grid = Image.open(os.path.join(GLYPH_DIR, "_grid_composite.png")).convert("L")
# Row with known ASCII chars (glyph 37=A is in row 1, col 16)
# Row 1: glyphs 21-41 -> col 0-20
# So row 1 contains digits 1-9, :, ;, <, =, >, ?, @, A, B, C, D
row_idx = 1
y_start = row_idx * 12 * 4  # 48 pixels per glyph
row_img = grid.crop((0, y_start, grid.width, y_start + 12 * 4))
row_arr = np.array(row_img)
print(f"Row image shape: {row_arr.shape}")

result = reader.readtext(row_arr, detail=1)
print(f"Row OCR results ({len(result)} detections):")
for r in result:
    print(f"  bbox={r[0]}, text='{r[1]}', conf={r[2]:.4f}")

# Try row 2
row_idx = 2
y_start = row_idx * 12 * 4
row_img = grid.crop((0, y_start, grid.width, y_start + 12 * 4))
row_arr = np.array(row_img)
result2 = reader.readtext(row_arr, detail=1)
print(f"\nRow 2 OCR results ({len(result2)} detections):")
for r in result2:
    print(f"  bbox={r[0]}, text='{r[1]}', conf={r[2]:.4f}")

# Try bigger individual glyph
print("\nTrying bigger individual glyphs (192px)...")
for gi in [37, 38, 39, 40, 69, 70, 100, 200, 300, 500]:
    gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")
    img_arr = prepare_large(gpath)
    t0 = time.time()
    ocr_out = reader.readtext(img_arr, detail=1)
    dt = time.time() - t0
    if ocr_out:
        text = ocr_out[0][1]
        conf = ocr_out[0][2]
        print(f"  Glyph {gi}: '{text}' conf={conf:.4f} ({dt:.2f}s)")
    else:
        print(f"  Glyph {gi}: no result ({dt:.2f}s)")

print("Done.")
