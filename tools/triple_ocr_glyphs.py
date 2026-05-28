import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GLYPH_DIR = "dumps/glyphs"
OUTPUT = "data/glyph_map_triple_ocr.json"
os.makedirs("data", exist_ok=True)

from PIL import Image
import numpy as np

# Load known ASCII mapping from EXE (glyph indices 1-93 -> ASCII 0x20-0x73)
ASCII_MAP = {}
# space=1, then with gaps: 5=!, 6=", etc.
# We'll fill these in from the EXE data we already have
# For now, mark glyphs 0-93 as "ascii_range"

print("Loading OCR engines...")

# --- EasyOCR ---
try:
    import easyocr
    easy_reader = easyocr.Reader(["ja"], gpu=False, verbose=False)
    print("  EasyOCR loaded")
except Exception as e:
    easy_reader = None
    print(f"  EasyOCR FAILED: {e}")

# --- RapidOCR ---
try:
    from rapidocr_onnxruntime import RapidOCR
    rapid_engine = RapidOCR()
    print("  RapidOCR loaded")
except Exception as e:
    rapid_engine = None
    print(f"  RapidOCR FAILED: {e}")

# --- PaddleOCR ---
try:
    from paddleocr import PaddleOCR
    paddle_engine = PaddleOCR(use_angle_cls=False, lang="japan", show_log=False, use_gpu=False)
    print("  PaddleOCR loaded")
except Exception as e:
    paddle_engine = None
    print(f"  PaddleOCR FAILED: {e}")

def prepare_glyph(path, scale=8):
    """Load glyph PNG, upscale, add padding for better OCR."""
    img = Image.open(path).convert("L")
    w, h = img.size
    # Upscale with nearest neighbor
    img = img.resize((w * scale, h * scale), Image.NEAREST)
    # Add white padding
    pad = 20
    padded = Image.new("L", (img.width + pad*2, img.height + pad*2), 255)
    # Invert if needed (OCR expects dark text on light background)
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    if avg > 128:  # light background
        padded.paste(img, (pad, pad))
    else:  # dark background - invert
        from PIL import ImageOps
        img_inv = ImageOps.invert(img)
        padded.paste(img_inv, (pad, pad))
    return padded

def ocr_easyocr(img):
    if easy_reader is None: return ""
    try:
        arr = np.array(img)
        results = easy_reader.readtext(arr, detail=1)
        if results:
            return results[0][1]
    except: pass
    return ""

def ocr_rapidocr(img):
    if rapid_engine is None: return ""
    try:
        arr = np.array(img)
        result, _ = rapid_engine(arr)
        if result:
            return result[0][1]
    except: pass
    return ""

def ocr_paddleocr(img):
    if paddle_engine is None: return ""
    try:
        arr = np.array(img)
        result = paddle_engine.ocr(arr, cls=False)
        if result and result[0]:
            return result[0][0][1][0]
    except: pass
    return ""

results = {}
total = 882
batch_size = 50

for i in range(total):
    path = os.path.join(GLYPH_DIR, f"glyph_{i:04d}.png")
    if not os.path.exists(path):
        continue
    
    img = prepare_glyph(path)
    
    e = ocr_easyocr(img)
    r = ocr_rapidocr(img)
    p = ocr_paddleocr(img)
    
    # Consensus: if 2+ agree, use that; otherwise take the first non-empty
    consensus = ""
    confidence = 0
    votes = [x for x in [e, r, p] if x]
    
    if len(votes) >= 2:
        from collections import Counter
        counts = Counter(votes)
        top = counts.most_common(1)[0]
        consensus = top[0]
        confidence = top[1] / 3.0  # 0.33, 0.67, or 1.0
    elif len(votes) == 1:
        consensus = votes[0]
        confidence = 0.33
    
    results[str(i)] = {
        "easyocr": e,
        "rapidocr": r,
        "paddleocr": p,
        "consensus": consensus,
        "confidence": confidence,
    }
    
    if (i + 1) % batch_size == 0:
        agreed = sum(1 for r in results.values() if r["confidence"] >= 0.67)
        print(f"  Processed {i+1}/{total} glyphs, {agreed} with 2+ agreement")

# Save
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Summary
agreed_2 = sum(1 for r in results.values() if r["confidence"] >= 0.67)
agreed_3 = sum(1 for r in results.values() if r["confidence"] >= 1.0)
any_hit = sum(1 for r in results.values() if r["consensus"])
print(f"\nDone! {total} glyphs processed")
print(f"  Any OCR result: {any_hit}")
print(f"  2+ engines agree: {agreed_2}")
print(f"  All 3 agree: {agreed_3}")
print(f"  No result: {total - any_hit}")
print(f"Saved to: {OUTPUT}")
