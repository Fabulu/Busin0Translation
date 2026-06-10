#!/usr/bin/env python3
"""
R2138 unified patcher — patches ALL sub-resources with Japanese text.

Sub-resources patched:
  Sub 0  — Town menu (3 labels)
  Sub 4  — SKIPPED (dual-language atlas; patching caused status screen artifacts)
  Sub 6  — Guild/adventurer roster (15 labels)
  Sub 7  — Chargen stat/tab/sidebar labels (25 labels)
  Sub 25 — Level-up screen (7 labels)
  Sub 26 — Shop/alchemy/automaton menus (19 labels)
  Sub 27 — Purchase/curse power (3 labels)

Each sub-resource is a self-contained patch unit: extract pixel data,
deswizzle, render English labels, re-swizzle, write back.

Output: build/packdata_resources/2138_type29.raw
Debug:  build/r2138_sub*_patched_preview.png
"""

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
PREVIEW_DIR = os.path.join(BASE, "build")

# ── Constants ──
EXPECTED_SIZE = 1542144


# ═══════════════════════════════════════════════════════════════════════
# Sub-resource definitions
# ═══════════════════════════════════════════════════════════════════════
# Each sub-resource dict has:
#   offset:       byte offset of sub-resource in R2138
#   pixel_off:    offset of pixel data within the sub-resource
#   pixel_size:   raw pixel data size in bytes
#   tex_w/tex_h:  texture dimensions
#   bw_psmt4:     PSMT4 buffer width
#   dbw_ct32:     CT32 destination buffer width
#   bg_index:     palette index for transparent/background
#   ink_index:    palette index for fully opaque text (ink)
#   labels:       list of (x, y, w, h, text) tuples
#   clear_only:   optional list of (x, y, w, h) regions to clear without text
#   font_size:    default font size for labels
#   name:         human-readable name for debug output

SUB_DEFS = []

# ── Sub 0: Town Menu ──
SUB_DEFS.append({
    "name": "sub0_town_menu",
    "sub_index": 0,
    "offset": 0x1D0,
    "pixel_off": 0x500,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 0, "ink_index": 15,
    "font_size": 12,
    "labels": [
        (29,  2, 70, 20, "Go Outside"),
        (16, 25, 99, 21, "Registry"),
        ( 9, 49, 111, 21, "Guild"),
    ],
    "clear_only": [],
})

# ── Sub 4: Status screen / chargen dual-language atlas ──
# 512x256 PSMT4. Left half = English cursive status labels (already English).
# Right half = Japanese chargen labels. Only 転職条件 (Job Change Requirements)
# at (186,177) needs translation. Previous attempt at wrong coords (210,120)
# caused artifacts — correct location confirmed via deswizzle analysis.
SUB_DEFS.append({
    "name": "sub4_status_tabs",
    "sub_index": 4,
    "offset": 0x4B490,
    "pixel_off": 0x900,
    "pixel_size": 65536,
    "tex_w": 512, "tex_h": 256,
    "bw_psmt4": 512, "dbw_ct32": 256,
    "bg_index": 0, "ink_index": 15,
    "font_size": 11,
    "labels": [
        (186, 177, 64, 17, "Class Req"),
    ],
    "clear_only": [],
})

# ── Sub 6: Guild Roster ──
SUB_DEFS.append({
    "name": "sub6_guild_roster",
    "sub_index": 6,
    "offset": 0x6C910,
    "pixel_off": 0x800,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 0, "ink_index": 15,
    "font_size": 12,
    # overlay REMOVED: sub6 has bg=0 (transparent), ink strokes at high values (8-15).
    # The "metallic banner" appearance was actually just anti-aliased Japanese kanji
    # strokes, not a background texture. Normal clear (fill with bg=0) + render is correct.
    # The banner bar itself is in a separate texture layer rendered by the game engine.
    "labels": [
        # Guild menu (large, left column)
        ( 7,   1, 108, 22, "Adv. Roster"),
        ( 7,  24, 108, 23, "Change Class"),
        ( 7,  49, 108, 22, "Join Party"),
        ( 7,  74, 109, 21, "Leave Party"),
        (16,  96,  86, 24, "Delete"),
        (18, 121,  86, 22, "Swap Roster"),
        (16, 145,  88, 23, "New Character", 14),
        (28, 170,  63, 21, "Rename"),
        (27, 193,  66, 22, "Purchase"),
        # Button prompts (right column, smaller)
        (129,  76, 84, 17, "[] Swap"),
        (128, 100, 85, 17, "/\\ Info"),
        # Action arrows (right column)
        (130, 144, 126, 19, "<Join Party>"),
        (130, 166, 101, 17, "<Leave Party>"),
        (139, 185,  83, 18, "<Delete>"),
        (139, 205,  83, 18, "<Swap>"),
    ],
    "clear_only": [],
})

