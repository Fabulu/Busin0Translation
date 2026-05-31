#!/usr/bin/env python3
"""
R1188 atlas pixel overwriter -- direct Japanese-to-English label patching.

APPROACH: The name-entry-screen atlas (R1188, 1024x1024 PSMT4) stores
individual character glyphs.  The game composes labels like "カナ" by drawing
two characters side by side.  This script:

  1.  Deswizzles the raw texture.
  2.  Identifies known character cells in the kana/ASCII rows (y < 144).
  3.  Overwrites every kana cell with a roman/English replacement glyph so that
      BOTH the keyboard grid AND composed labels show English.
  4.  Writes English label sprites into empty atlas space (y >= 1009) as a
      secondary strategy for future EXE-redirect patching.
  5.  Re-swizzles and writes the patched file.

Character cell positions were mapped by cluster analysis of the deswizzled
atlas and cross-referenced with visual inspection of the glyph rows.

Round-trip verified: deswizzle -> edit -> reswizzle = exact byte match on
unmodified pixels.
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
# Paths
# ---------------------------------------------------------------------------
BIN_PATH  = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
RAW_PATH  = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
OUT_PATH  = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
DEBUG_DIR = os.path.join(BASE, "build", "textures_to_edit")

SECTOR      = 2048
HEADER_SIZE = 0xC00   # 3072 bytes
TEX_W       = 1024
TEX_H       = 1024
DBW_CT32    = 512
BW_PSMT4    = 1024

# ---------------------------------------------------------------------------
# Character cell map  (row_y, x_start, x_end, japanese, english_replacement)
#
# Each entry describes one glyph cell in the deswizzled atlas.
# The English replacement is rendered into the same bounding box.
# ---------------------------------------------------------------------------

# Row 2  (y=48-71) -- hiragana あ-そ  and special symbols
# Symbols (cells 0-5) are left as-is; they are useful in English too.
HIRAGANA_ROW2 = [
    # (y0, y1, x0, x1, jp_char, en_replacement)
    (48, 72, 161, 180, "a",  "a"),
    (48, 72, 187, 205, "i",  "i"),
    (48, 72, 198, 214, "u",  "u"),
    (48, 72, 212, 230, "e",  "e"),
    (48, 72, 233, 256, "o",  "o"),
    (48, 72, 256, 280, "ka", "ka"),
    (48, 72, 281, 306, "ki", "ki"),
    (48, 72, 308, 330, "ku", "ku"),
    (48, 72, 333, 355, "ke", "ke"),
    (48, 72, 355, 378, "ko", "ko"),
    (48, 72, 380, 400, "sa", "sa"),
    (48, 72, 403, 424, "si", "si"),
    (48, 72, 428, 449, "su", "su"),
    (48, 72, 449, 473, "se", "se"),
    (48, 72, 473, 496, "so", "so"),
]

# Row 3  (y=72-95) -- hiragana や-ぞ  (ya-row, ra-row, wa/n, dakuten)
HIRAGANA_ROW3 = [
    (72, 96,   0,  17, "ya", "ya"),
    (72, 96,  18,  41, "yu", "yu"),
    (72, 96,  42,  64, "yo", "yo"),
    (72, 96,  68,  90, "ra", "ra"),
    (72, 96,  94, 113, "ri", "ri"),
    (72, 96, 114, 136, "ru", "ru"),
    (72, 96, 137, 162, "re", "re"),
    (72, 96, 163, 184, "ro", "ro"),
    (72, 96, 185, 210, "wo", "wo"),
    (72, 96, 211, 233, "n",  "n"),
    (72, 96, 233, 257, "pa", "pa"),
    (72, 96, 257, 282, "gi", "gi"),
    (72, 96, 283, 306, "gu", "gu"),
    (72, 96, 307, 329, "ge", "ge"),
    (72, 96, 329, 354, "go", "go"),
    (72, 96, 354, 378, "za", "za"),
    (72, 96, 379, 404, "ji", "ji"),
    (72, 96, 405, 425, "zu", "zu"),
    (72, 96, 426, 449, "ze", "ze"),
    (72, 96, 449, 473, "zo", "zo"),
]

# Row 4  (y=96-119) -- katakana ア-チ  (left half)
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
    (96, 120, 209, 234, "Ka", "Ka"),   # <-- used in カナ tab label
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

# Row 4 right half (y=96-119, x=512+) -- katakana ツ-モ  (24px grid)
KATAKANA_ROW4_RIGHT = [
    (96, 120, 512, 535, "Tu", "Tu"),
    (96, 120, 536, 559, "Te", "Te"),
    (96, 120, 560, 583, "To", "To"),
    (96, 120, 584, 607, "Na", "Na"),   # <-- used in カナ tab label
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

# Row 5  (y=120-143) -- katakana ラ-ヅ  (left half)
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

# Row 5 right half (y=120-143, x=512+) -- remaining katakana (24px grid)
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

# Bottom-area English labels (backup for EXE-redirect approach)
BOTTOM_LABELS = [
    (1009, 1020,   0,  47, "Kana",  "Kana"),
    (1009, 1020,  50,  97, "Hira",  "Hira"),
    (1009, 1020, 100, 147, "ABC",   "ABC"),
    (1009, 1020, 150, 197, "Sym",   "Sym"),
    (1009, 1020, 200, 239, "OK",    "OK"),
    (1009, 1020, 242, 289, "M.Name","M.Name"),
    (1009, 1020, 292, 339, "F.Name","F.Name"),
    (1009, 1020, 342, 389, "Delete","Delete"),
    (1009, 1020, 392, 439, "Clear", "Clear"),
    (1009, 1020, 450, 569, "New Character", "New Character"),
    # Stat labels
    (1009, 1020, 572, 635, "Strength", "Strength"),
    (1009, 1020, 638, 701, "IQ",       "IQ"),
    (1009, 1020, 704, 767, "Piety",    "Piety"),
    (1009, 1020, 770, 833, "Vitality", "Vitality"),
    (1009, 1020, 836, 899, "Agility",  "Agility"),
    (1009, 1020, 902, 965, "Luck",     "Luck"),
]

# ---------------------------------------------------------------------------
# Sidebar kanji cells  (y0, y1, x0, x1, jp_char, en_replacement)
#
# These are the individual kanji used in chargen sidebar labels:
#   性別 (gender), 種族 (race), 属性 (alignment), 職業 (class), 性格 (personality)
#
# Positions verified by visual inspection of R1188_CORRECT_dbw512.png.
# Grid: rows 6-41 at 24px height, cols at x = 0,17,41,65,89,113,...
# NOTE: 別 and 業 are NOT in the left-half kanji grid (x=0-495).
#       They exist in the right half or alternate atlas region.
#       Only the 6 kanji found in the left-half grid are patched here.
# NOTE: 性 is shared by gender (性別), alignment (属性), and personality (性格).
#       A single abbreviation must serve all three contexts.
# ---------------------------------------------------------------------------
SIDEBAR_KANJI_CELLS = [
    # (y0, y1, x0, x1, jp_char, en_replacement)
    # 性 = row 19, col 20 -> used in 性別/属性/性格 -> "sx" (sex/nature)
    (456, 480, 473, 495, "sei",   "sx"),
    # 種 = row 18, col 9 -> used in 種族 (race) -> "ra"
    (432, 456, 209, 231, "shu",   "ra"),
    # 族 = row 18, col 10 -> used in 種族 (race) -> "ce"
    (432, 456, 233, 255, "zoku",  "ce"),
    # 属 = row 37, col 5 -> used in 属性 (alignment) -> "al"
    (888, 912, 113, 135, "zoku2", "al"),
    # 職 = row 15, col 9 -> used in 職業 (class) -> "cl"
    (360, 384, 209, 231, "shoku", "cl"),
    # 格 = row 22, col 3 -> used in 性格 (personality) -> "pe"
    (528, 552, 65,  87,  "kaku",  "pe"),
]

# Combine all cell tables
ALL_KANA_CELLS = (
    HIRAGANA_ROW2 + HIRAGANA_ROW3 +
    KATAKANA_ROW4_LEFT + KATAKANA_ROW4_RIGHT +
    KATAKANA_ROW5_LEFT + KATAKANA_ROW5_RIGHT
)


# ---------------------------------------------------------------------------
# Font / rendering helpers
# ---------------------------------------------------------------------------

def get_font(size=10):
    """Return a TrueType font suitable for rendering into atlas cells."""
    for path in [
        "C:/Windows/Fonts/consola.ttf",   # Consolas
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
    """Render *text* centered in a (width x height) box.

    Returns a 2-D numpy array of palette indices (0 = transparent,
    *max_index* = fully opaque).
    """
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Shrink font if too wide
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
    # Quantise 0-255 grayscale -> 0-max_index
    out = np.round(arr * max_index / 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------
# Core patching
# ---------------------------------------------------------------------------

def patch_cells(linear, cells, font_size=11):
    """Clear each cell and render its English replacement.

    *linear* is a 1-D array of palette indices (0-15) for 1024x1024 pixels.
    Modified in place.  Returns the number of edited pixels.
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


