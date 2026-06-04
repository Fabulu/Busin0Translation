#!/usr/bin/env python3
"""
Analyze the EXE embedded font bitmap at offset 0x3D6C10 and R1188 auxiliary data.
"""
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import (
    deswizzle_psmt4, _psmt4_nibble_addr, _psmct32_word_addr,
    BLOCK_TABLE_4, COLUMN_TABLE_4, BLOCK_TABLE_32, COLUMN_TABLE_32
)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")
os.makedirs(TEX_DIR, exist_ok=True)

EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
R1188_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")

print("=== EXE Embedded Font Analysis ===\n")

# ---- Part 1: Read the 128x128 PSMT4 bitmap at EXE offset 0x3D6C10 ----
print("--- Part 1: EXE bitmap at 0x3D6C10 (8192 bytes, 128x128 PSMT4) ---")
exe_data = open(EXE_PATH, 'rb').read()
EXE_FONT_OFF = 0x3D6C10
EXE_FONT_SIZE = 8192  # 128*128/2

font_raw = exe_data[EXE_FONT_OFF:EXE_FONT_OFF + EXE_FONT_SIZE]
print(f"Read {len(font_raw)} bytes from EXE at 0x{EXE_FONT_OFF:X}")

# Check if data is all zeros
nonzero = sum(1 for b in font_raw if b != 0)
print(f"Non-zero bytes: {nonzero} / {len(font_raw)}")

# Try multiple interpretations:

# 1a) Deswizzle as PSMT4 128x128 (bw=128, dbw=128)
print("\n  1a) PSMT4 deswizzle (bw=128, dbw=128)...")
pixels_desw = deswizzle_psmt4(font_raw, 128, 128, bw_psmt4=128, dbw_ct32=128)

# Use grayscale palette
palette = bytearray(64)
for i in range(16):
    v = i * 17
    palette[i*4] = v; palette[i*4+1] = v; palette[i*4+2] = v; palette[i*4+3] = 128

from psmt4_deswizzle import make_rgba_image_4bit
img = make_rgba_image_4bit(pixels_desw, palette, 128, 128)
out1a = os.path.join(TEX_DIR, "EXE_embedded_font_deswizzle_128.png")
img.save(out1a)
print(f"  Saved: {out1a}")

# 1b) Linear reading (no deswizzle) - just interpret nibbles left to right
print("\n  1b) Linear nibble reading (no deswizzle)...")
pixels_lin = bytearray(128 * 128)
for i in range(len(font_raw)):
    lo = font_raw[i] & 0xF
    hi = (font_raw[i] >> 4) & 0xF
    pixels_lin[i * 2] = lo
    pixels_lin[i * 2 + 1] = hi
img_lin = make_rgba_image_4bit(pixels_lin, palette, 128, 128)
out1b = os.path.join(TEX_DIR, "EXE_embedded_font_linear.png")
img_lin.save(out1b)
print(f"  Saved: {out1b}")

# 1c) Linear but with swapped nibble order (hi first)
print("\n  1c) Linear nibble reading (hi-lo order)...")
pixels_lin2 = bytearray(128 * 128)
for i in range(len(font_raw)):
    hi = (font_raw[i] >> 4) & 0xF
    lo = font_raw[i] & 0xF
    pixels_lin2[i * 2] = hi
    pixels_lin2[i * 2 + 1] = lo
img_lin2 = make_rgba_image_4bit(pixels_lin2, palette, 128, 128)
out1c = os.path.join(TEX_DIR, "EXE_embedded_font_linear_hilo.png")
img_lin2.save(out1c)
print(f"  Saved: {out1c}")

# 1d) Try different widths for linear reading
for width in [64, 256, 32]:
    height = (128 * 128) // width
    pixels_w = bytearray(width * height)
    for i in range(len(font_raw)):
        lo = font_raw[i] & 0xF
        hi = (font_raw[i] >> 4) & 0xF
        pixels_w[i * 2] = lo
        pixels_w[i * 2 + 1] = hi
    img_w = make_rgba_image_4bit(pixels_w, palette, width, height)
    out_w = os.path.join(TEX_DIR, f"EXE_embedded_font_linear_{width}x{height}.png")
    img_w.save(out_w)
    print(f"  1d) Saved {width}x{height}: {out_w}")

# 1e) As 1-bit per pixel bitmap (8192 bytes = 65536 bits = 256x256)
print("\n  1e) As 1bpp bitmap (256x256)...")
img_1bpp = Image.new('L', (256, 256))
bits = []
for b in font_raw:
    for bit in range(8):
        bits.append(255 if (b >> (7 - bit)) & 1 else 0)