# ── Sub 7: Chargen stat/tab/sidebar labels ──
SUB_DEFS.append({
    "name": "sub7_chargen_stats",
    "sub_index": 7,
    "offset": 0x075510,
    "pixel_off": 0xC0,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 15, "ink_index": 0,
    "font_size": 12,
    "labels": [
        # Stat labels (right side)
        # NOTE: HP/MAX at (192,13)-(256,31) is ALREADY English in the original
        # Japanese game — do NOT overwrite it or it shows garbled text.
        (192,  80, 64, 16, "Str"),
        (192, 100, 64, 16, "Int"),
        (192, 120, 64, 16, "Pie"),
        (192, 140, 64, 16, "Vit"),
        (192, 160, 64, 16, "Agi"),
        (192, 180, 64, 16, "Lck"),
        (192, 200, 48, 16, "Atk"),
        (194, 221, 45, 15, "Eva"),
        (194, 241, 45, 15, "Def"),
        # Tab labels (top-left) — 20px grid matching sidebar pattern
        # Game reads UV blocks: (0,0-20), (0,20-40), (0,40-60), (0,60-80), (0,80-100)
        (  0,   0, 96, 20, "Basic Info"),
        (  0,  20, 96, 20, "Details"),
        (  0,  40, 96, 20, "Item"),
        (  0,  60, 96, 20, "Mage Magic"),
        (  0,  80, 96, 20, "Prs. Magic"),
        # Input mode buttons — 20px grid, width covers JP glyph extent (x=96-128)
        ( 96,   0, 32, 20, "Kana"),
        ( 96,  20, 32, 20, "Hira"),
        ( 96,  40, 32, 20, "ABC"),
        ( 96,  60, 32, 20, "Sym"),
        # Chargen field labels — UV coords: (136,0)-(184,20) etc., 48px wide
        # Clear old JP area (x=110-170) then render English in UV area (x=136-184)
        # Left-aligned (6th element = alignment)
        (136,   0, 48, 20, "Sex"),
        (136,  20, 48, 20, "Race"),
        (136,  40, 48, 20, "Align"),
        (136,  60, 48, 20, "Class"),
        # OK button — UV: (88,88)-(128,112) = 40x24
        ( 88,  88, 40, 24, "OK"),
        # Large HP REMOVED — overlapped OK button (x=110..150,y=80..100
        # vs OK x=88..128,y=88..112), causing garbled text.
        # HP/MAX at UV (192,20) is already English in the original game.
    ],
    "clear_only": [
        # Residual JP below Priest Magic (y=100-112)
        (0, 100, 96, 12),
        # Clear old input mode area below !@ (y=80-100)
        (96, 80, 40, 20),
        # Clear old JP field labels area (x=110-135) that is outside new UV rect
        (110, 0, 26, 100),
        # Clear residual JP in OK/HP area (y=78-100 covers old HP region too)
        (86, 78, 66, 22),
    ],
})

# ── Sub 25: Level Up ──
SUB_DEFS.append({
    "name": "sub25_level_up",
    "sub_index": 25,
    "offset": 0x15C4D0,
    "pixel_off": 0x6E0,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 0, "ink_index": 15,
    "font_size": 12,
    "labels": [
        # Large anti-aliased text
        (  4, 176, 118, 41, "Level Up!!"),
        (  5, 224, 116, 30, "Skill Up!!"),
        # Small text groups
        (144, 198,  44, 19, "Everyone"),
        ( 35, 151,  32, 16, "All"),
        (144, 176,  44, 16, "Next"),
        # Panel right text (unknown kanji phrase — clear area)
        (132, 155,  73, 11, ""),
    ],
    "clear_only": [],
})

