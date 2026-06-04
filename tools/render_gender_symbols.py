#!/usr/bin/env python3
"""
Render Mars (♂) and Venus (♀) gender symbols as 16x16 PSMT4 pixel art
for the R2100 chargen/stat font atlas.

Palette convention (same as patch_r2100.py):
  index 0  = fully opaque text (brightest)
  index 1-3 = antialiased edges (decreasing opacity)
  index 15 = fully transparent background

Output:
  - build/textures_to_edit/mars_symbol_16x16.png   (preview)
  - build/textures_to_edit/venus_symbol_16x16.png   (preview)
  - Prints PSMT4 index arrays ready for patch_r2100.py

Cell positions in R2100:
  ♂ (Mars/男):  sub-block 2, row 0, col 6  — glyph ID 518
  ♀ (Venus/女): sub-block 1, row 5, col 13 — glyph ID 349
"""

import os
import sys
import io
from PIL import Image, ImageDraw

# Force UTF-8 output on Windows to handle Unicode symbols
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "build", "textures_to_edit")
os.makedirs(OUT_DIR, exist_ok=True)

CELL = 16


def grayscale_to_psmt4(val):
    """Convert 0-255 grayscale to PSMT4 index.
    White (255) -> 0 (opaque), Black (0) -> 15 (transparent).
    Same formula as generate_font_atlas.py / patch_r2100.py.
    """
    return 15 - min(val * 15 // 255, 15)


def render_mars_symbol():
    """Draw ♂ (Mars): circle with diagonal arrow pointing upper-right.

    Hand-tuned pixel art for best appearance on PS2 at 16x16.
    Uses antialiasing indices for diagonal arrow shaft.
    """
    img = Image.new("L", (CELL, CELL), 0)
    draw = ImageDraw.Draw(img)

    # Circle: center at (5, 9), radius 4 for ~8px diameter
    cx, cy = 5, 9
    r = 4
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=255, width=1
    )

    # Arrow shaft: diagonal from circle edge upper-right toward corner
    # Use width=1 line for clean diagonal
    draw.line([(8, 6), (13, 1)], fill=255, width=1)

    # Arrowhead barbs at tip (13, 1)
    # Horizontal barb going left
    draw.line([(13, 1), (10, 1)], fill=255, width=1)
    # Vertical barb going down
    draw.line([(13, 1), (13, 4)], fill=255, width=1)

    # Add antialiasing on diagonal shaft (partial brightness pixels beside the line)
    aa_pixels = [
        # Slight AA along diagonal — below-left of each shaft pixel
        (8, 7, 80), (9, 6, 80),
        (10, 5, 80), (11, 4, 80), (12, 3, 80),
        # Above-right of shaft
        (9, 4, 80), (10, 3, 80), (11, 2, 80),
    ]
    for ax, ay, av in aa_pixels:
        # Only apply AA to pixels that are currently black (transparent)
        if img.getpixel((ax, ay)) == 0:
            img.putpixel((ax, ay), av)

    return img


def render_venus_symbol():
    """Draw ♀ (Venus): circle with vertical line and cross below.

    Hand-tuned pixel art for best appearance on PS2 at 16x16.
    """
    img = Image.new("L", (CELL, CELL), 0)
    draw = ImageDraw.Draw(img)

    # Circle: centered, in upper portion — ~8px diameter
    cx, cy = 7, 5
    r = 4
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=255, width=1
    )

    # Vertical stem: from bottom of circle downward
    draw.line([(cx, cy + r + 1), (cx, 14)], fill=255, width=1)

    # Cross bar: horizontal line across the stem
    cross_y = 12
    draw.line([(cx - 2, cross_y), (cx + 2, cross_y)], fill=255, width=1)

    return img


def image_to_psmt4_array(img):
    """Convert a grayscale PIL image to a list of PSMT4 indices (0-15)."""
    pixels = list(img.getdata())
    return [grayscale_to_psmt4(v) for v in pixels]


