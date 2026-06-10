#!/usr/bin/env python3
"""
R2100 chargen/stat font atlas patcher.

Reads the R2100 resource (4 sub-blocks of 256x256 PSMT4 textures) from
PACKDATA.DIG, replaces specific kanji cells with English stat abbreviations,
and writes the patched resource to build/packdata_resources/2100_type04.raw.

Structure per sub-block (34,624 bytes each):
  - 0x4C0 bytes: VIF/GIF DMA chain header (preserved verbatim)
  - 32,768 bytes: PSMT4 pixel data (256x256, deswizzled with dbw_ct32=128)
  - 640 bytes: CLUT tail (10 x 16-color RGBA palettes, preserved verbatim)

Resource-level layout:
  - 64 bytes: descriptor table (4 entries x 16 bytes)
  - 4 x 34,624 bytes: sub-block data
  - padding to sector boundary (139,264 bytes total = 68 sectors)
"""

import math
import struct
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")
OUTPUT_PATH = os.path.join(BASE, "build", "packdata_resources", "2100_type04.raw")
PREVIEW_DIR = os.path.join(BASE, "build")

# ── Constants ──
SECTOR = 2048
R2100_TOC_INDEX = 2100
TOC_ENTRIES = 2883
NUM_SUBS = 4
SUB_SIZE = 34624      # 0x8740
HDR_SIZE = 0x4C0      # 1216 bytes of VIF/GIF header per sub-block
PIXEL_SIZE = 32768    # 256x256 PSMT4 = 32768 bytes swizzled
TAIL_SIZE = 640       # CLUT data after pixels
TEX_W, TEX_H = 256, 256
CELL_W, CELL_H = 16, 16
COLS = TEX_W // CELL_W   # 16 cells per row
ROWS = TEX_H // CELL_H   # 16 cells per column
DBW_CT32 = 128
BW_PSMT4 = 256

# ── Stat kanji replacement map ──
# Format: (sub_block, row, col) -> text_to_render
# Index 0 = fully opaque text, index 15 = transparent background
# Each kanji occupies one 16x16 cell. English abbreviations are rendered
# into the cell that held the FIRST kanji of the Japanese stat name.
# Subsequent kanji cells are blanked.
#
# Japanese stat names -> English:
#   力        -> Str
#   知恵      -> Int (知=Int, 恵=blank)
#   信仰心    -> Pie (信=Pie, 仰=blank, 心=blank)
#   生命      -> Vit (生=Vit, 命=blank)
#   敏捷度    -> Agi (敏=Agi, 捷=blank, 度=blank)
#   幸運      -> Lck (幸=Lck, 運=blank)

# ── Gender symbol replacement map ──
# ♂ and ♀ symbols rendered into R2100 kanji cells.
# Placed in sub-block 2, row 10 (unused cells far from any keyboard/stat glyphs)
# to avoid VRAM conflicts when the game uploads different sub-blocks.
# Old positions (sub 2 row 0 col 6 = glyph 518, sub 1 row 5 col 13 = glyph 349)
# shared VRAM space with keyboard ASCII cells, causing F and M to disappear.
GENDER_PATCHES = {
    # ♂ (Mars/male): sub-block 2, row 10, col 0 — glyph ID 672
    (2, 10, 0): "male",
    # ♀ (Venus/female): sub-block 2, row 10, col 1 — glyph ID 673
    (2, 10, 1): "female",
}


def render_gender_symbol(symbol_name):
    """Render ♂ or ♀ symbol procedurally into a 16x16 cell.

    Returns list of 256 pixel values: 0=opaque (ink), 15=transparent (bg).
    Draws anti-alias-free 1-bit shapes suitable for PSMT4 on real PS2 hardware.
    """
    # Start with all-transparent
    pixels = [15] * (CELL_W * CELL_H)

    def put(x, y):
        if 0 <= x < CELL_W and 0 <= y < CELL_H:
            pixels[y * CELL_W + x] = 0

    if symbol_name == "male":
        # ♂ Mars symbol: circle center (6,9), radius 4, arrow to upper-right
        # Circle (r=4, center 6,9) using midpoint algorithm
        cx, cy, r = 6, 9, 4
        # Draw circle outline
        for angle_step in range(360):
            rad = math.radians(angle_step)
            rx = round(cx + r * math.cos(rad))
            ry = round(cy + r * math.sin(rad))
            put(rx, ry)

        # Arrow shaft: from circle edge (~upper-right at 45 deg) to corner area
        # Circle edge at 45 deg: (6+2.8, 9-2.8) ~ (9, 6)
        # Arrow tip at (13, 2)
        # Shaft from (9,6) to (13,2)
        for i in range(9):
            t = i / 8
            ax = round(9 + (13 - 9) * t)
            ay = round(6 + (2 - 6) * t)
            put(ax, ay)

        # Arrowhead
        # Tip at (13,2), barbs
        put(13, 2)
        put(12, 2); put(11, 2)  # horizontal barb left
        put(13, 3); put(13, 4)  # vertical barb down

    elif symbol_name == "female":
        # ♀ Venus symbol: circle center (7,5), radius 4, cross below
        cx, cy, r = 7, 5, 4
        # Draw circle outline
        for angle_step in range(360):
            rad = math.radians(angle_step)
            rx = round(cx + r * math.cos(rad))
            ry = round(cy + r * math.sin(rad))
            put(rx, ry)

        # Vertical stem: from bottom of circle (7,9) down to (7,14)
        for y in range(9, 15):
            put(7, y)

        # Horizontal crossbar at y=12
        for x in range(5, 10):
            put(x, 12)

    return pixels


