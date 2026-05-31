#!/usr/bin/env python3
"""
Comprehensive R1188 patcher: ALL name-entry / character-creation screen edits.

Handles in a SINGLE pass:
  1. Kana cell overwriting (hiragana/katakana -> romaji in keyboard grid)
  2. Pre-rendered English labels in empty atlas rows (y>=1009)
  3. PCSX2 texture replacement PNGs (emulator-only overlay approach)

Categories of labels patched:
  - Stat labels:   Strength, IQ, Piety, Vitality, Agility, Luck
  - Sidebar labels: Gender, Class, Race, Align
  - Tab labels:    Kana, Hira, ABC, Sym
  - Gender symbols: M.Name, F.Name
  - Banner text:   New Character
  - Buttons:       OK, Delete, Clear

R1188 layout:
  Format:   PSMT4 1024x1024 (4bpp, 16 palette entries)
  Header:   3072 bytes (0xC00) in .bin, +0x10 outer container in .raw
  Pixels:   524,288 bytes
  Deswizzle: dbw_ct32=512, bw_psmt4=1024
  Round-trip verified.
"""
import sys
import os
import io

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed.  Run:  pip install Pillow")
    sys.exit(1)

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
BIN_PATH    = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
RAW_PATH    = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
OUT_PATH    = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
DEBUG_DIR   = os.path.join(BASE, "build", "textures_to_edit")
REPLACE_DIR = os.path.join(BASE, "build", "pcsx2_texture_replacements")

SECTOR      = 2048
HEADER_SIZE = 0xC00   # 3072 bytes
TEX_W       = 1024
TEX_H       = 1024
DBW_CT32    = 512
BW_PSMT4    = 1024

# ---------------------------------------------------------------------------
# PCSX2 texture replacement hashes
# ---------------------------------------------------------------------------
CLUT_HASH       = '3cb39bf7659ef15f'
CLUT_HASH_TITLE = 'e786e0650b284c64'
GS_PAGE         = '00002214'

PCSX2_TAB_LABELS_48x20 = {
    '16625baf9feaeafb': 'Gender',    # 性別
    '19a39fbc8a08d7ec': 'Sym',       # 記号
    '1f839869fab251d':  'Kana',      # カナ
    '6f1fb24fad5cd1a':  'ABC',       # 英数
    '88ff8b577084a2a8': 'Class',     # 職業
    '9677cb23da53ff88': 'Hira',      # かな
    '9bec87b4031a7172': 'Race',      # 種族
    'c89b469f7a152a6':  'Align',     # 属性
}

PCSX2_BUTTONS_40x24 = {
    'd09a04bdfaf715bc': 'OK',        # 決定
}

PCSX2_TITLE_120x24 = {
    'a2d3fce36c8c719d': 'New Character',  # 新規登録
}

PCSX2_STAT_LABELS_64x16 = {
    '280ea82c1c476a98': 'Luck',      # 幸運度
    '4841ef9a2dc4981':  'Agility',   # 敏捷度
    '5d0c6327e20384e7': 'Vitality',  # 生命力
    'aa43f966ad69195e': 'Piety',     # 信仰心
    'bb20512b10c3128b': 'IQ',        # 知恵
    'f2013a64642252e3': 'Strength',  # 力
}

# ---------------------------------------------------------------------------
# Kana cell map  (y0, y1, x0, x1, jp_label, en_replacement)
#
# Each entry is one glyph cell in the deswizzled atlas.
# The cell is cleared and the English replacement rendered in its place.
# ---------------------------------------------------------------------------

# Row 2 left (y=48-71): first 5 are symbols (kept), then hiragana a-se
HIRAGANA_ROW2 = [
    # Symbols at cells 0-5 are left alone (useful punctuation/arrows)
    # Hiragana begins at cell 6 (after the gap)
    (48, 72, 161, 180, "a",  "a"),
    (48, 72, 187, 195, "i",  "i"),
    (48, 72, 198, 205, "u",  "u"),
    (48, 72, 212, 225, "e",  "e"),
    (48, 72, 233, 251, "o",  "o"),
    (48, 72, 256, 278, "ka", "ka"),
    (48, 72, 281, 302, "ki", "ki"),
    (48, 72, 308, 325, "ku", "ku"),
    (48, 72, 333, 346, "ke", "ke"),
    (48, 72, 355, 374, "ko", "ko"),
    (48, 72, 380, 394, "sa", "sa"),
    (48, 72, 403, 419, "si", "si"),
    (48, 72, 428, 444, "su", "su"),
    (48, 72, 449, 470, "se", "se"),
    (48, 72, 473, 494, "so", "so"),
]