# ── Sub 26: Shop/Alchemy/Automaton ──
SUB_DEFS.append({
    "name": "sub26_shop_alchemy",
    "sub_index": 26,
    "offset": 0x164DB0,
    "pixel_off": 0x500,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 0, "ink_index": 15,
    "font_size": 12,
    "labels": [
        # Left column
        ( 29,   0,  70, 22, "Go Outside"),
        ( 12,  24, 101, 21, "Magic Stones"),
        ( 42,  48,  44, 21, "Synthesize"),
        ( 43,  72,  44, 22, "Disassemble"),
        ( 17,  97,  96, 20, "Automaton"),
        ( 42, 120,  45, 22, "Buy"),
        ( 44, 145,  42, 21, "Enhance"),
        ( 19, 168,  93, 20, "Customize"),
        ( 16, 192, 101, 21, "Brain Chip"),
        ( 17, 216, 100, 21, "Body Chip"),
        # Right column
        (144,   0, 101, 22, "Hand Chip"),
        (147,  24,  97, 21, "Arm Chip"),
        (147,  48,  98, 21, "Leg Chip"),
        (154,  72,  79, 22, "Shop"),
        (170,  97,  45, 20, "Buy"),
        (171, 120,  43, 22, "Sell"),
        (137, 145, 113, 21, "Alchemy Guild"),
        (136, 192, 113, 21, "Buy Automaton"),
        (136, 216, 112, 21, "Enhance Auto."),
    ],
    "clear_only": [],
})

# ── Sub 27: Purchase/Curse ──
SUB_DEFS.append({
    "name": "sub27_purchase_curse",
    "sub_index": 27,
    "offset": 0x16D4F0,
    "pixel_off": 0x740,
    "pixel_size": 32768,
    "tex_w": 256, "tex_h": 256,
    "bw_psmt4": 256, "dbw_ct32": 128,
    "bg_index": 0, "ink_index": 15,
    "font_size": 11,
    "labels": [
        (171, 110,  76, 18, "Total Price"),
        (125, 218,  90, 14, "Curse Pwr"),
        (125, 234, 110, 14, "Req. Curse Pwr"),
    ],
    "clear_only": [],
})


# ═══════════════════════════════════════════════════════════════════════
# Rendering utilities
# ═══════════════════════════════════════════════════════════════════════

_font_cache = {}

