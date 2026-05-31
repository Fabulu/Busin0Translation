#!/usr/bin/env python3
"""
patch_r1188_stats.py -- Replace Japanese stat label kanji with English text
in the R1188 PSMT4 1024x1024 glyph atlas.

Stat labels in Busin 0 are composed of 1-3 kanji glyphs from R1188:
  STR = 力          (1 glyph)
  INT = 知恵        (2 glyphs)
  PIE = 信仰心      (3 glyphs)
  VIT = 生命力      (3 glyphs)
  AGI = 敏速度      (3 glyphs)
  LCK = 幸運度      (3 glyphs)

Shared glyphs:
  力 (glyph 346): used by both STR (sole char) and VIT (3rd char)
  度 (glyph 590): used by both AGI (3rd char) and LCK (3rd char)

Approach: Edit each glyph's pixel data in-place at its exact atlas position.
The atlas position is computed from the cell's VRAM block address via the
PSMT4 nibble-address mapping.

Rendering assignments (shared glyphs get ONE rendering):
  力  -> 'T'  : STR displays 'T', VIT displays 'VIT'
  知  -> 'I'  : INT displays 'IQ'
  恵  -> 'Q'  : INT displays 'IQ'
  信  -> 'P'  : PIE displays 'PIE'
  仰  -> 'I'  : PIE displays 'PIE'
  心  -> 'E'  : PIE displays 'PIE'
  生  -> 'V'  : VIT displays 'VIT'
  命  -> 'I'  : VIT displays 'VIT'
  敏  -> 'A'  : AGI displays 'AGI'
  速  -> 'G'  : AGI displays 'AGI'
  度  -> 'I'  : AGI displays 'AGI', LCK displays 'LCI'
  幸  -> 'L'  : LCK displays 'LCI'
  運  -> 'C'  : LCK displays 'LCI'

Compromise: STR shows as 'T' (shared with VIT), LCK shows as 'LCI' (shared with AGI).
Both are recognisable from context in the stat screen.

Usage:
  python tools/patch_r1188_stats.py
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

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4, _psmt4_nibble_addr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
BIN_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
OUT_PATH = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
SECTOR = 2048
TEX_W = 1024
TEX_H = 1024
DBW_CT32 = 512
BW_PSMT4 = 1024
HEADER_BIN = 0xC00   # header size in .bin file
HEADER_RAW = 0xC10   # header size in .raw file (16-byte container + 0xC00)
BASE_VRAM = 0xA140   # lowest VRAM block used by any cell in the atlas

# ---------------------------------------------------------------------------
# Cell data for all stat label glyphs (from EXE analysis)
# Format: (label, english_char, u_cell, v_cell, vram_block, exe_offset)
# exe_offset = file offset where this cell's 8 bytes live in SLPM_653.78
# ---------------------------------------------------------------------------
STAT_GLYPHS = [
    # STR = 力 (glyph 346, shared with VIT-3)
    ("STR",   "T",  1, 60, 0xA450, 0x3D9040),
    # INT = 知 + 恵
    ("INT-1", "I",  0, 67, 0xA1F0, 0x3D8DC8),
    ("INT-2", "Q",  3, 88, 0xA700, 0x3D92F8),
    # PIE = 信 + 仰 + 心
    ("PIE-1", "P",  0, 76, 0xA238, 0x3D8E10),
    ("PIE-2", "I",  0, 66, 0xA390, 0x3D8F80),
    ("PIE-3", "E",  0, 62, 0xA290, 0x3D8E70),
    # VIT = 生 + 命 + 力(shared)
    ("VIT-1", "V",  4, 60, 0xA708, 0x3D9300),
    ("VIT-2", "I",  3, 67, 0xA658, 0x3D9250),
    # VIT-3 is STR (glyph 346) -- already listed above
    # AGI = 敏 + 速 + 度(shared)
    ("AGI-1", "A",  0, 60, 0xA2E0, 0x3D8EC0),
    ("AGI-2", "G",  4, 61, 0xA710, 0x3D9308),
    # AGI-3 / LCK-3 = 度 (glyph 590, shared)
    ("AGI-3", "I",  0, 60, 0xA318, 0x3D8F00),
    # LCK = 幸 + 運 + 度(shared)
    ("LCK-1", "L",  4, 62, 0xA718, 0x3D9310),
    ("LCK-2", "C",  4, 63, 0xA720, 0x3D9318),
    # LCK-3 is AGI-3 (glyph 590) -- already listed above
]

# Glyph cell size: each glyph occupies roughly 20x20 pixels in the atlas.
# The game renders each as a sprite, so we clear the bounding box and render text.
GLYPH_W = 20
GLYPH_H = 20


def get_font(size=16):
    """Get a font suitable for rendering single letters in ~20px cells."""
    for font_name in [
        os.path.join(BASE, "build", "font", "arial.ttf"),
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/verdana.ttf",
        "arial.ttf",
    ]:
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_letter_indices(letter, width, height, font_size=16):
    """Render a single letter as PSMT4 index array (0-15).

    Returns a 2D list [row][col] of palette indices.
    Index 0 = transparent, index 15 = fully opaque.
    """
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Shrink if too wide
    while tw > width - 1 and font_size > 8:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), letter, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    # Centre the letter in the cell
    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), letter, fill=255, font=font)

    # Convert grayscale to 4-bit index
    pixels = img.load()
    result = []
    for py in range(height):
        row = []
        for px in range(width):
            v = pixels[px, py]
            idx = round(v * 15 / 255)
            row.append(idx)
        result.append(row)
    return result


def build_reverse_nibble_map():
    """Build a reverse map: VRAM nibble address -> (atlas_x, atlas_y).

    This allows us to find where any VRAM address maps to in the
    deswizzled 1024x1024 atlas.
    """
    reverse = {}
    for y in range(TEX_H):
        for x in range(TEX_W):
            nib = _psmt4_nibble_addr(x, y, BW_PSMT4)
            reverse[nib] = (x, y)
    return reverse


def cell_to_atlas_position(u_cell, v_cell, vram_block, reverse_map):
    """Map a cell's (U, V, VRAM) to the deswizzled atlas pixel coordinate.

    The game reads PSMT4 at TBP0=vram_block, TBW=4 (256px), pixel (U, V).
    This translates to a global VRAM nibble address which we look up in
    the deswizzled atlas.
    """
    local_nib = _psmt4_nibble_addr(u_cell, v_cell, 256)
    global_nib = (vram_block - BASE_VRAM) * 512 + local_nib
    return reverse_map.get(global_nib)


def patch_glyph_in_atlas(linear, atlas_x, atlas_y, letter_indices, reverse_map,
                          u_cell, v_cell, vram_block):
    """Write rendered letter pixels into the deswizzled atlas.

    For each pixel (dx, dy) in the letter, we compute the exact atlas
    position via the VRAM nibble mapping. This handles page-boundary
    wrapping correctly.
    """
    h = len(letter_indices)
    w = len(letter_indices[0]) if h > 0 else 0
    edits = 0

    for dy in range(h):
        for dx in range(w):
            # Compute the VRAM nibble for this pixel in the 256-wide sub-atlas
            local_nib = _psmt4_nibble_addr(u_cell + dx, v_cell + dy, 256)
            global_nib = (vram_block - BASE_VRAM) * 512 + local_nib
            pos = reverse_map.get(global_nib)
            if pos is None:
                continue
            ax, ay = pos
            if 0 <= ax < TEX_W and 0 <= ay < TEX_H:
                linear[ay * TEX_W + ax] = letter_indices[dy][dx]
                edits += 1

    return edits


def main():
    print("=== R1188 Stat Label Patcher ===")
    print()

    # --- Load source file ---
    if os.path.exists(OUT_PATH):
        # If a previously patched file exists (from patch_r1188_direct.py),
        # use it as the base so both patches stack
        src_path = OUT_PATH
        header_size = HEADER_RAW
        print(f"  Source: {src_path} (previously patched)")
    elif os.path.exists(BIN_PATH):
        src_path = BIN_PATH
        header_size = HEADER_BIN
        print(f"  Source: {src_path}")
    elif os.path.exists(RAW_PATH):
        src_path = RAW_PATH
        header_size = HEADER_RAW
        print(f"  Source: {src_path}")
    else:
        print(f"  ERROR: No R1188 file found")
        sys.exit(1)

    data = open(src_path, "rb").read()
    header = data[:header_size]
    pixel_data = data[header_size : header_size + TEX_W * TEX_H // 2]
    print(f"  File: {len(data)} bytes, header: {header_size}, pixels: {len(pixel_data)}")

    # --- Deswizzle ---
    print("  Deswizzling 1024x1024 PSMT4 (dbw_ct32=512)...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # --- Build reverse nibble map ---
    print("  Building VRAM reverse lookup (this takes ~20s)...")
    reverse_map = build_reverse_nibble_map()
    print(f"  Reverse map: {len(reverse_map)} entries")

    # --- Render and patch each glyph ---
    print()
    print("  Patching stat label glyphs:")
    total_edits = 0

    for label, eng_char, u, v, vram, exe_off in STAT_GLYPHS:
        # Find atlas origin
        origin = cell_to_atlas_position(u, v, vram, reverse_map)
        if origin is None:
            print(f"    {label:7s}: FAILED to map (U={u}, V={v}, VRAM=0x{vram:04X})")
            continue

        ax, ay = origin

        # Clear the glyph area first (set to index 0 = transparent)
        cleared = 0
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                local_nib = _psmt4_nibble_addr(u + dx, v + dy, 256)
                global_nib = (vram - BASE_VRAM) * 512 + local_nib
                pos = reverse_map.get(global_nib)
                if pos:
                    px, py = pos
                    if 0 <= px < TEX_W and 0 <= py < TEX_H:
                        if linear[py * TEX_W + px] != 0:
                            cleared += 1
                        linear[py * TEX_W + px] = 0

        # Render English letter
        letter_indices = render_letter_indices(eng_char, GLYPH_W, GLYPH_H)

        # Write letter pixels into the atlas
        edits = patch_glyph_in_atlas(linear, ax, ay, letter_indices, reverse_map,
                                      u, v, vram)
        total_edits += edits
        print(f"    {label:7s}: '{eng_char}' at atlas({ax:4d},{ay:4d}), "
              f"cleared={cleared}, written={edits}")

    print(f"\n  Total pixel edits: {total_edits}")

    # --- Re-swizzle ---
    print("  Re-swizzling to PSMCT32 upload format...")
    reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # --- Write output ---
    # Use the raw file's header format (16-byte container + GIF header)
    raw_data = open(RAW_PATH, "rb").read()
    raw_header = raw_data[:HEADER_RAW]

    out_data = bytearray(raw_header)
    out_data += reswizzled

    # Pad to sector boundary
    remainder = len(out_data) % SECTOR
    if remainder:
        out_data += b"\x00" * (SECTOR - remainder)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(out_data)
    print(f"  Output: {OUT_PATH} ({len(out_data)} bytes, sector-aligned)")

    # --- Round-trip verification ---
    verify_pixels = reswizzled[: len(pixel_data)]
    re_deswizzled = deswizzle_psmt4(verify_pixels, TEX_W, TEX_H,
                                     bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    mismatches = sum(1 for a, b in zip(linear, re_deswizzled) if a != b)
    if mismatches == 0:
        print("  Round-trip verification: PASS")
    else:
        print(f"  Round-trip verification: FAIL ({mismatches} mismatches)")

    # --- Save debug visualisation ---
    debug_dir = os.path.join(BASE, "build", "textures_to_edit")
    os.makedirs(debug_dir, exist_ok=True)

    # Save a cropped view around each patched glyph
    from PIL import Image as PILImage
    full_dbg = PILImage.new("L", (TEX_W, TEX_H))
    for y in range(TEX_H):
        for x in range(TEX_W):
            idx = linear[y * TEX_W + x]
            full_dbg.putpixel((x, y), idx * 17)

    debug_path = os.path.join(debug_dir, "R1188_stat_labels_patched.png")
    full_dbg.save(debug_path)
    print(f"  Debug: {debug_path}")

    # Save close-ups (using VRAM mapping, as the game sees each glyph)
    closeup = PILImage.new("L", (GLYPH_W * len(STAT_GLYPHS), GLYPH_H))
    for i, (label, eng, u, v, vram, _) in enumerate(STAT_GLYPHS):
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                local_nib = _psmt4_nibble_addr(u + dx, v + dy, 256)
                global_nib = (vram - BASE_VRAM) * 512 + local_nib
                pos = reverse_map.get(global_nib)
                if pos:
                    px, py = pos
                    val = linear[py * TEX_W + px]
                    closeup.putpixel((i * GLYPH_W + dx, dy), val * 17)

    closeup = closeup.resize((closeup.width * 4, closeup.height * 4), PILImage.NEAREST)
    closeup_path = os.path.join(debug_dir, "R1188_stat_closeups.png")
    closeup.save(closeup_path)
    print(f"  Closeup: {closeup_path}")

    print("\nDone!")
    print()
    print("Stat labels after patching:")
    print("  STR -> T          (compromise: shared glyph with VIT)")
    print("  INT -> IQ         (Intelligence Quotient)")
    print("  PIE -> PIE        (Piety)")
    print("  VIT -> VIT        (Vitality)")
    print("  AGI -> AGI        (Agility)")
    print("  LCK -> LCI        (compromise: shared glyph with AGI)")


if __name__ == "__main__":
    main()