# Row 3 left (y=72-95): hiragana ya-zo
HIRAGANA_ROW3 = [
    (72, 96,   0,  14, "ya", "ya"),
    (72, 96,  18,  37, "yu", "yu"),
    (72, 96,  42,  59, "yo", "yo"),
    (72, 96,  68,  83, "ra", "ra"),
    (72, 96,  94, 106, "ri", "ri"),
    (72, 96, 114, 130, "ru", "ru"),
    (72, 96, 137, 159, "re", "re"),
    (72, 96, 163, 181, "ro", "ro"),
    (72, 96, 185, 206, "wo", "wo"),
    (72, 96, 211, 230, "n",  "n"),
    (72, 96, 233, 254, "ga", "ga"),
    (72, 96, 257, 278, "gi", "gi"),
    (72, 96, 283, 303, "gu", "gu"),
    (72, 96, 307, 325, "ge", "ge"),
    (72, 96, 329, 351, "go", "go"),
    (72, 96, 354, 374, "za", "za"),
    (72, 96, 379, 399, "ji", "ji"),
    (72, 96, 405, 420, "zu", "zu"),
    (72, 96, 426, 447, "ze", "ze"),
    (72, 96, 449, 471, "zo", "zo"),
]

# Row 4 left (y=96-119): small kana + katakana A-Chi
KATAKANA_ROW4_LEFT = [
    (96, 120,   0,  16, "e",  "e"),
    (96, 120,  18,  41, "o",  "o"),
    (96, 120,  42,  64, "tt", "tt"),
    (96, 120,  68,  90, "vu", "vu"),
    (96, 120,  91, 113, "A",  "A"),
    (96, 120, 114, 139, "I",  "I"),
    (96, 120, 140, 159, "U",  "U"),
    (96, 120, 160, 183, "E",  "E"),
    (96, 120, 184, 208, "O",  "O"),
    (96, 120, 209, 234, "Ka", "Ka"),
    (96, 120, 235, 257, "Ki", "Ki"),
    (96, 120, 258, 280, "Ku", "Ku"),
    (96, 120, 281, 306, "Ke", "Ke"),
    (96, 120, 307, 329, "Ko", "Ko"),
    (96, 120, 330, 353, "Sa", "Sa"),
    (96, 120, 354, 376, "Si", "Si"),
    (96, 120, 377, 402, "Su", "Su"),
    (96, 120, 403, 426, "Se", "Se"),
    (96, 120, 427, 450, "So", "So"),
    (96, 120, 451, 473, "Ta", "Ta"),
    (96, 120, 474, 496, "Ti", "Ti"),
]

# Row 4 right (y=96-119, x=512+): katakana Tu-Mo
KATAKANA_ROW4_RIGHT = [
    (96, 120, 512, 535, "Tu", "Tu"),
    (96, 120, 536, 559, "Te", "Te"),
    (96, 120, 560, 583, "To", "To"),
    (96, 120, 584, 607, "Na", "Na"),
    (96, 120, 608, 631, "Ni", "Ni"),
    (96, 120, 632, 655, "Nu", "Nu"),
    (96, 120, 656, 679, "Ne", "Ne"),
    (96, 120, 680, 703, "No", "No"),
    (96, 120, 704, 727, "Ha", "Ha"),
    (96, 120, 728, 751, "Hi", "Hi"),
    (96, 120, 752, 775, "Hu", "Hu"),
    (96, 120, 776, 799, "He", "He"),
    (96, 120, 800, 823, "Ho", "Ho"),
    (96, 120, 824, 847, "Ma", "Ma"),
    (96, 120, 848, 871, "Mi", "Mi"),
    (96, 120, 872, 895, "Mu", "Mu"),
    (96, 120, 896, 919, "Me", "Me"),
    (96, 120, 920, 943, "Mo", "Mo"),
]

# Row 5 left (y=120-143): katakana Ra-Du
KATAKANA_ROW5_LEFT = [
    (120, 144,   0,  19, "Ra", "Ra"),
    (120, 144,  20,  39, "Ri", "Ri"),
    (120, 144,  40,  67, "Ru", "Ru"),
    (120, 144,  68,  92, "Re", "Re"),
    (120, 144,  93, 115, "Ro", "Ro"),
    (120, 144, 116, 139, "Wa", "Wa"),
    (120, 144, 140, 161, "N",  "N"),
    (120, 144, 162, 183, "Ga", "Ga"),
    (120, 144, 184, 209, "Gi", "Gi"),
    (120, 144, 210, 233, "Gu", "Gu"),
    (120, 144, 234, 256, "Ge", "Ge"),
    (120, 144, 257, 282, "Go", "Go"),
    (120, 144, 283, 305, "Za", "Za"),
    (120, 144, 306, 329, "Ji", "Ji"),
    (120, 144, 330, 351, "Zu", "Zu"),
    (120, 144, 352, 377, "Ze", "Ze"),
    (120, 144, 378, 401, "Zo", "Zo"),
    (120, 144, 402, 424, "Da", "Da"),
    (120, 144, 425, 449, "Di", "Di"),
    (120, 144, 450, 473, "Du", "Du"),
]

