#!/usr/bin/env python3
"""Brute-force dbw_ct32 1-100 for R1188 PSMT4 1024x1024 deswizzle. Save ALL PNGs."""
import sys
import os
import time

sys.path.insert(0, 'C:/Programmieren/wizardrytranslation/tools')
from psmt4_deswizzle import deswizzle_psmt4

from PIL import Image

RAW_PATH = 'C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1188_type01.raw'
OUT_DIR = 'C:/Programmieren/wizardrytranslation/build/r1188_dbw_sweep'
os.makedirs(OUT_DIR, exist_ok=True)

HEADER = 2048
TEX_W, TEX_H = 1024, 1024
PIXEL_BYTES = TEX_W * TEX_H // 2  # 524288

data = open(RAW_PATH, 'rb').read()
pixels_raw = data[HEADER:HEADER + PIXEL_BYTES]
print(f"File: {len(data)} bytes, pixel data: {len(pixels_raw)} bytes from offset {HEADER}")

# Read actual palette from file
palette_raw = data[-2048:]
palette_bytes = bytearray(palette_raw[:64])
pal_nonzero = any(b != 0 for b in palette_bytes)
if not pal_nonzero:
    print("Palette is all zeros - using grayscale ramp")
    palette_bytes = bytearray(64)
    for i in range(16):
        v = i * 17
        palette_bytes[i*4] = v
        palette_bytes[i*4+1] = v
        palette_bytes[i*4+2] = v
        palette_bytes[i*4+3] = 128

pal_colors = []
for i in range(16):
    r = palette_bytes[i * 4]
    g = palette_bytes[i * 4 + 1]
    b = palette_bytes[i * 4 + 2]
    a = min(palette_bytes[i * 4 + 3] * 2, 255)
    pal_colors.append((r, g, b, a))

results = []
t0 = time.time()

for dbw in range(1, 101):
    try:
        pixels_lin = deswizzle_psmt4(pixels_raw, TEX_W, TEX_H,
                                      bw_psmt4=TEX_W, dbw_ct32=dbw)
    except Exception as e:
        print(f"dbw={dbw:3d}: ERROR - {e}")
        results.append((dbw, -1, -1, -1))
        continue

    elapsed = time.time() - t0

    # Metrics
    nonzero = sum(1 for p in pixels_lin if p != 0)
    total = TEX_W * TEX_H
    pct_nz = 100.0 * nonzero / total

    # Uniform chunk metric: count 32-pixel row chunks with <=2 unique values
    uniform_chunks = 0
    total_chunks = 0
    for row in range(TEX_H):
        for cx in range(0, TEX_W, 32):
            chunk = pixels_lin[row * TEX_W + cx: row * TEX_W + cx + 32]
            total_chunks += 1
            if len(set(chunk)) <= 2:
                uniform_chunks += 1
    pct_uniform = 100.0 * uniform_chunks / total_chunks

    # Horizontal transitions
    transitions = 0
    for row in range(TEX_H):
        for x in range(TEX_W - 1):
            if pixels_lin[row * TEX_W + x] != pixels_lin[row * TEX_W + x + 1]:
                transitions += 1

    # Save PNG - EVERY value
    img = Image.new('RGBA', (TEX_W, TEX_H))
    img_data = [pal_colors[min(p, 15)] for p in pixels_lin[:TEX_W * TEX_H]]
    img.putdata(img_data)
    out_path = os.path.join(OUT_DIR, f"dbw_{dbw:03d}.png")
    img.save(out_path)

    print(f"dbw={dbw:3d}: nz={pct_nz:5.1f}% uniform={pct_uniform:5.1f}% trans={transitions:8d} [{elapsed:.1f}s]")
    sys.stdout.flush()
    results.append((dbw, pct_nz, pct_uniform, transitions))

# Rankings
ok = [(d, nz, uc, tr) for d, nz, uc, tr in results if nz >= 0]

print("\n" + "="*80)
print("TOP 15 by MOST uniform chunks (higher = more structured/clean):")
print("="*80)
for d, nz, uc, tr in sorted(ok, key=lambda x: -x[2])[:15]:
    print(f"  dbw={d:3d}: uniform={uc:5.1f}% nonzero={nz:5.1f}% transitions={tr:8d}")

print("\nTOP 15 by FEWEST transitions (lower = blockier/more structured):")
for d, nz, uc, tr in sorted(ok, key=lambda x: x[3])[:15]:
    print(f"  dbw={d:3d}: transitions={tr:8d} uniform={uc:5.1f}% nonzero={nz:5.1f}%")

print("\nTOP 15 by MOST non-zero pixels:")
for d, nz, uc, tr in sorted(ok, key=lambda x: -x[1])[:15]:
    print(f"  dbw={d:3d}: nonzero={nz:5.1f}% uniform={uc:5.1f}% transitions={tr:8d}")

total_time = time.time() - t0
print(f"\nAll 100 PNGs saved to {OUT_DIR}")
print(f"Total time: {total_time:.1f}s")
