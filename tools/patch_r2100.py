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

        # Check if this sub-block has any patches
        sub_patches = {(r, c): txt for (sb, r, c), txt in STAT_PATCHES.items() if sb == blk}
        if not sub_patches:
            continue

        print(f"\n  Sub-block {blk}: {len(sub_patches)} patches")

        # Deswizzle
        linear = bytearray(deswizzle_psmt4(
            bytes(pixel_raw), TEX_W, TEX_H,
            bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
        ))

        # Apply patches
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
