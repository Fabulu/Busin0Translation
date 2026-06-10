#!/usr/bin/env python3
"""
Render English menu labels into 12x12 font atlas tiles.

Reads data/menu_labels.csv and produces a dict of {glyph_id: pixel_data}
where pixel_data is a 144-byte list (12x12, one byte per pixel).

Grayscale convention (matching generate_font_atlas.py image):
  255 = white (character foreground)
  0   = black (transparent background)

The 4bpp conversion in generate_font_atlas.py handles the inversion to
game palette (0=opaque text, 15=transparent).
"""
import csv
import os
import sys

from PIL import Image, ImageFont, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL_W, CELL_H = 12, 12
CSV_PATH = os.path.join(BASE, "data", "menu_labels.csv")


def find_font():
    """Find a narrow proportional font for 12x12 cells.

    Calibri 7pt fits 3 chars per 12px tile (vs Consolas 9pt = 2 chars).
    This allows 6-char labels across tile pairs (e.g. tavern, church).
    """
    candidates = [
        ("C:/Windows/Fonts/calibri.ttf", 7),
        ("C:/Windows/Fonts/tahoma.ttf", 7),
        ("C:/Windows/Fonts/segoeui.ttf", 7),
        ("C:/Windows/Fonts/arial.ttf", 7),
    ]
    for path, size in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def split_label(english: str, strategy: str) -> tuple:
    """Split an English label into (tile1_text, tile2_text).

    For 'abbrev' labels (<= 4 chars), the whole word goes on tile 1.
    For 'tile_pair' labels, split at 3 chars (max per tile with Calibri 7pt).
    """
    if strategy == "skip":
        return ("", "")
    if not english:
        return ("", "")

    # Short words: put everything on tile 1
    if strategy == "abbrev" or len(english) <= 3:
        return (english, "")

    # Split at 3 chars — each tile fits 3 chars with Calibri 7pt
    return (english[:3], english[3:])


def render_tile(text: str, font) -> list:
    """Render text into a 12x12 grayscale pixel array.

    Returns list of 144 ints (0-255), where 255=white text, 0=black bg.
    This matches the convention used by generate_font_atlas.py.
    """
    pixels = [0] * (CELL_W * CELL_H)  # start black (transparent in game)
    if not text:
        return pixels

    img = Image.new("L", (CELL_W, CELL_H), 0)  # black background
    draw = ImageDraw.Draw(img)

    bbox = font.getbbox(text)
    if not bbox:
        return pixels

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Left-align, vertically center
    ox = -bbox[0]  # flush left
    oy = max(0, (CELL_H - th) // 2) - bbox[1]
    draw.text((ox, oy), text, fill=255, font=font)

    return list(img.getdata())


def render_symbol_tile(symbol: str) -> list:
    """Render a special symbol (♂ or ♀) as a 12x12 pixel-art tile.

    Uses PIL drawing primitives for clean rendering at small size.
    Returns list of 144 ints (0-255), where 255=white text, 0=black bg.
    """
    img = Image.new("L", (CELL_W, CELL_H), 0)
    d = ImageDraw.Draw(img)

    if symbol == "\u2642":  # Mars / Male (♂)
        # Circle at lower-left, arrow pointing upper-right
        d.ellipse([1, 4, 7, 10], outline=255, width=1)
        d.line([(6, 5), (10, 1)], fill=255, width=1)
        d.line([(7, 1), (10, 1)], fill=255, width=1)
        d.line([(10, 1), (10, 4)], fill=255, width=1)
    elif symbol == "\u2640":  # Venus / Female (♀)
        # Circle at top, cross below
        d.ellipse([2, 1, 9, 7], outline=255, width=1)
        d.line([(5, 7), (5, 11)], fill=255, width=1)
        d.line([(6, 7), (6, 11)], fill=255, width=1)
        d.line([(3, 9), (8, 9)], fill=255, width=1)
    else:
        # Fallback: try font rendering
        font = find_font()
        d.text((1, 1), symbol, fill=255, font=font)

    return list(img.getdata())


def load_menu_tiles() -> dict:
    """Load CSV and render all menu tiles.

    Returns {glyph_id: [144 grayscale pixel values]} for all non-skip entries.
    Pixel values are 0-255 (0=black/bg, 255=white/text).
    """
    font = find_font()
    tiles = {}

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            strategy = row["strategy"].strip()
            if strategy == "skip":
                continue
            glyph_id_1 = int(row["glyph_id_1"])
            glyph_id_2 = int(row["glyph_id_2"])
            english = row["english"].strip()

            if strategy == "symbol":
                # Custom symbol rendering (e.g., ♂, ♀)
                tiles[glyph_id_1] = render_symbol_tile(english)
                # glyph_id_2 = 0 means no second tile needed
                if glyph_id_2 != 0:
                    tiles[glyph_id_2] = render_tile("", font)
                continue

            tile1_text, tile2_text = split_label(english, strategy)
            tiles[glyph_id_1] = render_tile(tile1_text, font)
            tiles[glyph_id_2] = render_tile(tile2_text, font)

    return tiles


if __name__ == "__main__":
    tiles = load_menu_tiles()
    print(f"Rendered {len(tiles)} menu tiles from {CSV_PATH}")
    # Debug: show a few
    for gid in sorted(tiles.keys())[:10]:
        non_bg = sum(1 for p in tiles[gid] if p > 0)
        print(f"  Glyph {gid}: {non_bg} foreground pixels")
