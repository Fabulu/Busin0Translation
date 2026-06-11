#!/usr/bin/env python3
"""
Preview R2138 sub4 — 512x256 PSMT4 dual-language atlas.
"""
import os, sys, struct

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

INPUT = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
OUTDIR = os.path.join(BASE, "build")

with open(INPUT, "rb") as f:
    r2138 = f.read()

# Sub4 descriptor from type-29 header:
# @0x040: sub_index=4, size=0x10900 (67840), file_offset=0x4B490
SUB4_OFFSET = 0x4B490
SUB4_SIZE = 0x10900

print(f"Sub4 at file offset 0x{SUB4_OFFSET:X}, size=0x{SUB4_SIZE:X} ({SUB4_SIZE})")

# Dump the sub-header (first 256 bytes)
sub4_data = r2138[SUB4_OFFSET:SUB4_OFFSET + SUB4_SIZE]
print(f"\n--- Sub4 header (first 256 bytes) ---")
for row in range(16):
    off = row * 16
    hexvals = " ".join(f"{sub4_data[off+i]:02X}" for i in range(16))
    ascii_repr = "".join(chr(sub4_data[off+i]) if 32 <= sub4_data[off+i] < 127 else "." for i in range(16))
    print(f"  0x{off:04X}: {hexvals}  {ascii_repr}")

# For other subs, pixel_off varies: sub0=0x500, sub6=0x800, sub7=0xC0, sub25=0x6E0, sub26=0x500, sub27=0x740
# And pixel_size = 32768 for 256x256 textures
# Sub4 is 512x256, so pixel_size = 512*256/2 = 65536 bytes
# Total sub4 size is 67840 = 0x10900
# 67840 - 65536 = 2304 = 0x900 header bytes

# Let's look for GIF metadata or TIM2-like headers
# Check what offset pixel data starts at
# 0x10900 - 0x10000 = 0x900 header
# But let's also check common PS2 texture header patterns

# Let's search for where pixel data likely starts by looking for the
# first non-zero block of significant data
pixel_off_candidates = [0x500, 0x800, 0x900, 0xC0, 0x100, 0x200, 0x400, 0x6E0, 0x740]
TEX_W, TEX_H = 512, 256
PIXEL_SIZE = TEX_W * TEX_H // 2  # 65536 for PSMT4

print(f"\nExpected pixel size: {PIXEL_SIZE} (0x{PIXEL_SIZE:X})")
print(f"Sub4 total size: {SUB4_SIZE} (0x{SUB4_SIZE:X})")
print(f"Header size must be: {SUB4_SIZE - PIXEL_SIZE} (0x{SUB4_SIZE - PIXEL_SIZE:X})")

# Header should be 0x900 = 2304 bytes
PIXEL_OFF = SUB4_SIZE - PIXEL_SIZE  # 0x900
print(f"Assuming pixel_off = 0x{PIXEL_OFF:X}")

# Try multiple dbw_ct32 values
for dbw in [128, 256, 512]:
    print(f"\n--- Trying dbw_ct32={dbw} ---")
    pixel_data = sub4_data[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE]

    try:
        linear = deswizzle_psmt4(
            pixel_data, TEX_W, TEX_H,
            bw_psmt4=TEX_W, dbw_ct32=dbw
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    # Check if we get reasonable data
    nonzero = sum(1 for v in linear if v != 0)
    total = len(linear)
    print(f"  Linear pixels: {total}, non-zero: {nonzero} ({100*nonzero//total}%)")

    # Save preview
    preview = Image.new("L", (TEX_W, TEX_H))
    for i, p in enumerate(linear[:TEX_W * TEX_H]):
        brightness = p * 255 // 15 if p <= 15 else 255
        preview.putpixel((i % TEX_W, i // TEX_W), brightness)

    out_path = os.path.join(OUTDIR, f"r2138_sub4_preview_dbw{dbw}.png")
    preview.save(out_path)
    print(f"  Saved: {out_path}")

# Also try with pixel_off = 0x500 (like sub0/sub26) in case header is smaller
# and there's a palette at the end
alt_pixel_off = 0x500
if alt_pixel_off + PIXEL_SIZE <= SUB4_SIZE:
    print(f"\n--- Trying pixel_off=0x{alt_pixel_off:X} ---")
    pixel_data = sub4_data[alt_pixel_off:alt_pixel_off + PIXEL_SIZE]
    for dbw in [256]:
        linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, bw_psmt4=TEX_W, dbw_ct32=dbw)
        preview = Image.new("L", (TEX_W, TEX_H))
        for i, p in enumerate(linear[:TEX_W * TEX_H]):
            brightness = p * 255 // 15
            preview.putpixel((i % TEX_W, i // TEX_W), brightness)
        out_path = os.path.join(OUTDIR, f"r2138_sub4_preview_off500_dbw{dbw}.png")
        preview.save(out_path)
        print(f"  Saved: {out_path}")

print("\nDone!")
