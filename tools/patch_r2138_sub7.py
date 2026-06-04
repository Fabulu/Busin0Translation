#!/usr/bin/env python3
"""
R2138 sub-resource #7 patcher — chargen stat/tab/sidebar label atlas.

Reads R2138 (type-29, 1,542,144 bytes), extracts the sub7 pixel data
(256x256 PSMT4 at offset 0x0755D0), deswizzles it, renders English labels
over the Japanese ones, re-swizzles, and writes back into a copy of R2138.

Output: build/packdata_resources/2138_type29.raw (same size as input)
Debug:  build/r2138_sub7_patched_preview.png
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
INPUT_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
OUTPUT_PATH = os.path.join(BASE, "build", "packdata_resources", "2138_type29.raw")
PREVIEW_PATH = os.path.join(BASE, "build", "r2138_sub7_patched_preview.png")
LABEL_MAP_PATH = os.path.join(BASE, "dumps", "r2138_analysis", "r2138_sub7_label_map.json")

# ── Constants ──
EXPECTED_SIZE = 1542144
SUB7_OFFSET = 0x075510
SUB7_SIZE = 33024
SUB7_HEADER_SIZE = 0xC0  # 192 bytes GIF A+D packets
PIXEL_OFFSET = 0x0755D0  # SUB7_OFFSET + SUB7_HEADER_SIZE
PIXEL_SIZE = 32768       # 256x256 PSMT4 = 32768 bytes
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128

# ── Label definitions ──
# Each entry: (x, y, w, h, english_text)
# Using the coordinates from the user's table (rounded to clean rectangles)
# and enriched with the label map JSON data.

STAT_LABELS = [
    # Stat labels (right side of atlas) — use wide clear zones
    # Height 18 on all labels (+1px top/bottom margin) to catch kanji descenders
    (192, 13,  64, 18, "HP"),       # HP/MAX display area
    (192, 77,  64, 18, "Str"),      # 力
    (192, 97,  64, 18, "Int"),      # 知恵
    (192, 117, 64, 18, "Pie"),      # 信仰心
    (192, 137, 64, 18, "Vit"),      # 生命力
    (192, 157, 64, 18, "Agi"),      # 敏捷度
    (192, 177, 64, 18, "Lck"),      # 幸運度
    (192, 197, 64, 18, "Atk"),      # 攻撃力
    (192, 217, 64, 18, "Eva"),      # 回避力
    (192, 237, 64, 19, "Def"),      # 防御力 (extends to bottom)
]

TAB_LABELS = [
    # Chargen tabs (top-left area) — each tab row ~20px tall
    (0,   0,  96, 20, "Basic Info"),       # 基本情報
    (0,  20,  96, 20, "Detail Status"),    # 詳細ステータス
    (0,  40,  96, 20, "Item"),             # アイテム
    (0,  58,  96, 20, "Mage Magic"),       # 魔術師魔法
    (0,  78,  96, 20, "Priest Magic"),     # 僧侶魔法
]

# Extra Japanese residuals that need clearing
CLEAR_ONLY = [
    # Residual JP below Priest Magic (visible at ~y=96-112)
    (0, 98, 96, 14),
    # Residual kana/characters below field labels area (~y=98-112, x=96-166)
    (96, 98, 70, 14),
]

INPUT_MODE_LABELS = [
    # Input mode buttons — clear enough to cover JP glyphs
    (96,   0, 14, 20, "Ka"),        # カナ (Katakana mode)
    (96,  20, 14, 20, "ka"),        # かな (Hiragana mode)
    (96,  40, 20, 20, "A1"),        # 英数 (Alphanumeric)
    (96,  58, 20, 20, "!@"),        # 記号 (Symbols)
]

CHARGEN_FIELD_LABELS = [
    # Character creation field labels — UV coords: (136,0)-(184,20) etc., 48px wide
    # Left-aligned within the 48px strip the game actually reads
    (136,  0, 48, 20, "Gender"),    # 性別
    (136, 20, 48, 20, "Race"),      # 種族
    (136, 40, 48, 20, "Align"),     # 属性
    (136, 60, 48, 20, "Class"),     # 職業
    # OK button — UV: (88,88)-(128,112) = 40x24
    (88,  88, 40, 24, "OK"),        # 決定
]

# Large HP label in chargen area
LARGE_LABELS = [
    (108, 78, 54, 22, "HP"),        # HP (large, chargen area) — JP extends to x=161
]

# Already-English labels we should NOT touch:
# LEVEL, EXP, NEXT, HP/MAX, digit glyphs — leave them as-is


def load_font(size=12, bold=True):
    """Load a suitable font for rendering labels."""
    if bold:
        candidates = [
            ("C:/Windows/Fonts/arialbd.ttf", size),
            ("C:/Windows/Fonts/arial.ttf", size),
        ]
    else:
        candidates = [
            ("C:/Windows/Fonts/arial.ttf", size),
            ("C:/Windows/Fonts/consola.ttf", size),
        ]
    for fp, sz in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, sz)
    return ImageFont.load_default()


def render_label(text, width, height, font, shrink=True):
    """Render text centered in a rectangle, returning palette indices.

    Returns a list of width*height values where:
      0 = fully opaque (ink/text)
      15 = fully transparent (background)
      1-14 = anti-aliased intermediate values
    """
    if not text:
        return [15] * (width * height)

    # Check if text fits; if not, try smaller fonts
    cur_font = font
    bbox = cur_font.getbbox(text)
    if bbox and shrink:
        tw = bbox[2] - bbox[0]
        while tw > width - 2 and cur_font.size > 7:
            cur_font = load_font(cur_font.size - 1, bold=True)
            bbox = cur_font.getbbox(text)
            tw = bbox[2] - bbox[0]

    # Render to grayscale image
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    bbox = cur_font.getbbox(text)
    if bbox:
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Center horizontally and vertically
        ox = max(0, (width - tw) // 2) - bbox[0]
        oy = max(0, (height - th) // 2) - bbox[1]
        draw.text((ox, oy), text, fill=255, font=cur_font)

    # Convert grayscale to palette indices
    # 255 (white/text) -> 0 (opaque), 0 (black/bg) -> 15 (transparent)
    pixels = list(img.getdata())
    result = []
    for val in pixels:
        if val == 0:
            result.append(15)  # transparent
        else:
            # Map 1-255 to 14-0 (higher brightness = lower palette = more opaque)
            game_val = 15 - min(val * 15 // 255, 15)
            if game_val == 15:
                game_val = 14  # ensure non-zero input maps to visible
            result.append(game_val)
    return result


def patch_rect(linear_pixels, x, y, w, h, cell_data, tex_w=TEX_W):
    """Write cell_data into the linear pixel array at arbitrary rectangle."""
    for dy in range(h):
        for dx in range(w):
            py = y + dy
            px = x + dx
            if 0 <= px < tex_w and 0 <= py < TEX_H:
                idx = py * tex_w + px
                linear_pixels[idx] = cell_data[dy * w + dx]


def clear_rect(linear_pixels, x, y, w, h, tex_w=TEX_W):
    """Fill rectangle with transparent (15)."""
    for dy in range(h):
        for dx in range(w):
            py = y + dy
            px = x + dx
            if 0 <= px < tex_w and 0 <= py < TEX_H:
                linear_pixels[py * tex_w + px] = 15


def main():
    print("=== R2138 Sub7 Stat Label Patcher ===\n")

    # ── Read R2138 ──
    print(f"Reading R2138 from {INPUT_PATH}...")
    with open(INPUT_PATH, "rb") as f:
        r2138 = bytearray(f.read())
    assert len(r2138) == EXPECTED_SIZE, \
        f"R2138 size mismatch: {len(r2138)} != {EXPECTED_SIZE}"
    print(f"  Size: {len(r2138)} bytes (OK)")

    # ── Extract sub7 pixel data ──
    pixel_data = bytes(r2138[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE])
    assert len(pixel_data) == PIXEL_SIZE
    print(f"  Sub7 pixel data: {PIXEL_SIZE} bytes at offset 0x{PIXEL_OFFSET:X}")

    # ── Deswizzle ──
    print("  Deswizzling (bw_psmt4=256, dbw_ct32=128)...")
    linear = bytearray(deswizzle_psmt4(
        pixel_data, TEX_W, TEX_H,
        bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
    ))
    assert len(linear) == TEX_W * TEX_H

    # ── Verify round-trip on original data ──
    print("  Verifying round-trip on original...")
    reswizzled_check = swizzle_psmt4(
        linear, TEX_W, TEX_H,
        bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
    )
    if bytes(reswizzled_check) == pixel_data:
        print("  Round-trip: PASS")
    else:
        mismatches = sum(1 for a, b in zip(reswizzled_check, pixel_data) if a != b)
        print(f"  Round-trip: WARNING - {mismatches} mismatches (proceeding anyway)")

    # ── Load fonts ──
    font_stat = load_font(size=12, bold=True)    # For stat labels (64px wide)
    font_tab = load_font(size=11, bold=True)      # For tab labels (96px wide)
    font_field = load_font(size=10, bold=True)     # For field labels (36px wide)
    font_input = load_font(size=9, bold=True)      # For input mode (small)
    font_large = load_font(size=14, bold=True)     # For large HP

    # ── Apply patches ──
    patches_applied = 0

    print("\n  Stat labels:")
    for x, y, w, h, text in STAT_LABELS:
        # Clamp height to not exceed texture
        if y + h > TEX_H:
            h = TEX_H - y
        clear_rect(linear, x, y, w, h)
        cell_data = render_label(text, w, h, font_stat)
        patch_rect(linear, x, y, w, h, cell_data)
        print(f"    [{x},{y} {w}x{h}] '{text}'")
        patches_applied += 1

    print("\n  Tab labels:")
    for x, y, w, h, text in TAB_LABELS:
        clear_rect(linear, x, y, w, h)
        cell_data = render_label(text, w, h, font_tab)
        patch_rect(linear, x, y, w, h, cell_data)
        print(f"    [{x},{y} {w}x{h}] '{text}'")
        patches_applied += 1

    print("\n  Input mode labels:")
    for x, y, w, h, text in INPUT_MODE_LABELS:
        clear_rect(linear, x, y, w, h)
        cell_data = render_label(text, w, h, font_input)
        patch_rect(linear, x, y, w, h, cell_data)
        print(f"    [{x},{y} {w}x{h}] '{text}'")
        patches_applied += 1

    print("\n  Chargen field labels:")
    for x, y, w, h, text in CHARGEN_FIELD_LABELS:
        clear_rect(linear, x, y, w, h)
        cell_data = render_label(text, w, h, font_field)
        patch_rect(linear, x, y, w, h, cell_data)
        print(f"    [{x},{y} {w}x{h}] '{text}'")
        patches_applied += 1

    print("\n  Large labels:")
    for x, y, w, h, text in LARGE_LABELS:
        clear_rect(linear, x, y, w, h)
        cell_data = render_label(text, w, h, font_large)
        patch_rect(linear, x, y, w, h, cell_data)
        print(f"    [{x},{y} {w}x{h}] '{text}'")
        patches_applied += 1

    print("\n  Clear-only zones (residual JP):")
    for x, y, w, h in CLEAR_ONLY:
        clear_rect(linear, x, y, w, h)
        print(f"    [{x},{y} {w}x{h}] cleared")

    print(f"\n  Total patches: {patches_applied}")

    # ── Save debug preview ──
    print(f"\n  Saving preview: {PREVIEW_PATH}")
    preview = Image.new("L", (TEX_W, TEX_H))
    for i, p in enumerate(linear[:TEX_W * TEX_H]):
        # 0 (opaque text) -> white(255), 15 (transparent) -> black(0)
        preview.putpixel((i % TEX_W, i // TEX_W), (15 - p) * 17)
    os.makedirs(os.path.dirname(PREVIEW_PATH), exist_ok=True)
    preview.save(PREVIEW_PATH)

    # ── Re-swizzle ──
    print("  Re-swizzling...")
    reswizzled = swizzle_psmt4(
        linear, TEX_W, TEX_H,
        bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
    )
    assert len(reswizzled) == PIXEL_SIZE, \
        f"Reswizzled size mismatch: {len(reswizzled)} != {PIXEL_SIZE}"

    # ── Verify round-trip on patched data ──
    print("  Verifying round-trip on patched data...")
    verify_linear = deswizzle_psmt4(
        bytes(reswizzled), TEX_W, TEX_H,
        bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32
    )
    if bytes(verify_linear) == bytes(linear):
        print("  Patched round-trip: PASS")
    else:
        mismatches = sum(1 for a, b in zip(verify_linear, linear) if a != b)
        print(f"  Patched round-trip: FAIL ({mismatches} pixel mismatches)")
        # Show first few
        shown = 0
        for i, (a, b) in enumerate(zip(verify_linear, linear)):
            if a != b:
                px = i % TEX_W
                py = i // TEX_W
                print(f"    pixel ({px},{py}): got {a}, expected {b}")
                shown += 1
                if shown >= 5:
                    break

    # ── Write patched R2138 ──
    output = bytearray(r2138)  # full copy
    output[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE] = reswizzled
    assert len(output) == EXPECTED_SIZE, \
        f"Output size mismatch: {len(output)} != {EXPECTED_SIZE}"

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(output)
    print(f"\n  Output: {OUTPUT_PATH} ({len(output)} bytes)")

    # Verify no bytes changed outside pixel data range
    before = r2138[:PIXEL_OFFSET]
    after = output[:PIXEL_OFFSET]
    assert before == after, "CORRUPTION: bytes before pixel data changed!"

    after_end = PIXEL_OFFSET + PIXEL_SIZE
    before_tail = r2138[after_end:]
    after_tail = output[after_end:]
    assert before_tail == after_tail, "CORRUPTION: bytes after pixel data changed!"
    print("  Integrity check: PASS (only pixel data modified)")

    print("\nDONE!")
    return True


if __name__ == "__main__":
    main()