def load_font(size=12, bold=True):
    """Load a suitable font for rendering labels (cached)."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    if bold:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]
    font = None
    for fp in candidates:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, size)
            break
    if font is None:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def render_label(text, width, height, font, bg_index=15, ink_index=0, align="center"):
    """Render text in a rectangle, returning palette indices.

    bg_index:  palette index for transparent background
    ink_index: palette index for fully opaque text
    align:     "center" (default) or "left"
    """
    if not text:
        return [bg_index] * (width * height)

    # Auto-shrink if text too wide
    cur_font = font
    bbox = cur_font.getbbox(text)
    if bbox:
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
        if align == "left":
            ox = 1 - bbox[0]  # 1px left margin
        else:
            ox = max(0, (width - tw) // 2) - bbox[0]
        oy = max(0, (height - th) // 2) - bbox[1]
        draw.text((ox, oy), text, fill=255, font=cur_font)

    pixels = list(img.getdata())
    result = []

    if ink_index < bg_index:
        # Convention: 0=ink, 15=transparent (sub0, sub6, sub7, sub26)
        for val in pixels:
            if val == 0:
                result.append(bg_index)
            else:
                game_val = bg_index - min(val * bg_index // 255, bg_index)
                if game_val == bg_index:
                    game_val = bg_index - 1
                result.append(game_val)
    else:
        # Convention: 0=transparent, 15=ink (sub4, sub25, sub27)
        for val in pixels:
            if val == 0:
                result.append(bg_index)
            else:
                game_val = min(val * ink_index // 255, ink_index)
                if game_val == bg_index:
                    game_val = bg_index + 1 if ink_index > bg_index else bg_index - 1
                result.append(game_val)

    return result


def patch_rect(linear_pixels, x, y, w, h, cell_data, tex_w, overlay_bg=None):
    """Write cell_data into the linear pixel array at arbitrary rectangle.

    If overlay_bg is set to a palette index, only pixels where cell_data
    differs from that index are written — preserving the original background.
    """
    tex_h = len(linear_pixels) // tex_w
    for dy in range(h):
        for dx in range(w):
            py = y + dy
            px = x + dx
            if 0 <= px < tex_w and 0 <= py < tex_h:
                val = cell_data[dy * w + dx]
                if overlay_bg is not None and val == overlay_bg:
                    continue  # skip transparent pixels, keep original background
                idx = py * tex_w + px
                linear_pixels[idx] = val


def clear_rect(linear_pixels, x, y, w, h, bg_index, tex_w):
    """Fill rectangle with background index."""
    tex_h = len(linear_pixels) // tex_w
    for dy in range(h):
        for dx in range(w):
            py = y + dy
            px = x + dx
            if 0 <= px < tex_w and 0 <= py < tex_h:
                linear_pixels[py * tex_w + px] = bg_index


def save_preview(linear_pixels, tex_w, tex_h, path, bg_index, ink_index):
    """Save a debug grayscale preview PNG."""
    preview = Image.new("L", (tex_w, tex_h))
    for i, p in enumerate(linear_pixels[:tex_w * tex_h]):
        if ink_index < bg_index:
            # 0=ink(white) -> 255, 15=bg(black) -> 0
            brightness = (bg_index - p) * 255 // bg_index if bg_index > 0 else 0
        else:
            # 0=bg(black) -> 0, 15=ink(white) -> 255
            brightness = p * 255 // ink_index if ink_index > 0 else 0
        brightness = max(0, min(255, brightness))
        preview.putpixel((i % tex_w, i // tex_w), brightness)
    preview.save(path)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def patch_sub(r2138, sub_def):
    """Patch a single sub-resource. Modifies r2138 in place."""
    name = sub_def["name"]
    offset = sub_def["offset"]
    pixel_off = sub_def["pixel_off"]
    pixel_size = sub_def["pixel_size"]
    tex_w = sub_def["tex_w"]
    tex_h = sub_def["tex_h"]
    bw = sub_def["bw_psmt4"]
    dbw = sub_def["dbw_ct32"]
    bg_idx = sub_def["bg_index"]
    ink_idx = sub_def["ink_index"]
    labels = sub_def["labels"]
    clear_zones = sub_def.get("clear_only", [])
    font_size = sub_def.get("font_size", 12)
    overlay = sub_def.get("overlay", False)

    abs_pixel_offset = offset + pixel_off
    print(f"\n--- {name} (sub {sub_def['sub_index']}) ---")
    print(f"  Pixel data: {pixel_size} bytes at 0x{abs_pixel_offset:X}")
    print(f"  Texture: {tex_w}x{tex_h}, bw={bw}, dbw={dbw}")
    print(f"  Palette: bg={bg_idx}, ink={ink_idx}")

    # Extract pixel data
    pixel_data = bytes(r2138[abs_pixel_offset:abs_pixel_offset + pixel_size])
    assert len(pixel_data) == pixel_size, \
        f"Pixel data truncated: {len(pixel_data)} < {pixel_size}"

    # Deswizzle
    linear = bytearray(deswizzle_psmt4(
        pixel_data, tex_w, tex_h, bw_psmt4=bw, dbw_ct32=dbw
    ))
    expected_linear = tex_w * tex_h
    assert len(linear) == expected_linear, \
        f"Deswizzled size mismatch: {len(linear)} != {expected_linear}"

    # Verify round-trip
    reswizzled_check = swizzle_psmt4(
        linear, tex_w, tex_h, bw_psmt4=bw, dbw_ct32=dbw
    )
    if bytes(reswizzled_check) == pixel_data:
        print("  Round-trip: PASS")
    else:
        mismatches = sum(1 for a, b in zip(reswizzled_check, pixel_data) if a != b)
        print(f"  Round-trip: WARNING - {mismatches} mismatches (proceeding)")

    # Load font
    font = load_font(size=font_size, bold=True)

    # Clear-only zones
    for x, y, w, h in clear_zones:
        clear_rect(linear, x, y, w, h, bg_idx, tex_w)
        print(f"  Cleared [{x},{y} {w}x{h}]")

    # Build sorted label list for gap-clearing (stat labels bleed fix)
    # For each label, clear down to the next label's top y at the same x
    # to eliminate white bleed from the label below
    sorted_by_x_y = sorted(enumerate(labels), key=lambda t: (t[1][0], t[1][1]))

    # Render labels
    count = 0
    for label_entry in labels:
        # Support 5-tuple (x,y,w,h,text), 6-tuple with align string or font size int
        x, y, w, h, text = label_entry[:5]
        label_align = "center"
        label_font_size = None
        if len(label_entry) > 5:
            extra = label_entry[5]
            if isinstance(extra, str):
                label_align = extra
            elif isinstance(extra, int):
                label_font_size = extra

        # Clamp to texture bounds
        if y + h > tex_h:
            h = tex_h - y
        if x + w > tex_w:
            w = tex_w - x
        if h <= 0 or w <= 0:
            continue

        # Find the next label at the same x to determine gap
        next_y = None
        for _, entry in sorted_by_x_y:
            ox, oy = entry[0], entry[1]
            if ox == x and oy > y:
                next_y = oy
                break

        # Clear the full zone including any gap to next label
        # In overlay mode, skip clearing to preserve background texture
        clear_h = h
        if not overlay:
            if next_y is not None and next_y > y:
                clear_h = min(next_y - y, tex_h - y)
            clear_rect(linear, x, y, w, clear_h, bg_idx, tex_w)

        if text:
            label_font = load_font(size=label_font_size, bold=True) if label_font_size else font
            cell_data = render_label(text, w, h, label_font, bg_idx, ink_idx, align=label_align)
            if overlay:
                patch_rect(linear, x, y, w, h, cell_data, tex_w, overlay_bg=bg_idx)
            else:
                patch_rect(linear, x, y, w, h, cell_data, tex_w)
        count += 1
        tag = f"'{text}'" if text else "(clear)"
        if overlay:
            extra = " (overlay)"
        elif clear_h > h:
            extra = f" (cleared {clear_h}px)"
        else:
            extra = ""
        print(f"  [{x},{y} {w}x{h}] {tag}{extra}")

    print(f"  Labels patched: {count}")

    # Save preview
    preview_path = os.path.join(PREVIEW_DIR, f"r2138_{name}_preview.png")
    save_preview(linear, tex_w, tex_h, preview_path, bg_idx, ink_idx)
    print(f"  Preview: {preview_path}")

    # Re-swizzle
    reswizzled = swizzle_psmt4(
        linear, tex_w, tex_h, bw_psmt4=bw, dbw_ct32=dbw
    )
    assert len(reswizzled) == pixel_size, \
        f"Re-swizzled size mismatch: {len(reswizzled)} != {pixel_size}"

    # Verify patched round-trip
    verify = deswizzle_psmt4(
        bytes(reswizzled), tex_w, tex_h, bw_psmt4=bw, dbw_ct32=dbw
    )
    if bytes(verify) == bytes(linear):
        print("  Patched round-trip: PASS")
    else:
        mismatches = sum(1 for a, b in zip(verify, linear) if a != b)
        print(f"  Patched round-trip: FAIL ({mismatches} mismatches)")

    # Write back into r2138
    r2138[abs_pixel_offset:abs_pixel_offset + pixel_size] = reswizzled
    return count


def main():
    print("=" * 60)
    print("  R2138 Unified Patcher — All Sub-Resources")
    print("=" * 60)

    # Read R2138
    print(f"\nReading R2138 from {INPUT_PATH}...")
    with open(INPUT_PATH, "rb") as f:
        r2138 = bytearray(f.read())
    assert len(r2138) == EXPECTED_SIZE, \
        f"R2138 size mismatch: {len(r2138)} != {EXPECTED_SIZE}"
    print(f"  Size: {len(r2138)} bytes (OK)")

    # Keep original for integrity check
    original = bytes(r2138)

    # Patch all sub-resources
    total_labels = 0
    total_subs = 0
    patched_ranges = []

    for sub_def in SUB_DEFS:
        abs_start = sub_def["offset"] + sub_def["pixel_off"]
        abs_end = abs_start + sub_def["pixel_size"]
        count = patch_sub(r2138, sub_def)
        total_labels += count
        total_subs += 1
        patched_ranges.append((abs_start, abs_end))

    # Integrity check: verify ONLY pixel data regions were modified
    print("\n--- Integrity Check ---")
    for byte_idx in range(len(r2138)):
        if r2138[byte_idx] != original[byte_idx]:
            in_range = any(s <= byte_idx < e for s, e in patched_ranges)
            if not in_range:
                print(f"  CORRUPTION at byte 0x{byte_idx:X}!")
                sys.exit(1)
    print("  Integrity: PASS (only pixel data regions modified)")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(r2138)
    print(f"\n  Output: {OUTPUT_PATH} ({len(r2138)} bytes)")

    print(f"\n{'=' * 60}")
    print(f"  DONE: {total_subs} sub-resources, {total_labels} labels patched")
    print(f"{'=' * 60}")
    return True


if __name__ == "__main__":
    main()