# Row 5 right (y=120-143, x=512+): remaining katakana
KATAKANA_ROW5_RIGHT = [
    (120, 144, 512, 535, "De", "De"),
    (120, 144, 536, 559, "Do", "Do"),
    (120, 144, 560, 583, "Ba", "Ba"),
    (120, 144, 584, 607, "Bi", "Bi"),
    (120, 144, 608, 631, "Bu", "Bu"),
    (120, 144, 632, 655, "Be", "Be"),
    (120, 144, 656, 679, "Bo", "Bo"),
    (120, 144, 680, 703, "Pa", "Pa"),
    (120, 144, 704, 727, "Pi", "Pi"),
    (120, 144, 728, 751, "Pu", "Pu"),
    (120, 144, 752, 775, "Pe", "Pe"),
    (120, 144, 776, 799, "Po", "Po"),
]

# Combine all kana cells
ALL_KANA_CELLS = (
    HIRAGANA_ROW2 + HIRAGANA_ROW3 +
    KATAKANA_ROW4_LEFT + KATAKANA_ROW4_RIGHT +
    KATAKANA_ROW5_LEFT + KATAKANA_ROW5_RIGHT
)

# ---------------------------------------------------------------------------
# Bottom-area English labels (y=1009+, empty space in original atlas)
# These are pre-rendered for future EXE UV-redirect patching.
# ---------------------------------------------------------------------------
BOTTOM_LABELS = [
    # Tab labels
    (1009, 1020,   0,  47, "tab:kana",      "Kana"),
    (1009, 1020,  50,  97, "tab:hira",      "Hira"),
    (1009, 1020, 100, 147, "tab:abc",       "ABC"),
    (1009, 1020, 150, 197, "tab:sym",       "Sym"),
    # Buttons
    (1009, 1020, 200, 239, "btn:ok",        "OK"),
    # Gender name labels
    (1009, 1020, 242, 289, "lbl:mname",     "M.Name"),
    (1009, 1020, 292, 339, "lbl:fname",     "F.Name"),
    # Action buttons
    (1009, 1020, 342, 389, "btn:delete",    "Delete"),
    (1009, 1020, 392, 439, "btn:clear",     "Clear"),
    # Banner
    (1009, 1020, 450, 569, "banner",        "New Character"),
    # Stat labels
    (1009, 1020, 572, 635, "stat:str",      "Strength"),
    (1009, 1020, 638, 701, "stat:iq",       "IQ"),
    (1009, 1020, 704, 767, "stat:piety",    "Piety"),
    (1009, 1020, 770, 833, "stat:vit",      "Vitality"),
    (1009, 1020, 836, 899, "stat:agi",      "Agility"),
    (1009, 1020, 902, 965, "stat:luck",     "Luck"),
    # Sidebar labels
    (1009, 1020, 0,   47, "side:gender",    "Gender"),   # shares space -- overwritten last
    (1009, 1020, 50,  97, "side:class",     "Class"),
    (1009, 1020, 100, 147, "side:race",     "Race"),
    (1009, 1020, 150, 197, "side:align",    "Align"),
]

# De-duplicate: later entries for same (x0,y0) overwrite earlier ones.
# Build a dict keyed by (y0, x0) so last one wins.
_bottom_dedup = {}
for entry in BOTTOM_LABELS:
    key = (entry[0], entry[2])  # (y0, x0)
    _bottom_dedup[key] = entry
BOTTOM_LABELS_DEDUP = list(_bottom_dedup.values())


# ---------------------------------------------------------------------------
# Font / rendering
# ---------------------------------------------------------------------------

def get_font(size=10):
    """Return a TrueType font for rendering into atlas cells."""
    for path in [
        "C:/Windows/Fonts/consola.ttf",   # Consolas -- monospace, crisp
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_text_indices(text, width, height, font_size=10, max_index=15):
    """Render *text* centred in a (width x height) box.

    Returns a 2-D numpy array of palette indices (0 = transparent,
    *max_index* = fully opaque).
    """
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Shrink font if text is too wide
    while tw > width - 2 and font_size > 6:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=255, font=font)

    arr = np.array(img)
    out = np.round(arr * max_index / 255).astype(np.uint8)
    return out


