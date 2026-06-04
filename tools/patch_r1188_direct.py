#!/usr/bin/env python3
"""
Direct R1188 pixel patcher for name entry screen English labels.

Two-pronged approach:
  1. PCSX2 texture replacements (renders English labels as separate PNGs
     that PCSX2 overlays at runtime via hash matching)
  2. Direct pixel editing of R1188's 1024x1024 PSMT4 atlas: renders English
     labels into the unused bottom rows (y=1009-1020) of the texture.
     A companion EXE patch (not yet implemented) would redirect the tab label
     UV lookups to these new positions.

Tab labels replaced:
  48x20: カナ->Kana, かな->Hira, 英数->ABC, 記号->Sym
  40x24: 決定->OK
  48x20: 男名->M, 女名->F
  120x24: 新規登録->New Character

R1188 layout:
  Header: 3072 bytes (0xC00)
  Pixel data: 524,288 bytes (1024x1024 PSMT4)
  No trailing CLUT in file
  Deswizzle: dbw_ct32=512, bw_psmt4=1024
"""
import sys
import os
import io
import struct

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

# Paths
BIN_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
OUT_PATH = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
REPLACE_DIR = os.path.join(BASE, "build", "pcsx2_texture_replacements")
SECTOR = 2048
HEADER_SIZE = 0xC00  # 3072 bytes
TEX_W = 1024
TEX_H = 1024
DBW_CT32 = 512
BW_PSMT4 = 1024

# --- PCSX2 texture replacement hashes ---
CLUT_HASH = '3cb39bf7659ef15f'
CLUT_HASH_TITLE = 'e786e0650b284c64'
GS_PAGE = '00002214'

TAB_LABELS_48x20 = {
    '16625baf9feaeafb': 'Gender',
    '19a39fbc8a08d7ec': 'Sym',
    '1f839869fab251d':  'Kana',
    '6f1fb24fad5cd1a':  'ABC',
    '88ff8b577084a2a8': 'Class',
    '9677cb23da53ff88': 'Hira',
    '9bec87b4031a7172': 'Race',
    'c89b469f7a152a6':  'Align',
}
BUTTONS_40x24 = {'d09a04bdfaf715bc': 'OK'}
TITLE_120x24 = {'a2d3fce36c8c719d': 'New Character'}
STAT_LABELS_64x16 = {
    '280ea82c1c476a98': 'Luck',
    '4841ef9a2dc4981':  'Agility',
    '5d0c6327e20384e7': 'Vitality',
    'aa43f966ad69195e': 'Piety',
    'bb20512b10c3128b': 'IQ',
    'f2013a64642252e3': 'Strength',
}

# --- English labels to render into the atlas bottom area ---
# Placed in the empty rows y=1009-1020 of the 1024x1024 atlas.
# Each label gets a 48x12 cell. Layout (left to right):
#   x=0:    "Kana"   (48x12)
#   x=48:   "Hira"   (48x12)
#   x=96:   "ABC"    (48x12)
#   x=144:  "Sym"    (48x12)
#   x=192:  "OK"     (40x12)
#   x=232:  "M" (48x12)
#   x=280:  "F" (48x12)
#   x=328:  "Delete" (48x12)
#   x=376:  "Clear"  (48x12)
# Row 2 (y=1013):
#   x=0:    "New Character" (120x12)
ATLAS_LABELS = [
    # (x, y, width, height, text)
    # Row 1 (y=1009): tab labels and buttons
    (0,   1009, 48, 11, "Kana"),
    (50,  1009, 48, 11, "Hira"),
    (100, 1009, 48, 11, "ABC"),
    (150, 1009, 48, 11, "Sym"),
    (200, 1009, 40, 11, "OK"),
    (242, 1009, 48, 11, "M"),
    (292, 1009, 48, 11, "F"),
    (342, 1009, 48, 11, "Delete"),
    (392, 1009, 48, 11, "Clear"),
    # Row 2 (y=1011): title text (non-overlapping, starts after row 1 height)
    (450, 1009, 120, 11, "New Character"),
]


