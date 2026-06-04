#!/usr/bin/env python3
"""
Detailed analysis of the EXE embedded font (deswizzle with dbw=64).
Save high-quality zoomed PNG and analyze what characters are present.
"""
import os, sys, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4, make_rgba_image_4bit

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")
os.makedirs(TEX_DIR, exist_ok=True)

EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
exe_data = open(EXE_PATH, 'rb').read()

# ---- Main discovery: EXE font at 0x3D6C10, PSMT4 128x128, dbw_ct32=64 ----
EXE_FONT_OFF = 0x3D6C10
font_raw = exe_data[EXE_FONT_OFF:EXE_FONT_OFF + 8192]

print("=== EXE Embedded Font (PSMT4 128x128, dbw=64) ===\n")

pixels = deswizzle_psmt4(font_raw, 128, 128, bw_psmt4=128, dbw_ct32=64)

# Grayscale palette
palette = bytearray(64)
for i in range(16):
    v = i * 17
    palette[i*4] = v; palette[i*4+1] = v; palette[i*4+2] = v; palette[i*4+3] = 128

img = make_rgba_image_4bit(pixels, palette, 128, 128)

# Save original size
out1 = os.path.join(TEX_DIR, "EXE_embedded_font.png")
img.save(out1)
print(f"Saved: {out1}")

# Save 4x zoomed
img_zoom = img.resize((512, 512), Image.NEAREST)
out2 = os.path.join(TEX_DIR, "EXE_embedded_font_4x.png")
img_zoom.save(out2)
print(f"Saved 4x zoom: {out2}")

# Save 8x zoomed
img_zoom8 = img.resize((1024, 1024), Image.NEAREST)
out3 = os.path.join(TEX_DIR, "EXE_embedded_font_8x.png")
img_zoom8.save(out3)
print(f"Saved 8x zoom: {out3}")

# Analyze: find non-empty rows/columns to understand glyph layout
print("\nPixel analysis:")
print(f"  Total pixels: {128*128}")
nonzero = sum(1 for p in pixels if p > 0)
print(f"  Non-zero pixels: {nonzero}")

# Find bounding box of content
min_x, min_y, max_x, max_y = 128, 128, 0, 0
for y in range(128):
    for x in range(128):
        if pixels[y * 128 + x] > 0:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
print(f"  Content bounding box: ({min_x},{min_y}) to ({max_x},{max_y})")
print(f"  Content size: {max_x - min_x + 1} x {max_y - min_y + 1}")

# Try to identify glyph grid
# Look for regular gaps (zero columns/rows)
print("\n  Row occupancy (non-zero pixel count per row):")
for y in range(128):
    count = sum(1 for x in range(128) if pixels[y * 128 + x] > 0)
    if count > 0:
        print(f"    Row {y:3d}: {count:3d} pixels {'#' * min(count, 60)}")

# Also try with inverted palette (white = 0, black = max)
palette_inv = bytearray(64)
for i in range(16):
    v = 255 - i * 17
    palette_inv[i*4] = v; palette_inv[i*4+1] = v; palette_inv[i*4+2] = v; palette_inv[i*4+3] = 128

img_inv = make_rgba_image_4bit(pixels, palette_inv, 128, 128)
img_inv_zoom = img_inv.resize((512, 512), Image.NEAREST)
out4 = os.path.join(TEX_DIR, "EXE_embedded_font_inv_4x.png")
img_inv_zoom.save(out4)
print(f"\nSaved inverted 4x: {out4}")

# ---- Also check what's immediately BEFORE the font in the EXE ----
# Maybe there's a palette or header
pre_off = EXE_FONT_OFF - 256
pre_data = exe_data[pre_off:EXE_FONT_OFF]
print(f"\n256 bytes before font (at 0x{pre_off:X}):")
for i in range(0, 256, 16):
    hex_str = ' '.join(f'{b:02X}' for b in pre_data[i:i+16])
    print(f"  {pre_off+i:08X}: {hex_str}")

# Check for palette-like data (64 bytes = 16 RGBA colors)
# Look in the 256 bytes before the font
print("\nLooking for 64-byte RGBA palette before font data...")
for off in range(0, 256 - 64, 4):
    candidate = pre_data[off:off+64]
    # Check if it looks like a palette (some non-zero, structured)
    nz = sum(1 for b in candidate if b != 0)
    if 10 < nz < 60:
        print(f"  Candidate at 0x{pre_off+off:X}: {candidate[:32].hex()}")

# ---- Data immediately AFTER the font (before cell data) ----
post_off = EXE_FONT_OFF + 8192  # 0x3D8C10
post_data = exe_data[post_off:post_off + 256]
print(f"\n256 bytes after font (at 0x{post_off:X}):")
for i in range(0, 256, 16):
    hex_str = ' '.join(f'{b:02X}' for b in post_data[i:i+16])
    print(f"  {post_off+i:08X}: {hex_str}")

print("\n=== Done ===")
