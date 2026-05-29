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
    """Find a narrow font suitable for 12x12 cells."""
    candidates = [
        ("C:/Windows/Fonts/consola.ttf", 9),
        ("C:/Windows/Fonts/arial.ttf", 9),
        ("C:/Windows/Fonts/cour.ttf", 9),
    ]
    for path, size in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def split_label(english: str, strategy: str) -> tuple:
    """Split an English label into (tile1_text, tile2_text).

    For 'abbrev' labels (<= 4 chars), the whole word goes on tile 1.
    For 'tile_pair' labels, the word is split roughly in half.
    """
    if strategy == "skip":
        return ("", "")
    if not english:
        return ("", "")

    # Short words: put everything on tile 1
    if strategy == "abbrev" or len(english) <= 3:
        return (english, "")

    # Split at midpoint
    mid = len(english) // 2

    # Try to find a good split point near the midpoint
    best = mid
    for offset in range(0, min(3, mid)):
        for candidate in [mid + offset, mid - offset]:
            if 0 < candidate < len(english):
                best = candidate
                break

    return (english[:best], english[best:])


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
