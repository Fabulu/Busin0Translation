#!/usr/bin/env python3
"""
Further analysis:
1. The palette data at 0x3D8C10 (between font and cell data)
2. Re-render font with proper PS2 palette
3. Analyze cell data structure
4. Check what the font is used for (debug overlay? name entry?)
"""
import os, sys, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4, make_rgba_image_4bit

try:
    from PIL import Image
except ImportError:
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
exe_data = open(EXE_PATH, 'rb').read()

# ---- The palette data between font bitmap and cell data ----
# 0x3D8C10 to 0x3D8D10 = 256 bytes
# Format: groups of 16 bytes (4 x 32-bit or 8 x 16-bit)
# Values like 0x7FFF are PS2 RGB555 white
PAL_OFF = 0x3D8C10
PAL_SIZE = 0x3D8D10 - 0x3D8C10  # 256 bytes

print("=== Palette Analysis at 0x3D8C10 ===\n")
pal_data = exe_data[PAL_OFF:PAL_OFF + PAL_SIZE]

# Parse as PS2 16-bit RGB555 colors (ABBBBBGGGGGRRRRR)
print("As PS2 16-bit RGBA5551 colors:")
for i in range(0, PAL_SIZE, 2):
    val = struct.unpack_from('<H', pal_data, i)[0]
    r = (val & 0x1F) << 3
    g = ((val >> 5) & 0x1F) << 3
    b = ((val >> 10) & 0x1F) << 3
    a = 255 if val & 0x8000 else 0
    if val != 0:
        print(f"  [{i//2:3d}] 0x{val:04X} -> R={r:3d} G={g:3d} B={b:3d} A={a:3d}")

# The data appears to be in groups of 16 bytes (8 colors per group)
# But with 00 00 padding between entries
# Let me parse as 32-bit entries where only lower 16 bits matter
print("\nAs 32-bit entries (lower 16 = PS2 color):")
colors_32 = []
for i in range(0, PAL_SIZE, 4):
    val = struct.unpack_from('<I', pal_data, i)[0]
    lo16 = val & 0xFFFF
    hi16 = (val >> 16) & 0xFFFF
    colors_32.append(lo16)
    if lo16 != 0:
        r = (lo16 & 0x1F) << 3
        g = ((lo16 >> 5) & 0x1F) << 3
        b = ((lo16 >> 10) & 0x1F) << 3
        print(f"  [{i//4:3d}] 0x{val:08X} -> color 0x{lo16:04X} R={r:3d} G={g:3d} B={b:3d}")

# These look like 16-color palettes in groups of 16 entries (64 bytes each)
# 256 bytes / 64 = 4 palettes
# But with 32-bit stride it's 256/4 = 64 entries, which is 4 palettes of 16 colors
# Actually: each color is 4 bytes (16-bit color + 16-bit padding = 00 00)
# So 256 bytes / 4 = 64 color entries
# These could be 4 palettes of 16 colors each

print("\n--- Interpreting as 4 palettes of 16 PS2 RGB555 colors ---")
for pal_idx in range(4):
    pal_start = pal_idx * 64  # 64 bytes = 16 colors * 4 bytes each
    print(f"\nPalette {pal_idx} (offset 0x{PAL_OFF + pal_start:X}):")
    rgba_pal = bytearray(64)
    for c in range(16):
        off = pal_start + c * 4
        if off + 2 <= PAL_SIZE:
            val = struct.unpack_from('<H', pal_data, off)[0]
            r = (val & 0x1F) << 3
            g = ((val >> 5) & 0x1F) << 3
            b = ((val >> 10) & 0x1F) << 3
            a = 128 if val != 0 else 0
            rgba_pal[c*4] = r
            rgba_pal[c*4+1] = g
            rgba_pal[c*4+2] = b
            rgba_pal[c*4+3] = a
            print(f"    [{c:2d}] 0x{val:04X} -> ({r:3d},{g:3d},{b:3d})")

    # Render font with this palette
    font_raw = exe_data[0x3D6C10:0x3D6C10 + 8192]
    pixels = deswizzle_psmt4(font_raw, 128, 128, bw_psmt4=128, dbw_ct32=64)
    img = make_rgba_image_4bit(pixels, rgba_pal, 128, 128)
    img_zoom = img.resize((512, 512), Image.NEAREST)
    out = os.path.join(TEX_DIR, f"EXE_embedded_font_pal{pal_idx}_4x.png")
    img_zoom.save(out)
    print(f"    Saved: {out}")