STAT_PATCHES = {
    # Sub-block 1: STR and PIE components
    # 力 (chikara) -> Str
    (1, 5, 10): "Str",    # 力
    # 信仰心 (shinkou-shin) -> Pie
    (1, 3,  4): "Pie",    # 信
    (1, 6,  2): "",       # 仰 -> blank
    (1, 4,  0): "",       # 心 -> blank

    # Sub-block 2: INT, VIT, AGI, LCK components
    # 知恵 (chie) -> Int
    (2, 1,  7): "Int",    # 知
    (2, 12, 13): "",      # 恵 -> blank
    # 敏捷度 (binshoudo) -> Agi
    (2, 4,  6): "Agi",    # 敏
    (2, 12, 15): "",      # 捷 -> blank
    (2, 4, 14): "",       # 度 -> blank
    # 生命 (seimei) -> Vit
    (2, 12, 14): "Vit",   # 生
    (2, 11,  8): "",      # 命 -> blank
    # 幸運 (kouun) -> Lck
    (2, 13,  0): "Lck",   # 幸
    (2, 13,  1): "",      # 運 -> blank
}


def load_font():
    """Find and load a suitable font for rendering stat abbreviations."""
    # Use a compact font at small size to fit 3 chars in a 16x16 cell
    # Arial Bold at size 9 fits all 3-letter abbreviations within 16px width
    font_candidates = [
        ("C:/Windows/Fonts/arialbd.ttf", 9),
        ("C:/Windows/Fonts/arial.ttf", 10),
        ("C:/Windows/Fonts/consola.ttf", 9),
        ("C:/Windows/Fonts/cour.ttf", 9),
    ]
    for fp, sz in font_candidates:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, sz)
            print(f"  Using font: {fp} size {sz}")
            return font
    font = ImageFont.load_default()
    print("  Using default font")
    return font