def render_label_rgba(text, width, height, font_size=14):
    """Render English label as white-on-transparent RGBA for PCSX2 replacement."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    while tw > width - 4 and font_size > 7:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Quantise alpha to PS2's 16 levels
    ps2_alphas = [0, 11, 19, 28, 36, 44, 52, 60,
                  69, 77, 85, 93, 102, 110, 118, 128]
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


# ---------------------------------------------------------------------------
# Phase 1: Overwrite kana cells with romaji
# ---------------------------------------------------------------------------

def patch_kana_cells(linear, cells, font_size=11):
    """Clear each kana cell and render its romaji replacement.

    *linear* is a 1-D bytearray of palette indices for 1024x1024 pixels.
    Modified in place.
    """
    edits = 0
    for y0, y1, x0, x1, _jp, en in cells:
        w = x1 - x0 + 1
        h = y1 - y0
        if w < 1 or h < 1:
            continue

        # Clear the cell
        for dy in range(h):
            for dx in range(w):
                px = x0 + dx
                py = y0 + dy
                if 0 <= px < TEX_W and 0 <= py < TEX_H:
                    idx = py * TEX_W + px
                    if linear[idx] != 0:
                        linear[idx] = 0
                        edits += 1

        # Render English replacement
        indices = render_text_indices(en, w, h, font_size=font_size)
        for dy in range(h):
            for dx in range(w):
                px = x0 + dx
                py = y0 + dy
                if 0 <= px < TEX_W and 0 <= py < TEX_H:
                    val = int(indices[dy, dx])
                    if val > 0:
                        linear[py * TEX_W + px] = val
                        edits += 1
    return edits


# ---------------------------------------------------------------------------
# Phase 2: Bottom-row English labels
# ---------------------------------------------------------------------------

def patch_bottom_labels(linear, labels, font_size=9):
    """Render English label sprites into the empty bottom rows."""
    edits = 0
    for y0, y1, x0, x1, _tag, en in labels:
        w = x1 - x0 + 1
        h = y1 - y0
        if w < 1 or h < 1:
            continue
        indices = render_text_indices(en, w, h, font_size=font_size)
        for dy in range(h):
            for dx in range(w):
                px = x0 + dx
                py = y0 + dy
                if 0 <= px < TEX_W and 0 <= py < TEX_H:
                    old = linear[py * TEX_W + px]
                    new = int(indices[dy, dx])
                    if new != old:
                        linear[py * TEX_W + px] = new
                        edits += 1
    return edits


# ---------------------------------------------------------------------------
# Phase 3: PCSX2 texture replacements
# ---------------------------------------------------------------------------

def create_pcsx2_replacements():
    """Create PCSX2 texture replacement PNG files for emulator overlay."""
    os.makedirs(REPLACE_DIR, exist_ok=True)
    count = 0

    # Tab labels (48x20)
    for hash1, english in PCSX2_TAB_LABELS_48x20.items():
        filename = f"{hash1}-{CLUT_HASH}-r48x20-{GS_PAGE}.png"
        img = render_label_rgba(english, 48, 20)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # Buttons (40x24)
    for hash1, english in PCSX2_BUTTONS_40x24.items():
        filename = f"{hash1}-{CLUT_HASH}-r40x24-{GS_PAGE}.png"
        img = render_label_rgba(english, 40, 24)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # Title/banner (120x24)
    for hash1, english in PCSX2_TITLE_120x24.items():
        filename = f"{hash1}-{CLUT_HASH_TITLE}-r120x24-{GS_PAGE}.png"
        img = render_label_rgba(english, 120, 24)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # Stat labels (64x16)
    for hash1, english in PCSX2_STAT_LABELS_64x16.items():
        filename = f"{hash1}-{CLUT_HASH}-r64x16-{GS_PAGE}.png"
        img = render_label_rgba(english, 64, 16)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    return count


# ---------------------------------------------------------------------------
# Debug visualisation
# ---------------------------------------------------------------------------

def save_debug_image(linear, path, y_range=None, zoom=2):
    """Save a greyscale visualisation of the atlas (or a slice)."""
    if y_range:
        y0, y1 = y_range
    else:
        y0, y1 = 0, TEX_H
    h = y1 - y0
    img = Image.new("L", (TEX_W, h))
    for y in range(h):
        for x in range(TEX_W):
            v = linear[(y0 + y) * TEX_W + x]
            img.putpixel((x, y), v * 17)
    img = img.resize((TEX_W * zoom, h * zoom), Image.NEAREST)
    img.save(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  R1188 Comprehensive Patcher")
    print("  (stat labels, sidebar, gender, banner, tabs, kana)")
    print("=" * 60)
    print()

    # ---- Load source ----
    if os.path.exists(BIN_PATH):
        src_path = BIN_PATH
        header_size = HEADER_SIZE
    elif os.path.exists(RAW_PATH):
        src_path = RAW_PATH
        header_size = HEADER_SIZE + 0x10
    else:
        print(f"ERROR: source file not found ({BIN_PATH} / {RAW_PATH})")
        sys.exit(1)

    data = open(src_path, "rb").read()
    header = data[:header_size]
    pixel_data = data[header_size:header_size + TEX_W * TEX_H // 2]

    print(f"  Source   : {src_path}")
    print(f"  Size     : {len(data)} bytes  (header={header_size}, pixels={len(pixel_data)})")

    # ---- Deswizzle ----
    print("  Deswizzling 1024x1024 PSMT4 (dbw_ct32=512) ...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    linear = bytearray(linear)

    # ---- Phase 1: kana cell overwriting ----
    print(f"\n  Phase 1: Overwriting {len(ALL_KANA_CELLS)} kana cells with romaji ...")
    edits1 = patch_kana_cells(linear, ALL_KANA_CELLS, font_size=11)
    print(f"           {edits1} pixel edits")

    # ---- Phase 2: bottom-row English labels ----
    print(f"\n  Phase 2: Rendering {len(BOTTOM_LABELS_DEDUP)} bottom-row labels ...")
    edits2 = patch_bottom_labels(linear, BOTTOM_LABELS_DEDUP, font_size=9)
    print(f"           {edits2} pixel edits")

    # ---- Phase 3: PCSX2 texture replacements ----
    print(f"\n  Phase 3: Creating PCSX2 texture replacement PNGs ...")
    pcsx2_count = create_pcsx2_replacements()
    print(f"           {pcsx2_count} replacement files in {REPLACE_DIR}")

    # ---- Debug images ----
    os.makedirs(DEBUG_DIR, exist_ok=True)

    kana_debug = os.path.join(DEBUG_DIR, "R1188_patched_kana_rows.png")
    save_debug_image(linear, kana_debug, y_range=(0, 144))
    print(f"\n  Debug    : {kana_debug}")

    bottom_debug = os.path.join(DEBUG_DIR, "R1188_patched_bottom.png")
    save_debug_image(linear, bottom_debug, y_range=(1005, 1024))
    print(f"  Debug    : {bottom_debug}")

    full_debug = os.path.join(DEBUG_DIR, "R1188_patched_full.png")
    save_debug_image(linear, full_debug, zoom=1)
    print(f"  Debug    : {full_debug}")

    # ---- Re-swizzle ----
    print("\n  Re-swizzling to PSMCT32 upload format ...")
    reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # ---- Round-trip verification ----
    re_lin = deswizzle_psmt4(reswizzled, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    mismatches = sum(1 for a, b in zip(linear, re_lin) if a != b)
    if mismatches == 0:
        print("  Round-trip verification: PASS")
    else:
        print(f"  Round-trip verification: FAIL ({mismatches} mismatches)")

    # ---- Write output ----
    # Use the original raw file layout (16-byte container + GIF header)
    if os.path.exists(RAW_PATH):
        raw_data = open(RAW_PATH, "rb").read()
        raw_header = raw_data[:HEADER_SIZE + 0x10]
    else:
        raw_header = header

    out = bytearray(raw_header) + reswizzled
    remainder = len(out) % SECTOR
    if remainder:
        out += b"\x00" * (SECTOR - remainder)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(out)

    print(f"  Output   : {OUT_PATH}  ({len(out)} bytes, sector-aligned)")

    # ---- Summary ----
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"    Kana cells overwritten:     {len(ALL_KANA_CELLS)}")
    print(f"    Bottom-row labels:          {len(BOTTOM_LABELS_DEDUP)}")
    print(f"    PCSX2 replacement PNGs:     {pcsx2_count}")
    print(f"    Total pixel edits:          {edits1 + edits2}")
    print(f"    Round-trip:                 {'PASS' if mismatches == 0 else 'FAIL'}")
    print(f"{'=' * 60}")
    print("\nDone!")


if __name__ == "__main__":
    main()
