#!/usr/bin/env python3
"""Verify the PSMT8 deswizzle LUT by computing forward and inverse mappings."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# From PCSX2 GSTables.cpp
blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

columnTable8 = [
    [  0,   4,  16,  20,  32,  36,  48,  52,   2,   6,  18,  22,  34,  38,  50,  54],
    [  8,  12,  24,  28,  40,  44,  56,  60,  10,  14,  26,  30,  42,  46,  58,  62],
    [ 33,  37,  49,  53,   1,   5,  17,  21,  35,  39,  51,  55,   3,   7,  19,  23],
    [ 41,  45,  57,  61,   9,  13,  25,  29,  43,  47,  59,  63,  11,  15,  27,  31],
    [ 96, 100, 112, 116,  64,  68,  80,  84,  98, 102, 114, 118,  66,  70,  82,  86],
    [104, 108, 120, 124,  72,  76,  88,  92, 106, 110, 122, 126,  74,  78,  90,  94],
    [ 65,  69,  81,  85,  97, 101, 113, 117,  67,  71,  83,  87,  99, 103, 115, 119],
    [ 73,  77,  89,  93, 105, 109, 121, 125,  75,  79,  91,  95, 107, 111, 123, 127],
    [128, 132, 144, 148, 160, 164, 176, 180, 130, 134, 146, 150, 162, 166, 178, 182],
    [136, 140, 152, 156, 168, 172, 184, 188, 138, 142, 154, 158, 170, 174, 186, 190],
    [161, 165, 177, 181, 129, 133, 145, 149, 163, 167, 179, 183, 131, 135, 147, 151],
    [169, 173, 185, 189, 137, 141, 153, 157, 171, 175, 187, 191, 139, 143, 155, 159],
    [224, 228, 240, 244, 192, 196, 208, 212, 226, 230, 242, 246, 194, 198, 210, 214],
    [232, 236, 248, 252, 200, 204, 216, 220, 234, 238, 250, 254, 202, 206, 218, 222],
    [193, 197, 209, 213, 225, 229, 241, 245, 195, 199, 211, 215, 227, 231, 243, 247],
    [201, 205, 217, 221, 233, 237, 249, 253, 203, 207, 219, 223, 235, 239, 251, 255],
]

# Forward: compute byte address from (x, y) within a page
def forward_pa(x, y):
    """Return byte offset in page for pixel at (x, y), where x=0..127, y=0..63."""
    bx = x // 16  # block column
    by = y // 16  # block row
    block = blockTable8[by][bx]

    lx = x % 16   # pixel x within block
    ly = y % 16   # pixel y within block
    col_offset = columnTable8[ly][lx]  # byte offset within block

    return block * 256 + col_offset

# Build inverse: byte_offset -> (x, y)
inv_lut = [None] * 8192
for y in range(64):
    for x in range(128):
        addr = forward_pa(x, y)
        if addr < 8192:
            if inv_lut[addr] is not None:
                print(f"COLLISION at addr {addr}: ({x},{y}) and {inv_lut[addr]}")
            inv_lut[addr] = (x, y)

# Check completeness
filled = sum(1 for e in inv_lut if e is not None)
print(f"Inverse LUT: {filled}/8192 entries filled")

# Check some known values
print(f"forward_pa(0, 0) = {forward_pa(0, 0)}")  # Should be 0
print(f"forward_pa(1, 0) = {forward_pa(1, 0)}")  # Should be 4
print(f"forward_pa(0, 1) = {forward_pa(0, 1)}")  # Should be 8

# Verify: reading byte 0 should give pixel (0,0)
print(f"inv_lut[0] = {inv_lut[0]}")  # Should be (0,0)
print(f"inv_lut[4] = {inv_lut[4]}")  # Should be (1,0)
print(f"inv_lut[8] = {inv_lut[8]}")  # Should be (0,1)

# Verify some more
for byte_off in [0, 1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 33, 64, 96, 128, 256]:
    if inv_lut[byte_off]:
        print(f"  byte[{byte_off:4d}] -> pixel {inv_lut[byte_off]}")

# Test: create a simple gradient image and deswizzle it
# If we write pixel value = x + y*128 to position (x,y),
# then reading linearly should give a specific pattern
from PIL import Image
import os

# Create swizzled data: for each byte position, store the pixel value
# that SHOULD appear there if the image is a simple gradient
swizzled = bytearray(8192)
for y in range(64):
    for x in range(128):
        addr = forward_pa(x, y)
        # Store a gradient value
        val = (x + y * 2) & 0xFF
        swizzled[addr] = val

# Now deswizzle using inverse LUT
deswizzled = bytearray(128 * 64)
for i in range(8192):
    if inv_lut[i] is not None:
        x, y = inv_lut[i]
        deswizzled[y * 128 + x] = swizzled[i]

# Save gradient test images
out_dir = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'
# Swizzled (raw linear read)
img_raw = Image.new('L', (128, 64))
img_raw.putdata(list(swizzled))
img_raw.save(f'{out_dir}/test_swizzled_raw.png')

# Deswizzled (should show clean gradient)
img_desw = Image.new('L', (128, 64))
img_desw.putdata(list(deswizzled))
img_desw.save(f'{out_dir}/test_deswizzled.png')

# Expected (original gradient)
expected = bytearray(128 * 64)
for y in range(64):
    for x in range(128):
        expected[y * 128 + x] = (x + y * 2) & 0xFF
img_exp = Image.new('L', (128, 64))
img_exp.putdata(list(expected))
img_exp.save(f'{out_dir}/test_expected.png')

# Compare
match = sum(1 for i in range(len(expected)) if deswizzled[i] == expected[i])
print(f"\nGradient test: {match}/{len(expected)} pixels match ({100*match/len(expected):.1f}%)")

if match == len(expected):
    print("PERFECT MATCH - deswizzle is correct!")
else:
    # Show first mismatches
    for i in range(len(expected)):
        if deswizzled[i] != expected[i]:
            y, x = divmod(i, 128)
            print(f"  Mismatch at ({x},{y}): got {deswizzled[i]}, expected {expected[i]}")
            if i > 20:
                break
