import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import numpy as np
from PIL import Image

# Known ASCII mapping from EXE 0x3C0870
KNOWN_MAP = {
    1: ' ',
    5: '!', 6: '"', 7: '#', 8: '$', 9: '%', 10: '&', 11: "'",
    12: '(', 13: ')', 14: '*', 15: '+', 16: ',', 17: '-', 18: '.', 19: '/',
    20: '0', 21: '1', 22: '2', 23: '3', 24: '4', 25: '5', 26: '6', 27: '7',
    28: '8', 29: '9', 30: ':', 31: ';', 32: '<', 33: '=', 34: '>', 35: '?',
    36: '@', 37: 'A', 38: 'B', 39: 'C', 40: 'D', 41: 'E', 42: 'F', 43: 'G',
    44: 'H', 45: 'I', 46: 'J', 47: 'K', 48: 'L', 49: 'M', 50: 'N', 51: 'O',
    52: 'P', 53: 'Q', 54: 'R', 55: 'S', 56: 'T', 57: 'U', 58: 'V', 59: 'W',
    60: 'X', 61: 'Y', 62: 'Z', 63: '[', 64: '\\', 65: ']', 66: '^', 67: '_',
    68: '`', 69: 'a', 70: 'b', 71: 'c', 72: 'd', 73: 'e', 74: 'f', 75: 'g',
    76: 'h', 77: 'i', 78: 'j', 79: 'k', 80: 'l', 81: 'm', 82: 'n', 83: 'o',
    84: 'p', 85: 'q', 86: 'r', 87: 's',
}

GLYPH_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"
OUT_JSON = r"C:\Programmieren\wizardrytranslation\data\glyph_map_ocr.json"
TOTAL_GLYPHS = 882

def is_empty_glyph(img_path):
    img = Image.open(img_path).convert("L")
    arr = np.array(img)
    return np.all(arr >= 250)

def prepare_for_ocr(img_path, target_size=96, padding=16):
    img = Image.open(img_path).convert("L")
    img = img.resize((target_size, target_size), Image.NEAREST)
    padded = Image.new("L", (target_size + padding*2, target_size + padding*2), 255)
    padded.paste(img, (padding, padding))
    return np.array(padded)

print("Loading EasyOCR...")
import easyocr
reader = easyocr.Reader(["ja", "en"], gpu=False)
print("EasyOCR loaded.")

results = {}

for gi in range(TOTAL_GLYPHS):
    gpath = os.path.join(GLYPH_DIR, f"glyph_{gi:04d}.png")

    if gi in KNOWN_MAP:
        results[str(gi)] = {
            "char": KNOWN_MAP[gi],
            "source": "exe_mapping",
            "confidence": 1.0
        }
        if gi % 100 == 0:
            print(f"Glyph {gi}: known = {repr(KNOWN_MAP[gi])}")
        continue

    if not os.path.exists(gpath):
        continue

    if is_empty_glyph(gpath):
        results[str(gi)] = {
            "char": "",
            "source": "empty",
            "confidence": 1.0
        }
        continue

    img_arr = prepare_for_ocr(gpath)
    try:
        ocr_out = reader.readtext(img_arr, detail=1)
        if ocr_out and len(ocr_out) > 0:
            text = ocr_out[0][1]
            conf = float(ocr_out[0][2])
            results[str(gi)] = {
                "char": text,
                "source": "easyocr",
                "confidence": round(conf, 4)
            }
        else:
            results[str(gi)] = {
                "char": "?",
                "source": "easyocr_no_result",
                "confidence": 0.0
            }
    except Exception as e:
        results[str(gi)] = {
            "char": "?",
            "source": f"error: {e}",
            "confidence": 0.0
        }

    if gi % 50 == 0:
        ch = results[str(gi)]["char"]
        cf = results[str(gi)]["confidence"]
        print(f"Glyph {gi}: OCR = {repr(ch)} (conf={cf})")

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

total = len(results)
known = sum(1 for v in results.values() if v["source"] == "exe_mapping")
ocr_ok = sum(1 for v in results.values() if v["source"] == "easyocr" and v["confidence"] > 0.5)
empty = sum(1 for v in results.values() if v["source"] == "empty")
low_conf = sum(1 for v in results.values() if v["source"] == "easyocr" and v["confidence"] <= 0.5)
no_result = sum(1 for v in results.values() if v["source"] == "easyocr_no_result")

print(f"\nSummary:")
print(f"  Total glyphs processed: {total}")
print(f"  Known from EXE: {known}")
print(f"  OCR high confidence (>0.5): {ocr_ok}")
print(f"  OCR low confidence: {low_conf}")
print(f"  OCR no result: {no_result}")
print(f"  Empty glyphs: {empty}")
print(f"Done. Saved to {OUT_JSON}")
