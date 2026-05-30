from PIL import Image, ImageDraw, ImageFont
import os

# Characters to test (avoiding backslash issues)
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
PUNCT = "!@#$%^&*()-_=+[]{}|;:,.<>/?`~"
CHARS = LOWER + UPPER + DIGITS + PUNCT + "'" + '"'

FONTS_TO_TRY = ["Consolas", "Courier New", "Arial", "Lucida Console", "Segoe UI", "Tahoma", "Verdana"]
SIZES = [5, 6, 7, 8, 9, 10]
TARGET_WIDTHS = [6, 7, 8]

def find_font(name, size):
    special = {
        "Consolas": "consola.ttf",
        "Courier New": "cour.ttf",
        "Arial": "arial.ttf",
        "Lucida Console": "lucon.ttf",
        "Segoe UI": "segoeui.ttf",
        "Tahoma": "tahoma.ttf",
        "Verdana": "verdana.ttf",
    }
    paths = []
    if name in special:
        paths.append("C:/Windows/Fonts/" + special[name])
    paths.append("C:/Windows/Fonts/" + name + ".ttf")
    paths.append("C:/Windows/Fonts/" + name.lower() + ".ttf")
    paths.append("C:/Windows/Fonts/" + name.replace(" ", "") + ".ttf")

    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return None

def measure_glyph_width(font, char):
    img = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), char, fill=255, font=font)
    pixels = img.load()
    max_x = 0
    found = False
    for x in range(30):
        for y in range(30):
            if pixels[x, y] > 0:
                max_x = max(max_x, x)
                found = True
    return max_x + 1 if found else 0

def measure_glyph_height(font, char):
    img = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), char, fill=255, font=font)
    pixels = img.load()
    max_y = 0
    found = False
    for y in range(30):
        for x in range(30):
            if pixels[x, y] > 0:
                max_y = max(max_y, y)
                found = True
    return max_y + 1 if found else 0

# ---- MAIN ANALYSIS ----
print("=" * 80)
print("HALFWIDTH FONT FEASIBILITY TEST")
print("=" * 80)

results = {}

for font_name in FONTS_TO_TRY:
    for size in SIZES:
        font = find_font(font_name, size)
        if font is None:
            continue

        widths = {}
        max_w = 0
        max_h = 0
        for ch in CHARS:
            w = measure_glyph_width(font, ch)
            h = measure_glyph_height(font, ch)
            widths[ch] = w
            max_w = max(max_w, w)
            max_h = max(max_h, h)

        results[(font_name, size)] = {
            "max_width": max_w,
            "max_height": max_h,
            "widths": widths,
            "font": font,
        }
        print(f"  Measured {font_name} @ {size}pt: max_w={max_w}, max_h={max_h}")

# Report
print()
hdr = f"{'Font':<18} {'Size':>4}  {'MaxW':>4}  {'MaxH':>4}  {'<=6px':>8}  {'<=7px':>8}  {'<=8px':>8}  Wide chars (>6px)"
print(hdr)
print("-" * len(hdr) + "-" * 20)

fit_results = {6: [], 7: [], 8: []}

for (font_name, size), data in sorted(results.items()):
    max_w = data["max_width"]
    max_h = data["max_height"]

    wide_6 = [ch for ch, w in data["widths"].items() if w > 6]
    wide_7 = [ch for ch, w in data["widths"].items() if w > 7]
    wide_8 = [ch for ch, w in data["widths"].items() if w > 8]

    fit6 = "YES" if len(wide_6) == 0 else "no(%d)" % len(wide_6)
    fit7 = "YES" if len(wide_7) == 0 else "no(%d)" % len(wide_7)
    fit8 = "YES" if len(wide_8) == 0 else "no(%d)" % len(wide_8)

    wide_sample = "".join(sorted(wide_6)[:15]) if wide_6 else ""

    print(f"{font_name:<18} {size:>4}  {max_w:>4}  {max_h:>4}  {fit6:>8}  {fit7:>8}  {fit8:>8}  {wide_sample}")

    for tw in TARGET_WIDTHS:
        wide = [ch for ch, w in data["widths"].items() if w > tw]
        if len(wide) == 0:
            fit_results[tw].append((font_name, size, max_w, max_h))

print()
print("=" * 80)
for tw in TARGET_WIDTHS:
    print()
    print("Font+size combos fitting ALL chars in %dpx width:" % tw)
    if fit_results[tw]:
        for fn, sz, mw, mh in fit_results[tw]:
            print("  %s @ %dpt  (max glyph: %dx%d)" % (fn, sz, mw, mh))
    else:
        print("  NONE")