img_1bpp.putdata(bits[:256*256])
out1e = os.path.join(TEX_DIR, "EXE_embedded_font_1bpp_256x256.png")
img_1bpp.save(out1e)
print(f"  Saved: {out1e}")

# 1f) As 1bpp at 128x512
print("\n  1f) As 1bpp bitmap (128x512)...")
img_1bpp2 = Image.new('L', (128, 512))
img_1bpp2.putdata(bits[:128*512])
out1f = os.path.join(TEX_DIR, "EXE_embedded_font_1bpp_128x512.png")
img_1bpp2.save(out1f)
print(f"  Saved: {out1f}")

# 1g) Deswizzle with different dbw values
for dbw in [64, 32, 256]:
    try:
        pixels_d = deswizzle_psmt4(font_raw, 128, 128, bw_psmt4=128, dbw_ct32=dbw)
        img_d = make_rgba_image_4bit(pixels_d, palette, 128, 128)
        out_d = os.path.join(TEX_DIR, f"EXE_embedded_font_deswizzle_dbw{dbw}.png")
        img_d.save(out_d)
        print(f"  1g) Saved deswizzle dbw={dbw}: {out_d}")
    except Exception as e:
        print(f"  1g) dbw={dbw} failed: {e}")


# ---- Part 2: R1188 auxiliary data at header offset 0x840-0xBFF ----
print("\n\n--- Part 2: R1188 auxiliary data at offset 0x840-0xBFF (960 bytes) ---")
r1188_data = open(R1188_PATH, 'rb').read()
aux_data = r1188_data[0x840:0xC00]
print(f"Read {len(aux_data)} bytes from R1188 at 0x840")

# Show first and last 64 bytes as hex
print(f"  First 64 bytes: {aux_data[:64].hex()}")
print(f"  Last 64 bytes:  {aux_data[-64:].hex()}")

# Check if it's all zeros
nonzero_aux = sum(1 for b in aux_data if b != 0)
print(f"  Non-zero bytes: {nonzero_aux} / {len(aux_data)}")

# 2a) As 128x60 1bpp bitmap
print("\n  2a) As 1bpp bitmap (128x60 = 7680 bits = 960 bytes)...")
img_aux_1bpp = Image.new('L', (128, 60))
aux_bits = []
for b in aux_data:
    for bit in range(8):
        aux_bits.append(255 if (b >> (7 - bit)) & 1 else 0)
img_aux_1bpp.putdata(aux_bits[:128*60])
out2a = os.path.join(TEX_DIR, "R1188_aux_1bpp_128x60.png")
img_aux_1bpp.save(out2a)
print(f"  Saved: {out2a}")

