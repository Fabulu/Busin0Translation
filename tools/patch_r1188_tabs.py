#!/usr/bin/env python3
"""
Patch R1188 name entry screen tab labels for English translation.

Creates PCSX2 texture replacement PNGs for the tab label sprites.
PCSX2 loads these from its texture replacement directory, overriding
the in-game Japanese labels with English text.

Also copies the original R1188 to the build output (the raw texture
data is left unmodified since PCSX2 replacement handles the visuals).

Tab labels replaced:
  48x20: カナ->Kana, かな->Hira, 英数->ABC, 記号->Sym,
         性別->Gender, 職業->Class, 種族->Race, 属性->Align
  40x24: 決定->OK
"""
import sys
import os
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
OUT_PATH = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
REPLACE_DIR = os.path.join(BASE, "build", "pcsx2_texture_replacements")
SECTOR = 2048

# PCSX2 texture dump filenames encode: hash1-hash2-rWxH-GSPAGE.png
# hash1 = content hash, hash2 = CLUT hash
# For replacement, PCSX2 matches on the FULL filename.

# Tab labels (48x20) - all share CLUT hash 3cb39bf7659ef15f, GS page 00002214
TAB_LABELS_48x20 = {
    '16625baf9feaeafb': 'Gender',   # 性別
    '19a39fbc8a08d7ec': 'Sym',      # 記号
    '1f839869fab251d':  'Kana',     # カナ
    '6f1fb24fad5cd1a':  'ABC',      # 英数
    '88ff8b577084a2a8': 'Class',    # 職業
    '9677cb23da53ff88': 'Hira',     # かな
    '9bec87b4031a7172': 'Race',     # 種族
    'c89b469f7a152a6':  'Align',    # 属性
}

# Confirm button (40x24)
BUTTONS_40x24 = {
    'd09a04bdfaf715bc': 'OK',       # 決定
}

# Title bar text (120x24) - same GS page, different CLUT
TITLE_120x24 = {
    'a2d3fce36c8c719d': 'New Character',  # 新規登録
}

# Stat labels (64x16) - same CLUT/page
STAT_LABELS_64x16 = {
    '280ea82c1c476a98': 'Luck',       # 幸運度
    '4841ef9a2dc4981':  'Agility',    # 敏捷度
    '5d0c6327e20384e7': 'Vitality',   # 生命力
    'aa43f966ad69195e': 'Piety',      # 信仰心
    'bb20512b10c3128b': 'IQ',         # 知恵
    'd455234204274c43': 'HP/MAX',     # HP/MAX (already English)
    'f2013a64642252e3': 'Strength',   # 力
}

CLUT_HASH = '3cb39bf7659ef15f'
CLUT_HASH_TITLE = 'e786e0650b284c64'  # Different CLUT for title text
GS_PAGE = '00002214'


def render_label_48x20(text, width=48, height=20):
    """Render English label text as white-on-transparent RGBA, matching
    the game's antialiased style (16 alpha levels)."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Try to find a suitable small font
    font = None
    font_size = 14
    try:
        # Try common system fonts
        for font_name in ['arial.ttf', 'ArialMT.ttf', 'DejaVuSans.ttf',
                          'segoeui.ttf', 'tahoma.ttf', 'verdana.ttf',
                          'C:/Windows/Fonts/arial.ttf',
                          'C:/Windows/Fonts/segoeui.ttf']:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except (OSError, IOError):
                continue
    except Exception:
        pass

    if font is None:
        font = ImageFont.load_default()

    # Get text bounding box and center it
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # If text is too wide, try smaller font
    if tw > width - 4 and font_size > 8:
        for sz in range(font_size - 1, 7, -1):
            try:
                font = ImageFont.truetype(font.path, sz)
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                if tw <= width - 4:
                    break
            except Exception:
                break

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]

    # Draw white text
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Quantize alpha to 16 levels (matching PS2 PSMT4 palette)
    # Alpha values: 0, 11, 19, 28, 36, 44, 52, 60, 69, 77, 85, 93, 102, 110, 118, 128
    alpha_levels = [0, 11, 19, 28, 36, 44, 52, 60, 69, 77, 85, 93, 102, 110, 118, 128]

    pixels = img.load()
    for py in range(height):
        for px in range(width):
            r, g, b, a = pixels[px, py]
            if a == 0:
                pixels[px, py] = (255, 255, 255, 0)
            else:
                # Map alpha (0-255) to closest PS2 alpha level
                ps2_a = round(a * 128 / 255)
                closest = min(alpha_levels, key=lambda v: abs(v - ps2_a))
                pixels[px, py] = (255, 255, 255, closest)

    return img


def render_label_40x24(text, width=40, height=24):
    """Render button label as white-on-transparent RGBA."""
    return render_label_48x20(text, width, height)


def create_pcsx2_replacements():
    """Create PCSX2 texture replacement PNG files."""
    os.makedirs(REPLACE_DIR, exist_ok=True)
    count = 0

    # 48x20 tab labels
    for hash1, english in TAB_LABELS_48x20.items():
        filename = f"{hash1}-{CLUT_HASH}-r48x20-{GS_PAGE}.png"
        img = render_label_48x20(english)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # 40x24 buttons
    for hash1, english in BUTTONS_40x24.items():
        filename = f"{hash1}-{CLUT_HASH}-r40x24-{GS_PAGE}.png"
        img = render_label_40x24(english)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # 120x24 title bar
    for hash1, english in TITLE_120x24.items():
        filename = f"{hash1}-{CLUT_HASH_TITLE}-r120x24-{GS_PAGE}.png"
        img = render_label_48x20(english, width=120, height=24)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    # 64x16 stat labels
    for hash1, english in STAT_LABELS_64x16.items():
        if english == 'HP/MAX':
            continue  # Already English
        filename = f"{hash1}-{CLUT_HASH}-r64x16-{GS_PAGE}.png"
        img = render_label_48x20(english, width=64, height=16)
        img.save(os.path.join(REPLACE_DIR, filename))
        count += 1

    print(f"  Created {count} PCSX2 replacement textures in {REPLACE_DIR}")
    return count


def copy_r1188_to_build():
    """Copy original R1188 to build output (sector-padded)."""
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    if not os.path.exists(RAW_PATH):
        print(f"  WARNING: {RAW_PATH} not found, skipping R1188 copy")
        return False

    data = open(RAW_PATH, 'rb').read()

    # Pad to sector boundary
    remainder = len(data) % SECTOR
    if remainder:
        data += b'\x00' * (SECTOR - remainder)

    with open(OUT_PATH, 'wb') as f:
        f.write(data)

    print(f"  R1188 copied to {OUT_PATH} ({len(data)} bytes, sector-aligned)")
    return True


def main():
    print("=== R1188 Tab Label Patcher ===")

    # Create PCSX2 texture replacements
    create_pcsx2_replacements()

    # Copy original R1188 to build output
    copy_r1188_to_build()

    # Print instructions for PCSX2 setup
    print(f"\n  To use PCSX2 texture replacements:")
    print(f"    1. Copy files from {REPLACE_DIR}")
    print(f"       to PCSX2/textures/replacements/SLPM-65378/replacements/")
    print(f"    2. Enable 'Load Textures' in PCSX2 Graphics settings")
    print(f"    3. The English labels will appear in-game")

    print("\nDone!")


if __name__ == "__main__":
    main()
