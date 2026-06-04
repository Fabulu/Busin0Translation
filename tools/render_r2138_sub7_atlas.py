#!/usr/bin/env python3
"""
Render the COMPLETE R2138 sub7 font atlas at high resolution with annotations.

Outputs:
  dumps/r2138_sub7_full_annotated_4x.png  — with grid + patch region markers
  dumps/r2138_sub7_full_clean_4x.png      — clean 4x zoom, no annotations
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image, ImageDraw, ImageFont

# ── Constants (from patch_r2138_sub7.py) ──
INPUT_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
PIXEL_OFFSET = 0x0755D0
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128
ZOOM = 4

# ── Already-patched regions from patch_r2138_sub7.py ──
STAT_LABELS = [
    (192, 14,  64, 16, "HP"),
    (192, 78,  64, 16, "Str"),
    (192, 98,  64, 16, "Int"),
    (192, 118, 64, 16, "Pie"),
    (192, 138, 64, 16, "Vit"),
    (192, 158, 64, 16, "Agi"),
    (192, 178, 64, 16, "Lck"),
    (192, 198, 64, 16, "Atk"),
    (192, 218, 64, 16, "Eva"),
    (192, 238, 64, 18, "Def"),
]

TAB_LABELS = [
    (0,   0,  96, 20, "Basic Info"),
    (0,  20,  96, 20, "Detail Status"),
    (0,  40,  96, 20, "Item"),
    (0,  58,  96, 20, "Mage Magic"),
    (0,  78,  96, 20, "Priest Magic"),
]

CLEAR_ONLY = [
    (0, 98, 96, 14),
    (96, 98, 70, 14),
]

INPUT_MODE_LABELS = [
    (96,   0, 14, 20, "Ka"),
    (96,  20, 14, 20, "ka"),
    (96,  40, 20, 20, "A1"),
    (96,  58, 20, 20, "!@"),
]

CHARGEN_FIELD_LABELS = [
    (110,  0, 56, 20, "Gender"),
    (110, 20, 56, 20, "Race"),
    (110, 40, 56, 20, "Align"),
    (110, 60, 56, 20, "Class"),
    (86,  78, 36, 22, "OK"),
]

LARGE_LABELS = [
    (108, 78, 44, 22, "HP"),
]


def main():
    print("=== R2138 Sub7 Full Atlas Renderer ===\n")

    # Read and deswizzle
    print(f"Reading {INPUT_PATH}...")
    with open(INPUT_PATH, "rb") as f:
        r2138 = f.read()
    pixel_data = r2138[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
    assert len(pixel_data) == PIXEL_SIZE, f"Pixel data size: {len(pixel_data)}"

    print("Deswizzling...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                             bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

    # ── Build 1x grayscale image (INVERTED: dark bg, bright text) ──
    img_1x = Image.new("L", (TEX_W, TEX_H))
    for i, p in enumerate(linear[:TEX_W * TEX_H]):
        # Palette index 0 = text (opaque), 15 = transparent (background)
        # Inverted: 0 -> bright (255), 15 -> dark (0)
        img_1x.putpixel((i % TEX_W, i // TEX_W), (15 - p) * 17)

    # ── Clean 4x version ──
    out_w, out_h = TEX_W * ZOOM, TEX_H * ZOOM
    img_clean = img_1x.resize((out_w, out_h), Image.NEAREST)
    clean_path = os.path.join(BASE, "dumps", "r2138_sub7_full_clean_4x.png")
    os.makedirs(os.path.dirname(clean_path), exist_ok=True)
    img_clean.save(clean_path)
    print(f"Saved clean: {clean_path}")

    # ── Annotated 4x version ──
    # Convert to RGB for colored annotations
    img_annot = img_clean.convert("RGB")
    draw = ImageDraw.Draw(img_annot)

    # Minor grid every 16 pixels (cell boundaries) — dark cyan
    MINOR_COLOR = (0, 80, 80)
    for gx in range(0, TEX_W + 1, 16):
        x = gx * ZOOM
        if x < out_w:
            draw.line([(x, 0), (x, out_h - 1)], fill=MINOR_COLOR, width=1)
    for gy in range(0, TEX_H + 1, 16):
        y = gy * ZOOM
        if y < out_h:
            draw.line([(0, y), (out_w - 1, y)], fill=MINOR_COLOR, width=1)

    # Major grid every 64 pixels — brighter cyan
    MAJOR_COLOR = (0, 180, 180)
    for gx in range(0, TEX_W + 1, 64):
        x = gx * ZOOM
        if x < out_w:
            draw.line([(x, 0), (x, out_h - 1)], fill=MAJOR_COLOR, width=2)
    for gy in range(0, TEX_H + 1, 64):
        y = gy * ZOOM
        if y < out_h:
            draw.line([(0, y), (out_w - 1, y)], fill=MAJOR_COLOR, width=2)

    # ── Mark patched regions ──
    # Color coding:
    #   Green  = stat labels
    #   Blue   = tab labels
    #   Yellow = input mode labels
    #   Magenta = chargen field labels
    #   Orange = large labels
    #   Red    = clear-only zones

    def draw_patch_rect(x, y, w, h, color, label=""):
        rx0 = x * ZOOM
        ry0 = y * ZOOM
        rx1 = (x + w) * ZOOM - 1
        ry1 = (y + h) * ZOOM - 1
        # Draw rectangle outline (2px wide)
        draw.rectangle([rx0, ry0, rx1, ry1], outline=color, width=2)
        if label:
            # Small label in top-left corner
            draw.text((rx0 + 3, ry0 + 1), label, fill=color)

    # Try to load a small font for annotations
    try:
        annot_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 11)
    except Exception:
        annot_font = ImageFont.load_default()

    # Override draw.text to use our font
    orig_text = draw.text
    def draw_text_with_font(pos, text, fill=None, **kw):
        orig_text(pos, text, fill=fill, font=annot_font, **kw)
    draw.text = draw_text_with_font

    print("Drawing patch region markers...")
    for x, y, w, h, text in STAT_LABELS:
        draw_patch_rect(x, y, w, h, (0, 255, 0), text)

    for x, y, w, h, text in TAB_LABELS:
        draw_patch_rect(x, y, w, h, (80, 140, 255), text)

    for x, y, w, h, text in INPUT_MODE_LABELS:
        draw_patch_rect(x, y, w, h, (255, 255, 0), text)

    for x, y, w, h, text in CHARGEN_FIELD_LABELS:
        draw_patch_rect(x, y, w, h, (255, 0, 255), text)

    for x, y, w, h, text in LARGE_LABELS:
        draw_patch_rect(x, y, w, h, (255, 160, 0), text)

    for x, y, w, h in CLEAR_ONLY:
        draw_patch_rect(x, y, w, h, (255, 0, 0), "CLEAR")

    # ── Legend ──
    legend_y = out_h - 90
    legend_x = 10
    legend_bg = (20, 20, 20)
    draw.rectangle([legend_x - 5, legend_y - 5, legend_x + 320, out_h - 5],
                   fill=legend_bg, outline=(100, 100, 100))
    items = [
        ((0, 255, 0), "Green = Stat labels"),
        ((80, 140, 255), "Blue = Tab labels"),
        ((255, 255, 0), "Yellow = Input mode"),
        ((255, 0, 255), "Magenta = Chargen fields"),
        ((255, 160, 0), "Orange = Large labels"),
        ((255, 0, 0), "Red = Clear-only zones"),
    ]
    for i, (color, desc) in enumerate(items):
        ly = legend_y + i * 13
        draw.rectangle([legend_x, ly, legend_x + 10, ly + 10], fill=color)
        orig_text((legend_x + 14, ly - 1), desc, fill=(220, 220, 220), font=annot_font)

    # ── Coordinate labels on edges ──
    for gx in range(0, TEX_W + 1, 64):
        x = gx * ZOOM
        orig_text((x + 2, 2), str(gx), fill=(0, 220, 220), font=annot_font)
    for gy in range(64, TEX_H + 1, 64):
        y = gy * ZOOM
        orig_text((2, y + 2), str(gy), fill=(0, 220, 220), font=annot_font)

    annot_path = os.path.join(BASE, "dumps", "r2138_sub7_full_annotated_4x.png")
    img_annot.save(annot_path)
    print(f"Saved annotated: {annot_path}")

    print("\nDONE!")


if __name__ == "__main__":
    main()
