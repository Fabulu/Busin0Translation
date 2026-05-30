#!/usr/bin/env python3
"""Brute-force dbw_ct32 sweep for R1188 PSMT4 1024x1024 deswizzle.

For each dbw_ct32 in [500..2048], deswizzle and score by counting
8x8 blocks where all pixels are identical (uniform/background blocks).

Uses vectorized numpy for the VRAM simulation to make the sweep feasible.
"""
import sys
import os
import time
import numpy as np

sys.path.insert(0, 'C:/Programmieren/wizardrytranslation/tools')
from psmt4_deswizzle import (BLOCK_TABLE_32, COLUMN_TABLE_32,
                               BLOCK_TABLE_4, COLUMN_TABLE_4,
                               make_rgba_image_4bit)

RAW_PATH = 'C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1188_type01.raw'
OUT_DIR = 'C:/Programmieren/wizardrytranslation/build/r1188_dbw_sweep'
TEX_W, TEX_H = 1024, 1024
HEADER = 2048
CLUT = 2048

# Precompute PSMT4 read-side address table (does NOT depend on dbw_ct32)
# This is constant for all iterations.
def build_psmt4_read_table(tex_w, tex_h, bw_psmt4):
    """Build array of nibble addresses for reading PSMT4 pixels from VRAM."""
    PAGE_W, PAGE_H = 128, 128
    BLOCK_W, BLOCK_H = 32, 16

    # Create coordinate arrays
    ys = np.arange(tex_h, dtype=np.int64)
    xs = np.arange(tex_w, dtype=np.int64)
    yy, xx = np.meshgrid(ys, xs, indexing='ij')

    ppr = max(1, bw_psmt4 // PAGE_W)
    pid = (yy // PAGE_H) * ppr + (xx // PAGE_W)

    # Block lookup
    by_idx = (yy % PAGE_H) // BLOCK_H
    bx_idx = (xx % PAGE_W) // BLOCK_W
    bt4 = np.array(BLOCK_TABLE_4, dtype=np.int64)
    bid = bt4[by_idx, bx_idx]

    # Column lookup
    cy_idx = yy % BLOCK_H
    cx_idx = xx % BLOCK_W
    ct4 = np.array(COLUMN_TABLE_4, dtype=np.int64)
    nib = ct4[cy_idx, cx_idx]

    nib_addr = pid * 16384 + bid * 512 + nib
    return nib_addr  # shape (tex_h, tex_w)


def build_psmct32_write_table(upload_w, upload_h):
    """Build PSMCT32 write address table for given upload dimensions.

    Returns array of VRAM word addresses, shape (upload_h, upload_w).
    """
    PAGE_W, PAGE_H = 64, 32

    ys = np.arange(upload_h, dtype=np.int64)
    xs = np.arange(upload_w, dtype=np.int64)
    yy, xx = np.meshgrid(ys, xs, indexing='ij')

    ppr = max(1, upload_w // PAGE_W)
    pid = (yy // PAGE_H) * ppr + (xx // PAGE_W)

    by_idx = (yy % PAGE_H) // 8
    bx_idx = (xx % PAGE_W) // 8
    bt32 = np.array(BLOCK_TABLE_32, dtype=np.int64)
    bid = bt32[by_idx, bx_idx]

    cy_idx = yy % 8
    cx_idx = xx % 8
    ct32 = np.array(COLUMN_TABLE_32, dtype=np.int64)
    wib = ct32[cy_idx, cx_idx]

    word_addr = pid * 2048 + bid * 64 + wib
    return word_addr


def deswizzle_fast(host_data_bytes, tex_w, tex_h, bw_psmt4, dbw_ct32, psmt4_nib_addr):
    """Fast vectorized PSMT4 deswizzle."""
    upload_w = dbw_ct32
    num_words = len(host_data_bytes) // 4
    upload_h = num_words // upload_w
    if upload_h <= 0:
        return None

    # Build PSMCT32 write table for this dbw
    ct32_word_addr = build_psmct32_write_table(upload_w, upload_h)

    # Determine VRAM size needed
    max_nib = int(psmt4_nib_addr.max())
    max_word = int(ct32_word_addr.max())
    vram_bytes_needed = max(max_nib // 2 + 1, (max_word + 1) * 4)
    vram = np.zeros(vram_bytes_needed, dtype=np.uint8)

    # Interpret host data as uint8 array
    host = np.frombuffer(host_data_bytes, dtype=np.uint8)

    # Write host data to VRAM using PSMCT32 swizzle
    # Each pixel is 4 bytes (one PSMCT32 word)
    flat_word_addr = ct32_word_addr.ravel()
    for byte_off in range(4):
        src_indices = np.arange(len(flat_word_addr)) * 4 + byte_off
        valid = src_indices < len(host)
        dst_indices = flat_word_addr[valid] * 4 + byte_off
        valid2 = dst_indices < len(vram)
        vram[dst_indices[valid2]] = host[src_indices[valid][valid2]]

    # Read PSMT4 pixels from VRAM
    flat_nib = psmt4_nib_addr.ravel()
    byte_addr = flat_nib // 2
    is_high = (flat_nib & 1).astype(bool)

    # Clamp byte addresses
    safe_addr = np.minimum(byte_addr, len(vram) - 1)
    byte_vals = vram[safe_addr]

    pixels = np.where(is_high, (byte_vals >> 4) & 0xF, byte_vals & 0xF).astype(np.uint8)
    return pixels.reshape(tex_h, tex_w)


def score_uniform_blocks(arr, block_size=8):
    """Count 8x8 blocks where all pixels are identical."""
    h, w = arr.shape
    # Reshape into blocks
    bh = h // block_size
    bw_count = w // block_size
    # Reshape: (bh, block_size, bw_count, block_size)
    blocks = arr[:bh*block_size, :bw_count*block_size].reshape(bh, block_size, bw_count, block_size)
    # Transpose to (bh, bw_count, block_size, block_size)
    blocks = blocks.transpose(0, 2, 1, 3)
    # Flatten each block
    blocks_flat = blocks.reshape(bh * bw_count, block_size * block_size)
    # Check uniformity: all elements equal to first
    uniform = np.all(blocks_flat == blocks_flat[:, :1], axis=1)
    return int(np.sum(uniform))


def main():
    data = open(RAW_PATH, 'rb').read()
    pixel_data = data[HEADER:HEADER + TEX_W * TEX_H // 2]
    palette_raw = data[-CLUT:]
    palette = bytearray(palette_raw[:64])

    if not any(b != 0 for b in palette):
        palette = bytearray(64)
        for i in range(16):
            v = i * 17
            palette[i*4] = v; palette[i*4+1] = v
            palette[i*4+2] = v; palette[i*4+3] = 128

    print(f"Pixel data: {len(pixel_data)} bytes")
    print(f"Sweeping dbw_ct32 from 500 to 2048 (1549 values)")
    print(f"Texture: {TEX_W}x{TEX_H} PSMT4")

    # Precompute PSMT4 read-side table (constant across all dbw values)
    print("Precomputing PSMT4 nibble address table...")
    t0 = time.time()
    psmt4_nib_addr = build_psmt4_read_table(TEX_W, TEX_H, TEX_W)
    print(f"  Done in {time.time()-t0:.1f}s")

    print("\nStarting sweep...")
    results = []
    t0 = time.time()

    for i, dbw in enumerate(range(500, 2049)):
        try:
            pixels = deswizzle_fast(pixel_data, TEX_W, TEX_H,
                                     bw_psmt4=TEX_W, dbw_ct32=dbw,
                                     psmt4_nib_addr=psmt4_nib_addr)
            if pixels is not None:
                score = score_uniform_blocks(pixels)
            else:
                score = -1
            results.append((dbw, score))
        except Exception as e:
            results.append((dbw, -1))

        if (i + 1) % 25 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            remaining = (1549 - i - 1) / rate
            best_so_far = max(results, key=lambda x: x[1])
            print(f"  [{i+1:4d}/1549] dbw={dbw:4d} score={results[-1][1]:5d}  "
                  f"({rate:.2f} it/s, ~{remaining:.0f}s left)  "
                  f"best so far: dbw={best_so_far[0]} score={best_so_far[1]}")

    elapsed = time.time() - t0
    print(f"\nSweep complete in {elapsed:.1f}s ({1549/elapsed:.2f} it/s)")

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'='*50}")
    print(f"TOP 10 dbw_ct32 values by uniform-block score:")
    print(f"{'='*50}")
    print(f"{'Rank':>4}  {'dbw_ct32':>10}  {'Score':>8}")
    print(f"{'-'*4}  {'-'*10}  {'-'*8}")
    for rank, (dbw, score) in enumerate(results[:10], 1):
        print(f"{rank:>4}  {dbw:>10}  {score:>8}")

    # Also show score for dbw=1024 specifically
    for dbw, score in results:
        if dbw == 1024:
            print(f"\n  (Reference: dbw=1024 score={score})")
            break

    # Save top 10 as PNGs
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"\nSaving top 10 as PNGs to {OUT_DIR}...")
    for rank, (dbw, score) in enumerate(results[:10], 1):
        pixels = deswizzle_fast(pixel_data, TEX_W, TEX_H,
                                 bw_psmt4=TEX_W, dbw_ct32=dbw,
                                 psmt4_nib_addr=psmt4_nib_addr)
        from PIL import Image
        img = make_rgba_image_4bit(pixels.ravel(), palette, TEX_W, TEX_H)
        out_path = os.path.join(OUT_DIR, f"rank{rank:02d}_dbw{dbw}_score{score}.png")
        img.save(out_path)
        print(f"  Saved: {out_path}")

    print("\nDone!")

if __name__ == "__main__":
    main()