def patch_bottom_labels(linear, font_size=9):
    """Render English label sprites into the empty bottom rows."""
    edits = 0
    for y0, y1, x0, x1, _jp, en in BOTTOM_LABELS:
        w = x1 - x0 + 1
        h = y1 - y0
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
# Debug visualisation
# ---------------------------------------------------------------------------

def save_debug_image(linear, path, y_range=None):
    """Save a grayscale visualisation of the atlas (or a slice)."""
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
    # 2x zoom for visibility
    img = img.resize((TEX_W * 2, h * 2), Image.NEAREST)
    img.save(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== R1188 Atlas Pixel Overwriter ===")
    print()

    # -- Load source --
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
    pixel_data = data[header_size : header_size + TEX_W * TEX_H // 2]

    print(f"  Source  : {src_path}  ({len(data)} bytes)")
    print(f"  Header  : {header_size} bytes")
    print(f"  Pixels  : {len(pixel_data)} bytes")

    # -- Deswizzle --
    print("  Deswizzling 1024x1024 PSMT4 (dbw_ct32=512) ...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    linear = bytearray(linear)   # ensure mutable

    # -- Phase 1: overwrite kana cells --
    print(f"  Phase 1: overwriting {len(ALL_KANA_CELLS)} kana cells ...")
    edits1 = patch_cells(linear, ALL_KANA_CELLS, font_size=11)
    print(f"           {edits1} pixel edits")

    # -- Phase 2: bottom-row English labels --
    print(f"  Phase 2: rendering {len(BOTTOM_LABELS)} bottom-row labels ...")
    edits2 = patch_bottom_labels(linear, font_size=9)
    print(f"           {edits2} pixel edits")

    # -- Phase 3: sidebar kanji cells --
    print(f"  Phase 3: overwriting {len(SIDEBAR_KANJI_CELLS)} sidebar kanji ...")
    edits3 = patch_cells(linear, SIDEBAR_KANJI_CELLS, font_size=14)
    print(f"           {edits3} pixel edits")

    # -- Debug images --
    os.makedirs(DEBUG_DIR, exist_ok=True)

    kana_debug = os.path.join(DEBUG_DIR, "R1188_patched_kana_rows.png")
    save_debug_image(linear, kana_debug, y_range=(0, 144))
    print(f"  Debug   : {kana_debug}")

    bottom_debug = os.path.join(DEBUG_DIR, "R1188_patched_bottom.png")
    save_debug_image(linear, bottom_debug, y_range=(1005, 1024))
    print(f"  Debug   : {bottom_debug}")

    sidebar_debug = os.path.join(DEBUG_DIR, "R1188_patched_sidebar_kanji.png")
    save_debug_image(linear, sidebar_debug, y_range=(350, 920))
    print(f"  Debug   : {sidebar_debug}")

    full_debug = os.path.join(DEBUG_DIR, "R1188_patched_full.png")
    save_debug_image(linear, full_debug)
    print(f"  Debug   : {full_debug}")

    # -- Re-swizzle --
    print("  Re-swizzling ...")
    reswizzled = swizzle_psmt4(linear, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # -- Verify round-trip on un-patched pixels --
    re_lin = deswizzle_psmt4(reswizzled, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    mismatches = sum(1 for a, b in zip(linear, re_lin) if a != b)
    if mismatches == 0:
        print("  Round-trip verification: PASS")
    else:
        print(f"  Round-trip verification: FAIL ({mismatches} mismatches)")

    # -- Write output --
    # Use original raw file layout (16-byte container + header)
    if os.path.exists(RAW_PATH):
        raw_data = open(RAW_PATH, "rb").read()
        raw_header = raw_data[: HEADER_SIZE + 0x10]
    else:
        raw_header = header

    out = bytearray(raw_header) + reswizzled
    remainder = len(out) % SECTOR
    if remainder:
        out += b"\x00" * (SECTOR - remainder)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(out)

    print(f"  Output  : {OUT_PATH}  ({len(out)} bytes, sector-aligned)")
    print()
    print("Done!")


if __name__ == "__main__":
    main()