def render_text_cell(text, font, cell_w=CELL_W, cell_h=CELL_H):
    """Render text centered in a cell. Returns list of pixel values 0-15.

    0 = fully opaque (text), 15 = transparent (background).
    The palette maps index 0 to highest alpha and index 15 to alpha 0.
    """
    # Render at 8-bit grayscale first
    img = Image.new("L", (cell_w, cell_h), 0)  # black background
    if not text:
        # Return all-transparent cell
        return [15] * (cell_w * cell_h)

    draw = ImageDraw.Draw(img)
    bbox = font.getbbox(text)
    if bbox:
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Center horizontally, but clamp to left edge if text is wider than cell
        if tw <= cell_w:
            ox = (cell_w - tw) // 2 - bbox[0]
        else:
            ox = -bbox[0]  # left-align, let it clip on right
        oy = max(0, (cell_h - th) // 2) - bbox[1]
        draw.text((ox, oy), text, fill=255, font=font)

    # Convert to 4-bit: white(255)->0(opaque), black(0)->15(transparent)
    pixels = list(img.getdata())
    result = []
    for val in pixels:
        game_val = 15 - min(val * 15 // 255, 15)
        result.append(game_val)
    return result


def patch_cell(linear_pixels, row, col, cell_data, tex_w=TEX_W):
    """Write cell_data (list of pixel values) into the linear pixel array."""
    x0 = col * CELL_W
    y0 = row * CELL_H
    for dy in range(CELL_H):
        for dx in range(CELL_W):
            idx = (y0 + dy) * tex_w + (x0 + dx)
            linear_pixels[idx] = cell_data[dy * CELL_W + dx]


def main():
    print("=== R2100 Stat Label Patcher ===\n")

    # ── Read R2100 from PACKDATA.DIG ──
    print(f"Reading R2100 from {DIG_PATH}...")
    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        byte_off = so * SECTOR
        byte_size = sc * SECTOR

        print(f"  TOC: sector_offset=0x{so:X}, sector_count={sc}, type={tc}")
        print(f"  Byte offset: {byte_off}, size: {byte_size}")

        f.seek(byte_off)
        r2100 = bytearray(f.read(byte_size))
        assert len(r2100) == byte_size, f"Short read: {len(r2100)} < {byte_size}"

    # ── Parse descriptor table ──
    print("\n  Descriptor table:")
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from("<IIII", r2100, i * 16)
        print(f"    Sub {i}: size=0x{sub_size:X}, offset=0x{data_off:X}")
        assert sub_size == SUB_SIZE, f"Unexpected sub-block size: {sub_size}"
        sub_entries.append((sub_idx, sub_size, data_off))

    # ── Load font ──
    font = load_font()

    # ── Process each sub-block ──
    patches_applied = 0
    for blk in range(NUM_SUBS):
        sub_idx, sub_size, data_off = sub_entries[blk]
        sub_data = r2100[data_off:data_off + sub_size]

        # Split: header | pixels | tail
        header = sub_data[:HDR_SIZE]
        pixel_raw = sub_data[HDR_SIZE:HDR_SIZE + PIXEL_SIZE]
        tail = sub_data[HDR_SIZE + PIXEL_SIZE:]

        assert len(pixel_raw) == PIXEL_SIZE
        assert len(tail) == TAIL_SIZE

        # Check if this sub-block has any patches (stat text, gender, or uppercase dup)
        sub_patches = {(r, c): txt for (sb, r, c), txt in STAT_PATCHES.items() if sb == blk}
        sub_gender = {(r, c): sym for (sb, r, c), sym in GENDER_PATCHES.items() if sb == blk}
        needs_uppercase_dup = (blk == 0)
        if not sub_patches and not sub_gender and not needs_uppercase_dup:
            continue

        print(f"\n  Sub-block {blk}: {len(sub_patches)} stat patches, {len(sub_gender)} gender patches")

        # Deswizzle
        linear = bytearray(deswizzle_psmt4(
            bytes(pixel_raw), TEX_W, TEX_H,
            bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
        ))

        # Apply stat text patches
        for (row, col), text in sub_patches.items():
            label = f"({row},{col})"
            if text:
                cell_data = render_text_cell(text, font)
                print(f"    Patch {label}: render '{text}'")
            else:
                cell_data = [15] * (CELL_W * CELL_H)  # transparent
                print(f"    Patch {label}: blank")
            patch_cell(linear, row, col, cell_data)
            patches_applied += 1

        # Apply gender symbol patches
        for (row, col), sym_name in sub_gender.items():
            label = f"({row},{col})"
            cell_data = render_gender_symbol(sym_name)
            sym_char = "♂" if sym_name == "male" else "♀"
            print(f"    Patch {label}: render '{sym_char}' ({sym_name})")
            patch_cell(linear, row, col, cell_data)
            patches_applied += 1

        # Duplicate uppercase A-Z from cells 33-58 to 95-120 (sub-block 0 only).
        # R37 name groups use remapped glyph IDs 95-120 to avoid keyboard font
        # metrics pollution. The chargen atlas needs matching bitmaps.
        # SKIP cell 110 (i=15, letter P): the padding glyph maps to cell 110,
        # so overwriting it with "P" causes "P" to appear in empty name slots.
        # Keeping cell 110's original Japanese content keeps padding invisible.
        if needs_uppercase_dup:
            dup_count = 0
            for i in range(26):
                src_id = 33 + i
                dst_id = 95 + i
                src_row, src_col = src_id // COLS, src_id % COLS
                dst_row, dst_col = dst_id // COLS, dst_id % COLS
                # Read source cell
                cell_data = []
                x0 = src_col * CELL_W
                y0 = src_row * CELL_H
                for dy in range(CELL_H):
                    for dx in range(CELL_W):
                        cell_data.append(linear[(y0 + dy) * TEX_W + (x0 + dx)])
                # Write to destination
                patch_cell(linear, dst_row, dst_col, cell_data)
                dup_count += 1
            print(f"    Duplicated {dup_count} uppercase cells (33-58 -> 95-120)")

        # Save preview
        preview = Image.new("L", (TEX_W, TEX_H))
        for i, p in enumerate(linear[:TEX_W * TEX_H]):
            preview.putpixel((i % TEX_W, i // TEX_W), 255 - p * 17)
        preview_path = os.path.join(PREVIEW_DIR, f"r2100_sub{blk}_patched.png")
        preview.save(preview_path)
        print(f"    Preview: {preview_path}")

        # Reswizzle
        reswizzled = swizzle_psmt4(
            linear, TEX_W, TEX_H,
            bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
        )

        # Verify round-trip on unpatched pixels would match
        assert len(reswizzled) == PIXEL_SIZE, \
            f"Reswizzled size mismatch: {len(reswizzled)} != {PIXEL_SIZE}"

        # Reassemble sub-block
        new_sub = bytes(header) + bytes(reswizzled) + bytes(tail)
        assert len(new_sub) == SUB_SIZE

        # Write back into r2100
        r2100[data_off:data_off + SUB_SIZE] = new_sub

    print(f"\n  Total patches applied: {patches_applied}")

    # ── Write output ──
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(r2100)
    print(f"\n  Output: {OUTPUT_PATH} ({len(r2100)} bytes)")
    print("DONE!")


if __name__ == "__main__":
    main()
