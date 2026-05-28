import os, sys, io, json, traceback
LOG = open("dumps/template_match_log.txt", "w", encoding="utf-8")
def log(msg):
    LOG.write(msg + "\n")
    LOG.flush()

try:
    log("Step 1: Importing libraries...")
    import numpy as np
    from PIL import Image, ImageFont, ImageDraw
    from pathlib import Path
    log("  OK")

    log("Step 2: Finding font...")
    font_path = None
    for p in ["C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/meiryo.ttc"]:
        if os.path.exists(p):
            font_path = p
            break
    log(f"  Font: {font_path}")

    log("Step 3: Building SJIS character list...")
    chars = []
    for c in range(0x20, 0x7F): chars.append(chr(c))
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
    seen = set(); unique = []
    for c in chars:
        if c not in seen: seen.add(c); unique.append(c)
    chars = unique
    log(f"  {len(chars)} reference characters")

    log("Step 4: Loading game glyphs...")
    glyphs = {}
    gdir = Path("dumps/glyphs")
    for gf in sorted(gdir.glob("glyph_*.png")):
        idx = int(gf.stem.split("_")[1])
        img = Image.open(gf).convert("L").resize((12, 12), Image.NEAREST)
        glyphs[idx] = (np.array(img) < 128).astype(np.uint8)
    log(f"  {len(glyphs)} glyphs loaded")

    log("Step 5: Rendering references and matching (size=10)...")
    font = ImageFont.truetype(font_path, 10)
    refs = {}
    for i, char in enumerate(chars):
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
        if (i+1) % 1000 == 0:
            log(f"  Rendered {i+1}/{len(chars)} refs ({len(refs)} valid)")
    log(f"  Total valid refs: {len(refs)}")

    log("Step 6: Matching glyphs against references...")
    results = {}
    for count, idx in enumerate(sorted(glyphs.keys())):
        g = glyphs[idx]
        if g.sum() == 0:
            results[idx] = (" ", 1.0)
        else:
            best_c, best_s = "?", 0
            for char, ref in refs.items():
                s = float(np.sum(g == ref)) / 144.0
                if s > best_s:
                    best_s = s
                    best_c = char
            results[idx] = (best_c, best_s)
        if (count+1) % 50 == 0:
            c, s = results[idx]
            log(f"  Matched {count+1}/{len(glyphs)} | glyph {idx} -> '{c}' ({s:.3f})")

    log("Step 7: Saving results...")
    output = {}
    for idx, (char, score) in sorted(results.items()):
        output[str(idx)] = {"char": char, "score": round(score, 4)}
    
    os.makedirs("data", exist_ok=True)
    with open("data/glyph_map_template.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    scores = [v[1] for v in results.values()]
    log(f"\n=== RESULTS ===")
    log(f"Total: {len(output)} glyphs")
    log(f">=95%: {sum(1 for s in scores if s >= 0.95)}")
    log(f">=90%: {sum(1 for s in scores if s >= 0.90)}")
    log(f">=85%: {sum(1 for s in scores if s >= 0.85)}")
    log(f"<80%:  {sum(1 for s in scores if s < 0.80)}")

    log(f"\nFirst 50 mappings:")
    for i in range(min(50, len(output))):
        r = results.get(i)
        if r: log(f"  glyph_{i:04d} -> '{r[0]}' ({r[1]:.3f})")

    log(f"\nLowest 20 confidence:")
    for idx, (c, s) in sorted(results.items(), key=lambda x: x[1][1])[:20]:
        log(f"  glyph_{idx:04d} -> '{c}' ({s:.3f})")

    log(f"\nSaved to data/glyph_map_template.json")
    log("DONE")

except Exception as e:
    log(f"ERROR: {e}")
    log(traceback.format_exc())

LOG.close()
