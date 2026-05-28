import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

GLYPH_DIR = Path("dumps/glyphs")
OUTPUT = Path("data/glyph_map_template.json")

# Find Japanese font
font_path = None
for p in ["C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/msmincho.ttc"]:
    if os.path.exists(p):
        font_path = p
        break
print(f"Using font: {font_path}")

# Build SJIS character list
chars = []
for c in range(0x20, 0x7F): chars.append(chr(c))  # ASCII
for high in range(0x81, 0xA0):
    for low in range(0x40, 0xFD):
        if low == 0x7F: continue
        try: chars.append(bytes([high, low]).decode("shift_jis"))
        except: pass
for high in range(0xE0, 0xF0):
    for low in range(0x40, 0xFD):
        if low == 0x7F: continue
        try: chars.append(bytes([high, low]).decode("shift_jis"))
        except: pass
# Deduplicate
seen = set(); unique_chars = []
for c in chars:
    if c not in seen: seen.add(c); unique_chars.append(c)
chars = unique_chars
print(f"Reference characters: {len(chars)}")

# Load game glyphs
glyphs = {}
for gf in sorted(GLYPH_DIR.glob("glyph_*.png")):
    idx = int(gf.stem.split("_")[1])
    img = Image.open(gf).convert("L").resize((12, 12), Image.NEAREST)
    glyphs[idx] = (np.array(img) < 128).astype(np.uint8)
print(f"Loaded {len(glyphs)} glyphs")

# Try font sizes
best_results = None
best_avg = 0
best_info = ""

for font_size in [10, 11, 12, 9, 8]:
    font = ImageFont.truetype(font_path, font_size)
    refs = {}
    for char in chars:
        img = Image.new("L", (12, 12), 255)
        draw = ImageDraw.Draw(img)
        try:
            bbox = font.getbbox(char)
            if bbox:
                x0, y0, x1, y1 = bbox
                ox = max(0, (12 - (x1-x0)) // 2 - x0)
                oy = max(0, (12 - (y1-y0)) // 2 - y0)
                draw.text((ox, oy), char, font=font, fill=0)
        except: continue
        arr = (np.array(img) < 128).astype(np.uint8)
        if arr.sum() > 0:
            refs[char] = arr
    
    # Match
    results = {}
    total = 0
    for idx in sorted(glyphs.keys()):
        g = glyphs[idx]
        if g.sum() == 0:
            results[idx] = (" ", 1.0)
            total += 1.0
            continue
        best_c, best_s = "?", 0
        for char, ref in refs.items():
            s = np.sum(g == ref) / 144.0
            if s > best_s:
                best_s = s
                best_c = char
        results[idx] = (best_c, best_s)
        total += best_s
    
    avg = total / len(results)
    high = sum(1 for _, s in results.values() if s >= 0.90)
    info = f"size={font_size}, avg={avg:.4f}, >=90%={high}/{len(results)}"
    print(f"  {info}")
    sys.stdout.flush()
    
    if avg > best_avg:
        best_avg = avg
        best_results = results
        best_info = info

print(f"\nBest: {best_info}")

# Save
output = {}
for idx, (char, score) in sorted(best_results.items()):
    output[str(idx)] = {"char": char, "score": round(score, 4)}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

scores = [v[1] for v in best_results.values()]
print(f"\nTotal: {len(output)} glyphs mapped")
print(f">=95%: {sum(1 for s in scores if s >= 0.95)}")
print(f">=90%: {sum(1 for s in scores if s >= 0.90)}")
print(f">=85%: {sum(1 for s in scores if s >= 0.85)}")
print(f"<80%: {sum(1 for s in scores if s < 0.80)}")

print("\nFirst 30:")
for i in range(min(30, len(output))):
    r = best_results.get(i)
    if r: print(f"  glyph_{i:04d} -> '{r[0]}' ({r[1]:.3f})")

print("\nLowest 15:")
for idx, (c, s) in sorted(best_results.items(), key=lambda x: x[1][1])[:15]:
    print(f"  glyph_{idx:04d} -> '{c}' ({s:.3f})")

print(f"\nSaved to {OUTPUT}")