# ---- Cell data structure analysis ----
print("\n\n=== Cell Data Analysis (0x3D8D10, 8800 bytes) ===\n")
CELL_OFF = 0x3D8D10
CELL_SIZE = 8800
cell_data = exe_data[CELL_OFF:CELL_OFF + CELL_SIZE]

# 8800 bytes. Could be:
# - 550 records of 16 bytes
# - 275 records of 32 bytes
# - 1100 records of 8 bytes

# Let's check as 8-byte records (x, y, w, h or similar)
print("As 8-byte records (1100 entries):")
print("  First 30 entries as (u16, u16, u16, u16):")
for i in range(30):
    off = i * 8
    a, b, c, d = struct.unpack_from('<HHHH', cell_data, off)
    print(f"  [{i:4d}] {a:5d} {b:5d} {c:5d} {d:5d}  (0x{a:04X} 0x{b:04X} 0x{c:04X} 0x{d:04X})")

# Also try as 4-byte records (coords?)
print("\nAs 4-byte records (2200 entries), first 30:")
for i in range(30):
    off = i * 4
    a, b = struct.unpack_from('<HH', cell_data, off)
    print(f"  [{i:4d}] {a:5d} {b:5d}  (0x{a:04X} 0x{b:04X})")

# Check if values are consistently small (coordinates into 128x128 texture)
print("\nAs 16-bit values, statistics:")
vals16 = [struct.unpack_from('<H', cell_data, i)[0] for i in range(0, CELL_SIZE-1, 2)]
nonzero16 = [v for v in vals16 if v > 0]
if nonzero16:
    print(f"  Non-zero count: {len(nonzero16)} / {len(vals16)}")
    print(f"  Min non-zero: {min(nonzero16)}, Max: {max(nonzero16)}")
    # Distribution of ranges
    under_128 = sum(1 for v in nonzero16 if v < 128)
    under_256 = sum(1 for v in nonzero16 if v < 256)
    under_1024 = sum(1 for v in nonzero16 if v < 1024)
    print(f"  Values < 128: {under_128}, < 256: {under_256}, < 1024: {under_1024}")

# Check for recognizable glyph-coordinate patterns
# If these are UV coordinates into the 128x128 font,
# values should be 0-127 for x and 0-127 for y
print("\nAs (u8,u8,u8,u8,...) byte values, first 80:")
for i in range(0, 80, 16):
    chunk = cell_data[i:i+16]
    vals = ' '.join(f'{b:3d}' for b in chunk)
    print(f"  0x{CELL_OFF+i:X}: {vals}")

# Look for where the non-zero data ends
last_nonzero = 0
for i in range(CELL_SIZE - 1, -1, -1):
    if cell_data[i] != 0:
        last_nonzero = i
        break
print(f"\nLast non-zero byte at offset {last_nonzero} (0x{last_nonzero:X})")
print(f"Active data: {last_nonzero + 1} bytes out of {CELL_SIZE}")

# Also check what's after the cell data
print(f"\n64 bytes after cell data (0x{CELL_OFF + CELL_SIZE:X}):")
after = exe_data[CELL_OFF + CELL_SIZE:CELL_OFF + CELL_SIZE + 64]
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in after[i:i+16])
    print(f"  {hex_str}")

print("\n=== Done ===")
