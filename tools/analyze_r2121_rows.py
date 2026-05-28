#!/usr/bin/env python3
"""Analyze R2121 pixel data row by row to find interleaving patterns."""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

data = open('C:/Programmieren/wizardrytranslation/build/textures_to_edit/R2121_guild_background.raw', 'rb').read()
tex = data[16:]
raw = tex[272:]
width = 512

# Check if rows have consistent entropy
# If some rows are metadata (GIF tags), they'll look different
import collections

print("Row analysis (first 32 rows of 512 bytes each):")
for row in range(32):
    start = row * width
    row_data = raw[start:start + width]
    unique = len(set(row_data))
    # Check for repeating patterns
    avg = sum(row_data) / len(row_data)
    # Check if it looks like a GIF tag (low entropy, specific patterns)
    first8 = struct.unpack_from('<Q', row_data, 0)[0]
    nloop = first8 & 0x7FFF
    flg = (first8 >> 46) & 3
    print(f"  Row {row:3d}: unique={unique:3d}, avg={avg:.1f}, first8=0x{first8:016x}")

# Check stride: maybe the actual width is not 512?
# Try rendering with different widths
from PIL import Image
import os

OUT = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'
pixel_count = 512 * 512
pal_bytes = raw[pixel_count:pixel_count + 1024]

# Unswizzle palette
colors = []
for i in range(256):
    off = i * 4
    if off + 3 < len(pal_bytes):
        r, g, b, a = pal_bytes[off], pal_bytes[off+1], pal_bytes[off+2], pal_bytes[off+3]
        colors.append((r, g, b, min(a * 2, 255)))
    else:
        colors.append((0, 0, 0, 0))
# CLUT swap
for grp in range(8):
    base = grp * 32
    for j in range(8):
        colors[base + 8 + j], colors[base + 16 + j] = \
            colors[base + 16 + j], colors[base + 8 + j]

# Try different widths
for test_w in [256, 384, 448, 480, 504, 508, 512, 516, 520, 528, 640, 768, 1024]:
    test_h = min(pixel_count // test_w, 1024)
    if test_h < 64:
        continue
    img = Image.new('RGBA', (test_w, test_h))
    px = []
    for j in range(test_w * test_h):
        if j < len(raw):
            px.append(colors[raw[j]])
        else:
            px.append((0, 0, 0, 0))
    img.putdata(px)
    fname = f'{OUT}/R2121_w{test_w}.png'
    img.save(fname)
    print(f"Saved: {fname}")

# Also try with row swaps (even/odd interleave)
# Sometimes PS2 data is stored with interlaced fields
for swap_h in [2, 4, 8, 16]:
    w, h = 512, 512
    img = Image.new('RGBA', (w, h))
    px = []
    for y in range(h):
        # Determine source row
        block = y // swap_h
        sub = y % swap_h
        if block % 2 == 0:
            src_y = block * swap_h + sub
        else:
            # Try swapping blocks
            src_y = (block - 1) * swap_h + swap_h + sub

        for x in range(w):
            src_idx = src_y * w + x
            if src_idx < len(raw):
                px.append(colors[raw[src_idx]])
            else:
                px.append((0, 0, 0, 0))
    img.putdata(px)
    fname = f'{OUT}/R2121_swap{swap_h}.png'
    img.save(fname)
    print(f"Saved: {fname}")

# Try row interleave: first all even rows, then all odd rows
w, h = 512, 512
img = Image.new('RGBA', (w, h))
px_data = raw[:pixel_count]
px = []
for y in range(h):
    # Source: even rows first, then odd
    if y < h // 2:
        src_y = y * 2  # even row
    else:
        src_y = (y - h // 2) * 2 + 1  # odd row
    for x in range(w):
        src_idx = src_y * w + x
        if src_idx < len(px_data):
            px.append(colors[px_data[src_idx]])
        else:
            px.append((0, 0, 0, 0))
img.putdata(px)
img.save(f'{OUT}/R2121_deinterlace.png')
print(f"Saved: R2121_deinterlace.png")

# Inverse: odd rows first, then even
img2 = Image.new('RGBA', (w, h))
px2 = []
for y in range(h):
    if y < h // 2:
        src_y = y * 2 + 1
    else:
        src_y = (y - h // 2) * 2
    for x in range(w):
        src_idx = src_y * w + x
        if src_idx < len(px_data):
            px2.append(colors[px_data[src_idx]])
        else:
            px2.append((0, 0, 0, 0))
img2.putdata(px2)
img2.save(f'{OUT}/R2121_deinterlace_inv.png')
print(f"Saved: R2121_deinterlace_inv.png")
