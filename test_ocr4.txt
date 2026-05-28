import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image
import easyocr

GLYPH_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"

# Try using EasyOCR's recognizer directly, bypassing CRAFT detector
reader = easyocr.Reader(["ja", "en"], gpu=False)
print("Loaded.")

# Access the recognizer directly
recognizer = reader.recognizer
converter = reader.converter

def recognize_single_char(img_arr):
    """Feed image directly to recognition model"""
    from easyocr.utils import get_image_list
    import torch
    from torch.autograd import Variable

    # Convert to proper format
    img = Image.fromarray(img_arr).convert("L")
    # Recognition model expects specific dimensions
    # Typical: height=64, variable width
    h = 64
    w = max(int(img.width * h / img.height), 1)
    img_resized = img.resize((w, h), Image.LANCZOS)

    result = reader.recognize(img_arr, horizontal_list=[[0, 0, img_arr.shape[1], img_arr.shape[0]]], free_list=[])
    return result

def prepare_char(img_path, target_h=64, padding=8):
    img = Image.open(img_path).convert("L")
    # Scale to height 64
    scale = target_h / img.height
    w = max(int(img.width * scale), 1)
    img = img.resize((w, target_h), Image.LANCZOS)
    # Threshold
    arr = np.array(img)
    arr = np.where(arr < 200, 0, 255).astype(np.uint8)
    # Add padding
    padded = np.full((target_h + padding*2, w + padding*2), 255, dtype=np.uint8)
    padded[padding:padding+target_h, padding:padding+w] = arr
    return padded

print("Testing direct recognition...")
for gi in [37, 38, 39, 40, 41, 42, 69, 70, 71, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800]:
    gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")
    if not os.path.exists(gpath):
        continue
    img = Image.open(gpath).convert("L")
    arr = np.array(img)
    # Check if empty
    if np.all(arr >= 250):
        print(f"  Glyph {gi}: EMPTY")
        continue

    img_arr = prepare_char(gpath)
    try:
        # Use reader.recognize with bounding box covering full image
        h, w = img_arr.shape[:2]
        result = reader.recognize(img_arr, horizontal_list=[[0, 0, w, h]], free_list=[])
        if result:
            for bbox, text, conf in result:
                print(f"  Glyph {gi}: '{text}' conf={conf:.4f}")
        else:
            print(f"  Glyph {gi}: no result from recognize")
    except Exception as e:
        print(f"  Glyph {gi}: error: {e}")

print("Done.")
