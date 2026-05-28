import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

GLYPH_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"

def prepare_for_ocr(img_path, target_size=96, padding=16):
    img = Image.open(img_path).convert("L")
    img = img.resize((target_size, target_size), Image.NEAREST)
    padded = Image.new("L", (target_size + padding*2, target_size + padding*2), 255)
    padded.paste(img, (padding, padding))
    return np.array(padded)

# Test with RapidOCR first
print("Testing RapidOCR...")
try:
    from rapidocr_onnxruntime import RapidOCR
    rapid = RapidOCR()

    # Test on a few known glyphs
    test_indices = [37, 38, 39, 69, 70, 71, 100, 150, 200, 300, 400, 500]
    for gi in test_indices:
        gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")
        img_arr = prepare_for_ocr(gpath)
        t0 = time.time()
        result, elapse = rapid(img_arr)
        dt = time.time() - t0
        if result:
            text = result[0][1]
            conf = result[0][2]
            print(f"  Glyph {gi}: '{text}' conf={conf:.4f} ({dt:.2f}s)")
        else:
            print(f"  Glyph {gi}: no result ({dt:.2f}s)")
    print("RapidOCR test done.")
except Exception as e:
    print(f"RapidOCR error: {e}")
    import traceback
    traceback.print_exc()

# Test EasyOCR on same glyphs
print("\nTesting EasyOCR...")
try:
    import easyocr
    reader = easyocr.Reader(["ja", "en"], gpu=False)

    test_indices = [37, 38, 39, 69, 70, 71, 100, 150, 200, 300]
    for gi in test_indices:
        gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")
        img_arr = prepare_for_ocr(gpath)
        t0 = time.time()
        ocr_out = reader.readtext(img_arr, detail=1)
        dt = time.time() - t0
        if ocr_out:
            text = ocr_out[0][1]
            conf = ocr_out[0][2]
            print(f"  Glyph {gi}: '{text}' conf={conf:.4f} ({dt:.2f}s)")
        else:
            print(f"  Glyph {gi}: no result ({dt:.2f}s)")
    print("EasyOCR test done.")
except Exception as e:
    print(f"EasyOCR error: {e}")
