import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GLYPH_DIR = "dumps/glyphs"
OUTPUT = "data/glyph_map_dual_ocr.json"
os.makedirs("data", exist_ok=True)

from PIL import Image, ImageOps
import numpy as np

print("Loading OCR engines (EasyOCR + RapidOCR, skipping PaddleOCR)...")

import easyocr
easy_reader = easyocr.Reader(["ja"], gpu=False, verbose=False)
print("  EasyOCR loaded")

from rapidocr_onnxruntime import RapidOCR
rapid_engine = RapidOCR()
print("  RapidOCR loaded")

def prepare_glyph(path, scale=6):
    img = Image.open(path).convert("L")
    w, h = img.size
    img = img.resize((w * scale, h * scale), Image.NEAREST)
    pad = 16
    padded = Image.new("L", (img.width + pad*2, img.height + pad*2), 255)
    img_inv = ImageOps.invert(img)
    padded.paste(img_inv, (pad, pad))
    return padded

def ocr_easy(img):
    try:
        arr = np.array(img)
        results = easy_reader.readtext(arr, detail=1)
        if results:
            return results[0][1], results[0][2]
    except: pass
    return "", 0.0

def ocr_rapid(img):
    try:
        arr = np.array(img)
        result, _ = rapid_engine(arr)
        if result:
            return result[0][1], result[0][2]
    except: pass
    return "", 0.0

results = {}
total = 882

for i in range(total):
    path = os.path.join(GLYPH_DIR, f"glyph_{i:04d}.png")
    if not os.path.exists(path):
        continue
    
    img = prepare_glyph(path)
    
    e_text, e_conf = ocr_easy(img)
    r_text, r_conf = ocr_rapid(img)
    
    if e_text == r_text and e_text:
        consensus = e_text
        confidence = 1.0
    elif e_conf > r_conf and e_text:
        consensus = e_text
        confidence = 0.5
    elif r_text:
        consensus = r_text
        confidence = 0.5
    else:
        consensus = ""
        confidence = 0.0
    
    results[str(i)] = {
        "easyocr": e_text,
        "easyocr_conf": round(e_conf, 3),
        "rapidocr": r_text,
        "rapidocr_conf": round(r_conf, 3),
        "consensus": consensus,
        "confidence": confidence,
    }
    
    if (i + 1) % 25 == 0:
        agreed = sum(1 for r in results.values() if r["confidence"] >= 1.0)
        print(f"  {i+1}/{total} | agreed={agreed} | last: [{i}] e={e_text!r} r={r_text!r}")
        sys.stdout.flush()

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

agreed = sum(1 for r in results.values() if r["confidence"] >= 1.0)
any_hit = sum(1 for r in results.values() if r["consensus"])
print(f"\nDone! {total} glyphs")
print(f"  Both agree: {agreed}")
print(f"  Any result: {any_hit}")
print(f"  No result: {total - any_hit}")
print(f"Saved to: {OUTPUT}")