# DETAILED WIDTH DISTRIBUTION
print()
print("=" * 80)
print("DETAILED WIDTH DISTRIBUTION (configs with max_width <= 10)")
print("=" * 80)

for (font_name, size), data in sorted(results.items(), key=lambda x: (x[1]["max_width"], x[0][1])):
    if data["max_width"] > 10:
        continue
    dist = {}
    for ch, w in data["widths"].items():
        dist.setdefault(w, []).append(ch)
    print()
    print("%s @ %dpt (max=%dpx, height=%dpx):" % (font_name, size, data["max_width"], data["max_height"]))
    for w in sorted(dist.keys()):
        chars = "".join(sorted(dist[w]))
        print("  %dpx wide (%2d chars): %s" % (w, len(dist[w]), chars))

# ---- GENERATE TEST ATLAS ----
print()
print("=" * 80)
print("GENERATING TEST ATLAS IMAGES")
print("=" * 80)

build_dir = "C:/Programmieren/wizardrytranslation/build"
run_dir = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"

def generate_atlas(font_name, size, cell_w, cell_h, label, outpath):
    font = find_font(font_name, size)
    if font is None:
        print("  Could not load %s for atlas" % font_name)
        return

    test_chars = LOWER + DIGITS + ".,:;!?'-/()@#$%"
    cols = 16
    rows = (len(test_chars) + cols - 1) // cols

    header_h = 20
    img_w = cols * cell_w + 2
    img_h = rows * cell_h + header_h + 2

    img = Image.new("RGB", (img_w, img_h), (32, 32, 32))
    draw = ImageDraw.Draw(img)

    try:
        hfont = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 10)
    except Exception:
        hfont = ImageFont.load_default()
    draw.text((2, 2), label, fill=(200, 200, 100), font=hfont)

    for i, ch in enumerate(test_chars):
        col = i % cols
        row = i // cols
        x = col * cell_w + 1
        y = row * cell_h + header_h + 1

        draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(80, 80, 80))
        draw.text((x, y), ch, fill=(255, 255, 255), font=font)

    img.save(outpath)
    print("  Saved: %s" % outpath)


# Comparison atlas
def generate_comparison_atlas(outpath):
    test_chars = LOWER + DIGITS + ".,:;!?'-/()@#$%"

    configs = []
    seen = set()

    # Collect all configs where max_width <= some threshold
    for tw in [6, 7, 8]:
        for (fn, sz), data in sorted(results.items(), key=lambda x: (-x[0][1], x[0][0])):
            if data["max_width"] <= tw:
                key = (fn, sz)
                if key not in seen:
                    seen.add(key)
                    configs.append((fn, sz, tw, data))

    # Add near-miss configs
    for (fn, sz), data in sorted(results.items(), key=lambda x: (x[1]["max_width"], -x[0][1])):
        if data["max_width"] in [7, 8, 9] and sz >= 6:
            key = (fn, sz)
            if key not in seen:
                seen.add(key)
                configs.append((fn, sz, data["max_width"], data))
        if len(configs) >= 20:
            break

    configs = configs[:15]

    row_height = 18
    header_h = 14
    margin = 4
    img_w = 600

    total_h = margin + len(configs) * (row_height + header_h + margin) + margin
    img = Image.new("RGB", (img_w, max(total_h, 100)), (24, 24, 24))
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 10)
    except Exception:
        label_font = ImageFont.load_default()

    y = margin
    for fn, sz, tw, data in configs:
        font = find_font(fn, sz)
        if font is None:
            continue

        label = "%s @%dpt (maxW=%dpx, fits %dpx cells)" % (fn, sz, data["max_width"], tw)
        draw.text((margin, y), label, fill=(180, 180, 80), font=label_font)
        y += header_h

        cell_w = tw + 1
        cell_h = row_height
        for i, ch in enumerate(test_chars):
            x = margin + i * cell_w
            if x + cell_w > img_w - margin:
                break
            draw.rectangle([x, y, x + tw, y + cell_h - 1], outline=(60, 60, 60))
            draw.text((x, y), ch, fill=(255, 255, 255), font=font)

        y += row_height + margin

    img.save(outpath)
    print("  Saved comparison atlas: %s" % outpath)


generate_comparison_atlas(build_dir + "/halfwidth_font_test.png")