# 2b) As 4bpp nibbles (960 bytes = 1920 nibbles)
# Try as 48x40 or 40x48 (1920 = 48*40)
for w, h in [(48, 40), (40, 48), (60, 32), (32, 60), (64, 30), (30, 64), (80, 24), (24, 80), (96, 20), (20, 96), (120, 16), (16, 120), (128, 15)]:
    if w * h <= 1920:
        nibs = bytearray(w * h)
        for i in range(min(len(aux_data), w * h // 2)):
            nibs[i * 2] = aux_data[i] & 0xF
            nibs[i * 2 + 1] = (aux_data[i] >> 4) & 0xF
        img_4 = make_rgba_image_4bit(nibs, palette, w, h)
        out_4 = os.path.join(TEX_DIR, f"R1188_aux_4bpp_{w}x{h}.png")
        img_4.save(out_4)
        print(f"  2b) Saved 4bpp {w}x{h}: {out_4}")

# 2c) As 8bpp byte values (960 bytes, try different widths)
for w in [16, 32, 48, 64, 96, 120]:
    h = 960 // w
    if w * h <= 960:
        img_8 = Image.new('L', (w, h))
        img_8.putdata(list(aux_data[:w*h]))
        out_8 = os.path.join(TEX_DIR, f"R1188_aux_8bpp_{w}x{h}.png")
        img_8.save(out_8)
        print(f"  2c) Saved 8bpp {w}x{h}: {out_8}")

# 2d) Interpret as structured data - look for patterns
print("\n  2d) Pattern analysis of auxiliary data...")
# Check if it's a table of small values
vals = list(aux_data)
print(f"    Min value: {min(vals)}, Max value: {max(vals)}")
print(f"    Unique values: {len(set(vals))}")
# Value histogram (top 10)
from collections import Counter
hist = Counter(vals)
print(f"    Top 10 values: {hist.most_common(10)}")

# Check for 16-bit or 32-bit structure
words16 = [struct.unpack_from('<H', aux_data, i)[0] for i in range(0, len(aux_data)-1, 2)]
words32 = [struct.unpack_from('<I', aux_data, i)[0] for i in range(0, len(aux_data)-3, 4)]
print(f"    As 16-bit words ({len(words16)} entries): min={min(words16)}, max={max(words16)}")
print(f"    First 20 16-bit values: {words16[:20]}")


# ---- Part 3: Cell data at EXE 0x3D8D10-0x3DAF70 ----
print("\n\n--- Part 3: Cell data arrays at EXE 0x3D8D10-0x3DAF70 (8800 bytes) ---")
CELL_OFF = 0x3D8D10
CELL_SIZE = 0x3DAF70 - 0x3D8D10  # = 8800
cell_data = exe_data[CELL_OFF:CELL_OFF + CELL_SIZE]
print(f"Read {len(cell_data)} bytes from EXE at 0x{CELL_OFF:X}")

nonzero_cell = sum(1 for b in cell_data if b != 0)
print(f"Non-zero bytes: {nonzero_cell} / {len(cell_data)}")

# Try as 1bpp at various widths
for w in [128, 64, 256]:
    total_bits = len(cell_data) * 8
    h = total_bits // w
    if h > 0:
        img_cell = Image.new('L', (w, h))
        cell_bits = []
        for b in cell_data:
            for bit in range(8):
                cell_bits.append(255 if (b >> (7 - bit)) & 1 else 0)
        img_cell.putdata(cell_bits[:w*h])
        out_cell = os.path.join(TEX_DIR, f"EXE_celldata_1bpp_{w}x{h}.png")
        img_cell.save(out_cell)
        print(f"  Saved 1bpp {w}x{h}: {out_cell}")

# Also try as 4bpp
for w in [128, 64, 32]:
    total_nibs = len(cell_data) * 2
    h = total_nibs // w
    if h > 0 and h < 10000:
        nibs = bytearray(w * h)
        for i in range(len(cell_data)):
            nibs[i * 2] = cell_data[i] & 0xF
            nibs[i * 2 + 1] = (cell_data[i] >> 4) & 0xF
        img_c4 = make_rgba_image_4bit(nibs[:w*h], palette, w, h)
        out_c4 = os.path.join(TEX_DIR, f"EXE_celldata_4bpp_{w}x{h}.png")
        img_c4.save(out_c4)
        print(f"  Saved 4bpp {w}x{h}: {out_c4}")

# Show first 128 bytes as hex
print(f"\n  First 128 bytes: {cell_data[:128].hex()}")

# Check as structured records - 8800 bytes could be many things
# 8800 = 8 * 1100, = 16 * 550, = 2 * 4400
# Check for record patterns
print(f"\n  First 64 as 16-bit words: {[struct.unpack_from('<H', cell_data, i)[0] for i in range(0, 128, 2)]}")
print(f"  First 16 as 32-bit words: {[struct.unpack_from('<I', cell_data, i)[0] for i in range(0, 64, 4)]}")


# ---- Part 4: Check for existing zero-write test ISOs ----
print("\n\n--- Part 4: Check for previous zero-write test ISOs ---")
import glob
isos = glob.glob(os.path.join(BASE, "build", "BUSIN0_EN_*.iso"))
for iso in sorted(isos):
    size = os.path.getsize(iso)
    mtime = os.path.getmtime(iso)
    import datetime
    dt = datetime.datetime.fromtimestamp(mtime)
    print(f"  {os.path.basename(iso)}: {size:,} bytes, modified {dt}")

# Also check if there's a specific test ISO mentioned in logs
test_isos = glob.glob(os.path.join(BASE, "build", "*test*.iso")) + glob.glob(os.path.join(BASE, "build", "*wipe*.iso"))
for iso in test_isos:
    print(f"  Test ISO: {os.path.basename(iso)}")


# ---- Part 5: Also look at the data between the font bitmap and cell data ----
print("\n\n--- Part 5: Data between bitmap and cell data (0x3D8C10-0x3D8D10) ---")
gap_off = EXE_FONT_OFF + EXE_FONT_SIZE  # 0x3D6C10 + 0x2000 = 0x3D8C10
gap_end = CELL_OFF  # 0x3D8D10
gap_size = gap_end - gap_off
gap_data = exe_data[gap_off:gap_end]
print(f"Gap: 0x{gap_off:X} to 0x{gap_end:X} = {gap_size} bytes")
print(f"Hex: {gap_data[:min(256, gap_size)].hex()}")
nonzero_gap = sum(1 for b in gap_data if b != 0)
print(f"Non-zero bytes: {nonzero_gap} / {gap_size}")

print("\n=== Done ===")