def get_font(size=10):
    """Get a suitable small font for rendering labels."""
    font = None
    for font_name in [
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/tahoma.ttf',
        'C:/Windows/Fonts/verdana.ttf',
        'arial.ttf',
        'DejaVuSans.ttf',
    ]:
        try:
            font = ImageFont.truetype(font_name, size)
            return font
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_label_rgba(text, width, height, font_size=14):
    """Render English label as white-on-transparent RGBA."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Shrink font if text too wide
    while tw > width - 2 and font_size > 6:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Quantize alpha to PS2's 16 levels
    ps2_alphas = [0, 11, 19, 28, 36, 44, 52, 60, 69, 77, 85, 93, 102, 110, 118, 128]
    pixels = img.load()
    for py in range(height):
        for px in range(width):
            r, g, b, a = pixels[px, py]
            if a == 0:
                pixels[px, py] = (255, 255, 255, 0)
            else:
                ps2_a = round(a * 128 / 255)
                closest = min(ps2_alphas, key=lambda v: abs(v - ps2_a))
                pixels[px, py] = (255, 255, 255, closest)
    return img


def render_label_indices(text, width, height, font_size=10):
    """Render English label as PSMT4 index array (0-15).

    Returns a 2D list of palette indices. Index 0 = transparent,
    index 15 = most opaque.
    """
    img = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    while tw > width - 2 and font_size > 6:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=255, font=font)

    # Convert grayscale (0-255) to PSMT4 index (0-15)
    arr = img.load()
    result = []
    for py in range(height):
        row = []
        for px in range(width):
            v = arr[px, py]
            idx = round(v * 15 / 255)
            row.append(idx)
        result.append(row)
    return result


def create_pcsx2_replacements():
    """Create PCSX2 texture replacement PNG files."""
    os.makedirs(REPLACE_DIR, exist_ok=True)
    count = 0

    for hash1, english in TAB_LABELS_48x20.items():
        filename = f"{hash1}-{CLUT_HASH}-r48x20-{GS_PAGE}.png"
        img = render_label_rgba(english, 48, 20)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    for hash1, english in BUTTONS_40x24.items():
        filename = f"{hash1}-{CLUT_HASH}-r40x24-{GS_PAGE}.png"
        img = render_label_rgba(english, 40, 24)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    for hash1, english in TITLE_120x24.items():
        filename = f"{hash1}-{CLUT_HASH_TITLE}-r120x24-{GS_PAGE}.png"
        img = render_label_rgba(english, 120, 24)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    for hash1, english in STAT_LABELS_64x16.items():
        filename = f"{hash1}-{CLUT_HASH}-r64x16-{GS_PAGE}.png"
        img = render_label_rgba(english, 64, 16)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    print(f"  PCSX2 replacements: {count} files in {REPLACE_DIR}")
    return count


def patch_atlas_pixels(linear_pixels):
    """Render English labels into the atlas's unused bottom rows.

    Modifies linear_pixels in place. These labels are placed in rows
    y=1009-1020 which are confirmed empty in the original atlas.
    """
    edits = 0
    for x, y, w, h, text in ATLAS_LABELS:
        indices = render_label_indices(text, w, h)
        for dy in range(h):
            for dx in range(w):
                px = x + dx
                py = y + dy
                if 0 <= px < TEX_W and 0 <= py < TEX_H:
                    old_val = linear_pixels[py * TEX_W + px]
                    new_val = indices[dy][dx]
                    if new_val != old_val:
                        linear_pixels[py * TEX_W + px] = new_val
                        edits += 1
    return edits


def main():
    print("=== R1188 Direct Pixel Patcher ===")

    # --- Step 1: Create PCSX2 texture replacements (proven approach) ---
    create_pcsx2_replacements()

    # --- Step 2: Load and deswizzle R1188 ---
    # Prefer the .bin (packdata_resources) for clean header
    if os.path.exists(BIN_PATH):
        src_path = BIN_PATH
        header_size = HEADER_SIZE
    elif os.path.exists(RAW_PATH):
        src_path = RAW_PATH
        header_size = HEADER_SIZE + 0x10  # raw has 16-byte outer container
    else:
        print(f"  ERROR: Neither {BIN_PATH} nor {RAW_PATH} found")
        sys.exit(1)

    data = open(src_path, 'rb').read()
    header = data[:header_size]
    pixel_data = data[header_size:header_size + TEX_W * TEX_H // 2]

    print(f"  Source: {src_path} ({len(data)} bytes)")
    print(f"  Header: {header_size} bytes, pixels: {len(pixel_data)} bytes")

    print("  Deswizzling 1024x1024 PSMT4 (dbw_ct32=512)...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # --- Step 3: Render English labels into atlas bottom area ---
    edits = patch_atlas_pixels(linear)
    print(f"  Direct pixel edits: {edits} pixels modified in atlas rows 1009-1020")

    # --- Step 4: Re-swizzle ---
    print("  Re-swizzling to PSMCT32 upload format...")
    reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # --- Step 5: Write output ---
    # For PACKDATA.DIG injection, we need the raw format:
    # Use the original raw file's header (including 16-byte container)
    raw_data = open(RAW_PATH, 'rb').read()
    raw_header = raw_data[:HEADER_SIZE + 0x10]  # 16-byte container + 3072-byte header

    out_data = bytearray(raw_header)
    out_data += reswizzled

    # Pad to sector boundary
    remainder = len(out_data) % SECTOR
    if remainder:
        out_data += b'\x00' * (SECTOR - remainder)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'wb') as f:
        f.write(out_data)

    print(f"  Output: {OUT_PATH} ({len(out_data)} bytes, sector-aligned)")

    # --- Step 6: Verify round-trip (optional sanity check) ---
    # Re-deswizzle and compare
    verify_pixels = reswizzled[:len(pixel_data)]
    re_deswizzled = deswizzle_psmt4(verify_pixels, TEX_W, TEX_H,
                                     bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    mismatches = sum(1 for a, b in zip(linear, re_deswizzled) if a != b)
    if mismatches == 0:
        print("  Round-trip verification: PASS")
    else:
        print(f"  Round-trip verification: FAIL ({mismatches} mismatches)")

    # Save debug visualization
    debug_dir = os.path.join(BASE, "build", "textures_to_edit")
    os.makedirs(debug_dir, exist_ok=True)
    debug_path = os.path.join(debug_dir, "R1188_patched_bottom.png")
    from PIL import Image as PILImage
    dbg = PILImage.new('L', (TEX_W, 24))
    for y in range(1005, 1024):
        for x in range(TEX_W):
            idx = linear[y * TEX_W + x]
            dbg.putpixel((x, y - 1005), idx * 17)
    dbg = dbg.resize((dbg.width * 3, dbg.height * 3), PILImage.NEAREST)
    dbg.save(debug_path)
    print(f"  Debug: {debug_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