def print_pixel_grid(indices, w=CELL, h=CELL, name=""):
    """Print a visual grid of the PSMT4 indices for debugging."""
    print(f"\n{'='*60}")
    print(f"  {name} — PSMT4 index grid ({w}x{h})")
    print(f"  0=opaque text, 15=transparent background")
    print(f"{'='*60}")
    for y in range(h):
        row = indices[y * w:(y + 1) * w]
        # Show as hex for compactness
        line = " ".join(f"{v:X}" for v in row)
        print(f"  {line}")


def format_python_array(indices, name, w=CELL, h=CELL):
    """Format indices as a Python list for copy-paste into patch_r2100.py."""
    lines = [f"{name} = ["]
    for y in range(h):
        row = indices[y * w:(y + 1) * w]
        line = "    " + ", ".join(f"{v:2d}" for v in row) + ","
        lines.append(line)
    lines.append("]")
    return "\n".join(lines)


def main():
    print("=== Gender Symbol Pixel Art Renderer ===\n")

    # ── Render Mars (♂) ──
    mars_img = render_mars_symbol()
    mars_indices = image_to_psmt4_array(mars_img)

    mars_path = os.path.join(OUT_DIR, "mars_symbol_16x16.png")
    # Save a 4x scaled preview for visibility
    mars_preview = mars_img.resize((CELL * 4, CELL * 4), Image.NEAREST)
    mars_preview.save(mars_path)
    print(f"Saved Mars preview: {mars_path}")

    # Also save 1:1 version
    mars_1x_path = os.path.join(OUT_DIR, "mars_symbol_16x16_1x.png")
    mars_img.save(mars_1x_path)

    print_pixel_grid(mars_indices, name="Mars (♂)")

    # ── Render Venus (♀) ──
    venus_img = render_venus_symbol()
    venus_indices = image_to_psmt4_array(venus_img)

    venus_path = os.path.join(OUT_DIR, "venus_symbol_16x16.png")
    venus_preview = venus_img.resize((CELL * 4, CELL * 4), Image.NEAREST)
    venus_preview.save(venus_path)
    print(f"Saved Venus preview: {venus_path}")

    venus_1x_path = os.path.join(OUT_DIR, "venus_symbol_16x16_1x.png")
    venus_img.save(venus_1x_path)

    print_pixel_grid(venus_indices, name="Venus (♀)")

    # ── Print Python arrays for patch_r2100.py ──
    print("\n" + "=" * 60)
    print("  Python arrays for patch_r2100.py")
    print("=" * 60)
    print()
    print(format_python_array(mars_indices, "MARS_PIXELS"))
    print()
    print(format_python_array(venus_indices, "VENUS_PIXELS"))

    # ── Print patch dict entries ──
    print()
    print("# Patch dict entries for patch_r2100.py:")
    print("GENDER_PATCHES = {")
    print("    # ♂ (Mars/男): sub-block 2, row 0, col 6 — glyph ID 518")
    print("    (2, 0, 6): MARS_PIXELS,")
    print("    # ♀ (Venus/女): sub-block 1, row 5, col 13 — glyph ID 349")
    print("    (1, 5, 13): VENUS_PIXELS,")
    print("}")

    # ── Verify dimensions ──
    assert len(mars_indices) == CELL * CELL, f"Mars has {len(mars_indices)} pixels, expected {CELL*CELL}"
    assert len(venus_indices) == CELL * CELL, f"Venus has {len(venus_indices)} pixels, expected {CELL*CELL}"
    assert all(0 <= v <= 15 for v in mars_indices), "Mars has out-of-range values"
    assert all(0 <= v <= 15 for v in venus_indices), "Venus has out-of-range values"

    # Count non-transparent pixels
    mars_drawn = sum(1 for v in mars_indices if v < 15)
    venus_drawn = sum(1 for v in venus_indices if v < 15)
    print(f"\nMars: {mars_drawn} drawn pixels, {CELL*CELL - mars_drawn} transparent")
    print(f"Venus: {venus_drawn} drawn pixels, {CELL*CELL - venus_drawn} transparent")
    print("\nDONE!")


if __name__ == "__main__":
    main()