# Individual best-case atlases
for tw in [6, 7, 8]:
    candidates = [(fn, sz, data) for (fn, sz), data in results.items() if data["max_width"] <= tw]
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        fn, sz, data = candidates[0]
        generate_atlas(fn, sz, tw, max(12, data["max_height"] + 2),
                       "%s@%dpt in %dpx cells" % (fn, sz, tw),
                       build_dir + "/halfwidth_font_%dpx.png" % tw)

# ---- MARKDOWN REPORT ----
md = []
md.append("# Halfwidth Font Feasibility Test")
md.append("Date: 2026-05-28\n")
md.append("## Question")
md.append("Can readable English text fit in 6 pixels wide per character?\n")
md.append("## Results Summary\n")
md.append("| Font | Size | MaxW | MaxH | <=6px | <=7px | <=8px |")
md.append("|------|------|------|------|-------|-------|-------|")

for (font_name, size), data in sorted(results.items()):
    mw = data["max_width"]
    mh = data["max_height"]
    w6 = [ch for ch, w in data["widths"].items() if w > 6]
    w7 = [ch for ch, w in data["widths"].items() if w > 7]
    w8 = [ch for ch, w in data["widths"].items() if w > 8]
    f6 = "YES" if not w6 else "no (%d)" % len(w6)
    f7 = "YES" if not w7 else "no (%d)" % len(w7)
    f8 = "YES" if not w8 else "no (%d)" % len(w8)
    md.append("| %s | %d | %d | %d | %s | %s | %s |" % (font_name, size, mw, mh, f6, f7, f8))

md.append("\n## Fonts that fit ALL characters\n")
for tw in [6, 7, 8]:
    md.append("### %dpx cell width" % tw)
    if fit_results[tw]:
        for fn, sz, mw, mh in fit_results[tw]:
            md.append("- **%s @ %dpt** (max glyph: %dx%dpx)" % (fn, sz, mw, mh))
    else:
        md.append("- NONE - no font/size combo fits all ASCII chars")
    md.append("")

md.append("## Width distribution (promising configs)\n")
for (font_name, size), data in sorted(results.items(), key=lambda x: (x[1]["max_width"], x[0][1])):
    if data["max_width"] > 10:
        continue
    dist = {}
    for ch, w in data["widths"].items():
        dist.setdefault(w, []).append(ch)
    md.append("### %s @ %dpt (max=%dpx, h=%dpx)" % (font_name, size, data["max_width"], data["max_height"]))
    for w in sorted(dist.keys()):
        chars = "".join(sorted(dist[w]))
        md.append("- %dpx: `%s`" % (w, chars))
    md.append("")

md.append("## Conclusions\n")

if fit_results[6]:
    md.append("### 6px width: FEASIBLE")
    md.append("The following fonts fit all ASCII characters in 6px:")
    for fn, sz, mw, mh in fit_results[6]:
        md.append("- %s @ %dpt" % (fn, sz))
    md.append("However, readability at this size may be poor.\n")
else:
    md.append("### 6px width: NOT FEASIBLE with standard fonts")
    md.append("No tested font/size combination fits ALL ASCII glyphs within 6 pixels.")
    closest = None
    for (fn, sz), data in results.items():
        wide = len([ch for ch, w in data["widths"].items() if w > 6])
        if closest is None or wide < closest[2]:
            closest = (fn, sz, wide, data["max_width"])
    if closest:
        md.append("Closest: %s @ %dpt (%d chars exceed 6px, max=%dpx)" % closest)
    md.append("")

if fit_results[7]:
    md.append("### 7px width: FEASIBLE")
    for fn, sz, mw, mh in fit_results[7]:
        md.append("- %s @ %dpt (height: %dpx)" % (fn, sz, mh))
    md.append("")
else:
    md.append("### 7px width: NOT FEASIBLE")
    md.append("")

if fit_results[8]:
    md.append("### 8px width: FEASIBLE (recommended fallback)")
    for fn, sz, mw, mh in fit_results[8]:
        md.append("- %s @ %dpt (height: %dpx)" % (fn, sz, mh))
    md.append("")
else:
    md.append("### 8px width: NOT FEASIBLE")
    md.append("")

md.append("## Generated images\n")
md.append("- `build/halfwidth_font_test.png` - Comparison atlas of all viable configs")
md.append("- `build/halfwidth_font_6px.png` - Best 6px config (if any)")
md.append("- `build/halfwidth_font_7px.png` - Best 7px config")
md.append("- `build/halfwidth_font_8px.png` - Best 8px config")

report_path = run_dir + "/halfwidth_font_test.md"
with open(report_path, "w") as f:
    f.write("\n".join(md))
print("\nReport written to: %s" % report_path)
print("\nDONE.")
